"""Shared measurement primitives for the AC-035 benchmark suite.

Deliberately dependency-free (stdlib only) so the benchmark reproduces in the
same clean-room environment the runtime itself targets. Nothing here imports
from the benchmark bodies, so timing code stays separable from the specimens
being timed.
"""

from __future__ import annotations

import copy
import json
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "fixtures"


# --------------------------------------------------------------------------
# fixture loading
# --------------------------------------------------------------------------

def load_fixture(relative: str) -> Any:
    """Load a fixture as parsed JSON. Path is relative to fixtures/."""
    with (FIXTURES / relative).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_fixture_text(relative: str) -> str:
    return (FIXTURES / relative).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# environment capture (Phase 1)
# --------------------------------------------------------------------------

def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNAVAILABLE"


def _installed_versions() -> dict[str, str]:
    """Report versions of the packages actually imported by the runtime path."""
    versions: dict[str, str] = {}
    for name in ("rfc8785", "pytest"):
        try:
            module = __import__(name)
            versions[name] = getattr(module, "__version__", "UNKNOWN")
        except ImportError:
            versions[name] = "NOT INSTALLED"
    return versions


def capture_environment() -> dict[str, Any]:
    return {
        "commit_sha": _git("rev-parse", "HEAD"),
        "tree_sha": _git("rev-parse", "HEAD^{tree}"),
        "git_status_clean": _git("status", "--porcelain") == "",
        "python_version": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or "UNKNOWN",
        "dependency_versions": _installed_versions(),
    }


# --------------------------------------------------------------------------
# latency measurement (Phase 3)
# --------------------------------------------------------------------------

def _percentile(sorted_values: list[float], fraction: float) -> float:
    """Nearest-rank percentile. Deterministic and dependency-free; for the
    sample sizes used here the difference from an interpolating definition is
    far below the measurement noise floor."""
    if not sorted_values:
        raise ValueError("percentile of empty sample")
    rank = max(1, min(len(sorted_values), int(round(fraction * len(sorted_values) + 0.5))))
    return sorted_values[rank - 1]


def summarize(samples_seconds: list[float]) -> dict[str, Any]:
    """Distribution summary in microseconds."""
    micros = sorted(value * 1e6 for value in samples_seconds)
    return {
        "n": len(micros),
        "unit": "microseconds",
        "min": round(micros[0], 3),
        "p50": round(_percentile(micros, 0.50), 3),
        "p95": round(_percentile(micros, 0.95), 3),
        "p99": round(_percentile(micros, 0.99), 3),
        "max": round(micros[-1], 3),
        "mean": round(statistics.fmean(micros), 3),
        "stdev": round(statistics.stdev(micros), 3) if len(micros) > 1 else 0.0,
    }


def measure(
    operation: Callable[[], Any],
    *,
    repetitions: int,
    warmup: int = 50,
    inner_batch: int = 1,
) -> dict[str, Any]:
    """Time `operation` and return a distribution summary.

    `inner_batch` amortizes clock granularity for very fast operations: each
    recorded sample is the mean of `inner_batch` back-to-back executions, so a
    sub-microsecond operation is still measured above the timer's resolution
    rather than being reported as a quantized 0. Warmup executions are
    discarded so the reported figures are steady-state (warm) numbers.
    """
    for _ in range(warmup):
        operation()

    samples: list[float] = []
    for _ in range(repetitions):
        start = time.perf_counter()
        for _ in range(inner_batch):
            operation()
        elapsed = time.perf_counter() - start
        samples.append(elapsed / inner_batch)

    result = summarize(samples)
    result["warmup_discarded"] = warmup
    result["inner_batch"] = inner_batch
    return result


def measure_cold(operation: Callable[[], Any]) -> dict[str, Any]:
    """Single un-warmed execution, for comparison against the warm figure."""
    start = time.perf_counter()
    operation()
    return {"unit": "microseconds", "single_cold_execution": round((time.perf_counter() - start) * 1e6, 3)}


def latency_derived_rate(summary: dict[str, Any]) -> float:
    """Reciprocal of mean latency. This is an ARITHMETIC DERIVATION, not an
    observed throughput measurement — it assumes zero per-iteration overhead
    and no drift over time. Report it only alongside `sustained_throughput`,
    never as a substitute for it."""
    mean_seconds = summary["mean"] / 1e6
    if mean_seconds <= 0:
        return float("inf")
    return round(1.0 / mean_seconds, 1)


