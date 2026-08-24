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


def throughput_per_second(summary: dict[str, Any]) -> float:
    """Derive sustained single-process rate from a mean latency in microseconds."""
    mean_seconds = summary["mean"] / 1e6
    if mean_seconds <= 0:
        return float("inf")
    return round(1.0 / mean_seconds, 1)


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