def sustained_throughput(
    operation: Callable[[], Any],
    *,
    duration_seconds: float = 5.0,
    warmup_seconds: float = 1.0,
    trials: int = 3,
) -> dict[str, Any]:
    """Observed sustained rate: run `operation` continuously for a fixed wall-clock
    window and count completed operations.

    This is a genuine throughput measurement rather than a reciprocal of mean
    latency: it includes loop overhead, allocator behaviour, and any drift that
    appears only under continuous operation, none of which a latency reciprocal
    captures. Single process, single thread, no concurrency.
    """
    trial_results: list[dict[str, Any]] = []

    for trial_index in range(trials):
        warmup_deadline = time.perf_counter() + warmup_seconds
        while time.perf_counter() < warmup_deadline:
            operation()

        operations = 0
        start = time.perf_counter()
        deadline = start + duration_seconds
        while time.perf_counter() < deadline:
            operation()
            operations += 1
        elapsed = time.perf_counter() - start

        trial_results.append(
            {
                "trial": trial_index + 1,
                "operations": operations,
                "elapsed_seconds": round(elapsed, 4),
                "operations_per_second": round(operations / elapsed, 1),
            }
        )

    rates = sorted(trial["operations_per_second"] for trial in trial_results)
    return {
        "method": "observed sustained rate — continuous single-threaded loop over a fixed window",
        "warmup_seconds": warmup_seconds,
        "measurement_seconds_per_trial": duration_seconds,
        "trials": trials,
        "trial_detail": trial_results,
        "total_operations": sum(trial["operations"] for trial in trial_results),
        "min_ops_per_second": rates[0],
        "median_ops_per_second": statistics.median(rates),
        "max_ops_per_second": rates[-1],
    }


# --------------------------------------------------------------------------
# device-under-test provenance (AC-035A)
# --------------------------------------------------------------------------

# Paths that constitute the device under test. The benchmark measures these and
# must not modify them; the harness itself lives outside this set.
def capture_dependency_identity() -> dict[str, Any]:
    """Record the exact third-party distributions present while measuring.

    Performance and correctness are properties of the code *plus* the
    dependencies it runs against. Recording the declared constraints alongside
    the versions actually installed makes the pair checkable: if they disagree,
    the run was not measuring the controlled set it claims to measure.
    """
    constraints_path = REPO_ROOT / "constraints.txt"
    declared: dict[str, str] = {}
    if constraints_path.exists():
        for line in constraints_path.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line and "==" in line:
                name, version = line.split("==", 1)
                declared[name.strip().lower().replace("_", "-")] = version.strip()

    installed: dict[str, str] = {}
    try:
        from importlib import metadata

        for dist in metadata.distributions():
            name = (dist.metadata["Name"] or "").lower().replace("_", "-")
            if name:
                installed[name] = dist.version
    except Exception as exc:  # pragma: no cover - defensive
        return {"declared": declared, "error": f"could not enumerate installed set: {exc}"}

    relevant = {name: installed.get(name) for name in sorted(declared)}
    mismatched = {
        name: {"declared": declared[name], "installed": relevant[name]}
        for name in declared
        if relevant[name] is not None and relevant[name] != declared[name]
    }
    absent = sorted(name for name in declared if relevant[name] is None)
    return {
        "constraints_file": "constraints.txt",
        "declared": declared,
        "installed_for_declared": relevant,
        "mismatched": mismatched,
        "declared_but_not_installed": absent,
        "matches_declared_set": not mismatched,
        "note": (
            "declared_but_not_installed is expected for distributions pinned only "
            "for older Python versions (pytest pulls exceptiongroup and tomli on "
            "Python < 3.11 only). A non-empty 'mismatched' means this run did not "
            "measure the controlled dependency set."
        ),
    }


DUT_PATHS = (
    "authcontract",
    "tests",
    "fixtures",
    ".github",
    "pyproject.toml",
    "README.md",
    "docs/SOTA.md",
    "docs/SOTA-EVIDENCE.md",
    "docs/DEVELOPER-LANGUAGE.md",
    "docs/CLEANROOM-VALIDATION-RUNBOOK.md",
)


def verify_dut_unchanged(dut_base_sha: str) -> dict[str, Any]:
    """Prove the measured product files are byte-identical to `dut_base_sha`.

    The harness is introduced by a later commit than the implementation it
    measures, so "which commit was measured" cannot be answered by HEAD alone.
    This diffs only the DUT paths between HEAD and the declared base: an empty
    diff establishes that the harness commit changed nothing under measurement.
    """
    try:
        # Deliberately diff against the WORKING TREE, not against HEAD: the
        # benchmark imports and measures the files on disk, so a comparison
        # between two commits would report "verified" while an uncommitted edit
        # silently changed what was actually measured. Omitting the second
        # revision makes git compare dut_base_sha to the working tree, catching
        # committed and uncommitted drift alike.
        completed = subprocess.run(
            ["git", "diff", "--name-only", dut_base_sha, "--", *DUT_PATHS],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        return {
            "verified": False,
            "error": f"could not diff against {dut_base_sha}: {exc}",
            "dut_paths": list(DUT_PATHS),
        }

    modified = [line for line in completed.stdout.splitlines() if line.strip()]
    return {
        "verified": not modified,
        "dut_base_sha": dut_base_sha,
        "dut_paths": list(DUT_PATHS),
        "modified_dut_files": modified,
        "statement": (
            f"All device-under-test paths are byte-identical to {dut_base_sha}; the "
            "benchmark harness changed nothing under measurement."
            if not modified
            else f"DUT DRIFT: {len(modified)} file(s) differ from {dut_base_sha}. "
            "Results do NOT describe that commit."
        ),
    }


# --------------------------------------------------------------------------
# memory measurement (Phase 9)
# --------------------------------------------------------------------------

def measure_peak_memory(operation: Callable[[], Any]) -> dict[str, Any]:
    """Peak Python heap attributable to one execution, via tracemalloc.

    This measures interpreter-level allocation, not RSS: it excludes the
    interpreter's own baseline and any allocator caching, which is what makes
    it comparable across runs.
    """
    tracemalloc.start()
    tracemalloc.reset_peak()
    operation()
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"peak_traced_bytes": peak, "peak_traced_kib": round(peak / 1024, 2)}


# --------------------------------------------------------------------------
# synthetic scale specimens (Phase 5)
# --------------------------------------------------------------------------

def _reseal(artifact: dict[str, Any]) -> dict[str, Any]:
    """Recompute the contract digest and re-bind every sibling that carries it.

    Generated specimens must be genuinely valid, not merely well-shaped: if the
    digest were left stale the specimen would refuse at the digest gate and the
    scale curve would measure the refusal path instead of the authorization
    path.
    """
    from authcontract.digest import contract_digest

    digest = contract_digest(artifact["contract"])
    for sibling in ("activation", "admission", "proof"):
        if isinstance(artifact.get(sibling), dict) and "contract_digest" in artifact[sibling]:
            artifact[sibling]["contract_digest"] = digest
    return artifact


def make_action_scaled_specimen(action_count: int) -> dict[str, Any]:
    """Banking specimen widened to `action_count` declared mediated actions.

    Scales the projection domain (the 'rules' dimension) while leaving the
    exercised action, the required facts, and the decision semantics identical,
    so any latency change is attributable to domain size alone.
    """
    artifact = copy.deepcopy(load_fixture("banking_payment_specimen.json"))
    actions = artifact["contract"]["projection_domain"]["actions"]
    template = copy.deepcopy(actions["send_payment"])
    mediated = artifact["contract"]["subject"]["mediated_actions"]
    for index in range(action_count - 1):
        name = f"synthetic_action_{index:05d}"
        actions[name] = copy.deepcopy(template)
        mediated.append(name)
    return _reseal(artifact)


def make_fact_scaled_specimen(fact_count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Banking specimen and matching bundle widened to `fact_count` facts.

    Both sides are widened together: a contract requiring N facts is only
    satisfiable by a bundle supplying all N, so this scales the admissibility
    workload rather than manufacturing a refusal.
    """
    artifact = copy.deepcopy(load_fixture("banking_payment_specimen.json"))
    bundle = copy.deepcopy(load_fixture("runtime/facts_valid.json"))

    required_template = copy.deepcopy(artifact["contract"]["required_facts"][0])
    fact_template = copy.deepcopy(bundle["facts"][0])

    for index in range(fact_count - 1):
        fact_id = f"synthetic.fact_{index:05d}"

        requirement = copy.deepcopy(required_template)
        requirement["fact_id"] = fact_id
        artifact["contract"]["required_facts"].append(requirement)

        fact = copy.deepcopy(fact_template)
        fact["fact_id"] = fact_id
        fact["evidence"] = copy.deepcopy(fact_template["evidence"])
        fact["evidence"]["fact_id"] = fact_id
        bundle["facts"].append(fact)

    return _reseal(artifact), bundle


# --------------------------------------------------------------------------
# result serialization
# --------------------------------------------------------------------------

def write_result(filename: str, payload: dict[str, Any]) -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path
