#!/usr/bin/env python3
"""AC-035 — end-to-end operational and performance baseline for AuthContract.

Exercises only capabilities that exist at the measured commit. No runtime code
is imported-and-patched, monkeypatched, or reimplemented here: every number
comes from calling the same public entry points a developer would call.

Reproduce with:

    python3 -m pip install -e ".[test]"
    python3 benchmarks/run_benchmarks.py

Results are written to benchmarks/results/ as JSON.
"""

from __future__ import annotations

import copy
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (  # noqa: E402
    REPO_ROOT,
    capture_environment,
    load_fixture,
    load_fixture_text,
    make_action_scaled_specimen,
    make_fact_scaled_specimen,
    measure,
    measure_cold,
    measure_peak_memory,
    throughput_per_second,
    write_result,
)
from specimens import ADVERSARIAL_SPECIMENS, E2E_SPECIMENS  # noqa: E402

from authcontract.digest import canonical_bytes, contract_digest, verify_artifact  # noqa: E402
from authcontract.projection import check_action, project, projection_digest, projection_to_dict  # noqa: E402
from authcontract.veip import run_specimen, verify_receipt  # noqa: E402

EXECUTION_RESULT = "SIMULATED_SUCCESS"

# Repetition counts. Chosen so each stage's sample is large enough for a stable
# p99 without making the suite take longer than a developer will tolerate.
STAGE_REPS = 2000
STAGE_INNER_BATCH = 20
E2E_REPS = 1000
DETERMINISM_REPS = 100


def _run(artifact: dict, action: dict, facts: dict):
    return run_specimen(artifact, action, facts, execution_result=EXECUTION_RESULT)


def _load_triple(spec) -> tuple[dict, dict, dict]:
    return (
        load_fixture(spec.artifact_fixture),
        load_fixture(spec.action_fixture),
        load_fixture(spec.facts_fixture),
    )


# --------------------------------------------------------------------------
# Phase 2 + Phase 6 — end-to-end specimens and correctness matrix
# --------------------------------------------------------------------------

def _classify(result) -> str:
    return "ALLOW" if result.decision == "ALLOW" else "REFUSE"


def _evaluate_specimen(spec) -> dict[str, Any]:
    """Run one declarative specimen and record what actually happened."""
    artifact, action, facts = _load_triple(spec)

    failure_stage = None
    receipt_generated = False
    receipt_verified = None
    notes = ""

    try:
        result = _run(artifact, action, facts)
        observed = _classify(result)
        reason_code = result.reason_code
        receipt_generated = result.receipt is not None

        if observed == "REFUSE":
            failure_stage = "authorization_decision"
        elif receipt_generated:
            verification = verify_receipt(result.receipt, artifact, action, facts)
            receipt_verified = verification.status == "PASS"
            if not receipt_verified:
                notes = f"receipt failed self-verification: {verification.reason_code}"
    except Exception as exc:  # noqa: BLE001 - an escaping exception is itself a finding
        observed = "EXCEPTION"
        reason_code = type(exc).__name__
        failure_stage = "uncaught_exception"
        notes = (
            "Implementation raised instead of returning a refusal. An escaping "
            f"exception is a fail-closed defect, not a refusal: {exc}"
        )

    passed = observed == spec.expected
    if spec.expected == "ALLOW" and passed:
        passed = receipt_generated and receipt_verified is True

    return {
        "specimen": spec.specimen_id,
        "description": spec.description,
        "category": spec.category,
        "expected_result": spec.expected,
        "observed_result": observed,
        "pass_fail": "PASS" if passed else "FAIL",
        "failure_stage": failure_stage,
        "receipt_generated": receipt_generated,
        "receipt_verified": receipt_verified,
        "reason_code": reason_code,
        "notes": notes,
    }


def _stale_bound_mutation(mutate) -> dict[str, Any]:
    """Return a specimen whose contract body was altered but whose declared
    digests were deliberately NOT recomputed — the real post-binding attack."""
    artifact = copy.deepcopy(load_fixture("banking_payment_specimen.json"))
    mutate(artifact)
    return artifact


def phase_e2e_and_correctness() -> dict[str, Any]:
    rows = [_evaluate_specimen(spec) for spec in E2E_SPECIMENS]

    action_v = load_fixture("actions/send_payment_valid.json")
    facts_v = load_fixture("runtime/facts_valid.json")

    # E2E-06: source/version-bound material changed with NO corresponding valid
    # binding. Built programmatically because every on-disk "mutated" fixture is
    # correctly re-sealed and therefore cannot express this attack.
    def _bump_version(art: dict) -> None:
        art["contract"]["identity"]["version"] = "9.9.9-attacker"

    mutated = _stale_bound_mutation(_bump_version)
    mutated_result = _run(mutated, action_v, facts_v)
    rows.append(
        {
            "specimen": "E2E-06",
            "description": "Source/version material changed with stale (non-recomputed) digest binding",
            "category": "source_version_mutation",
            "expected_result": "REFUSE",
            "observed_result": _classify(mutated_result),
            "pass_fail": "PASS" if mutated_result.decision != "ALLOW" else "FAIL",
            "failure_stage": "digest_binding",
            "receipt_generated": mutated_result.receipt is not None,
            "receipt_verified": None,
            "reason_code": mutated_result.reason_code,
            "notes": "contract.identity.version altered; activation/admission/proof digests left stale",
        }
    )

    # E2E-05: receipt mutation. Every protected field is mutated in turn, so
    # this measures whether the binding covers the whole payload rather than
    # only the one field a single-shot test would happen to pick.
    artifact = load_fixture("banking_payment_specimen.json")
    action = load_fixture("actions/send_payment_valid.json")
    facts = load_fixture("runtime/facts_valid.json")
    baseline = _run(artifact, action, facts)

    mutation_rows = []
    if baseline.receipt is not None:
        for field in sorted(baseline.receipt.keys()):
            tampered = copy.deepcopy(baseline.receipt)
            original = tampered[field]
            tampered[field] = "TAMPERED" if not isinstance(original, str) else original + "-TAMPERED"
            verification = verify_receipt(tampered, artifact, action, facts)
            mutation_rows.append(
                {
                    "mutated_field": field,
                    "detected": verification.status != "PASS",
                    "reason_code": verification.reason_code,
                }
            )

        # Truncation: a receipt missing a protected field must not verify.
        for field in sorted(baseline.receipt.keys()):
            truncated = copy.deepcopy(baseline.receipt)
            del truncated[field]
            verification = verify_receipt(truncated, artifact, action, facts)
            mutation_rows.append(
                {
                    "mutated_field": f"{field} (removed)",
                    "detected": verification.status != "PASS",
                    "reason_code": verification.reason_code,
                }
            )

    all_detected = all(row["detected"] for row in mutation_rows) and bool(mutation_rows)
    rows.append(
        {
            "specimen": "E2E-05",
            "description": "Receipt mutation and truncation across every protected field",
            "category": "receipt_mutation",
            "expected_result": "REFUSE",
            "observed_result": "REFUSE" if all_detected else "ALLOW",
            "pass_fail": "PASS" if all_detected else "FAIL",
            "failure_stage": "receipt_verification",
            "receipt_generated": True,
            "receipt_verified": False,
            "reason_code": "VEIP_RECEIPT_MISMATCH/MALFORMED",
            "notes": (
                f"{len(mutation_rows)} mutation/truncation variants tested; "
                f"{sum(1 for r in mutation_rows if r['detected'])} detected"
            ),
        }
    )

    # E2E-07: deterministic replay (detail recorded in the determinism phase).
    replays = [_run(artifact, action, facts) for _ in range(DETERMINISM_REPS)]
    receipts_identical = all(r.receipt == replays[0].receipt for r in replays)
    decisions_identical = all(r.decision == replays[0].decision for r in replays)
    rows.append(
        {
            "specimen": "E2E-07",
            "description": f"Deterministic replay, {DETERMINISM_REPS} executions of the identical specimen",
            "category": "deterministic_replay",
            "expected_result": "ALLOW",
            "observed_result": "ALLOW" if decisions_identical and replays[0].decision == "ALLOW" else "FAIL",
            "pass_fail": "PASS" if (receipts_identical and decisions_identical) else "FAIL",
            "failure_stage": None if receipts_identical else "determinism",
            "receipt_generated": True,
            "receipt_verified": True,
            "reason_code": replays[0].reason_code,
            "notes": (
                "all protected receipt fields byte-identical across replays"
                if receipts_identical
                else "receipt fields varied across replays"
            ),
        }
    )

    return {
        "specimens": rows,
        "receipt_mutation_detail": mutation_rows,
        "totals": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row["pass_fail"] == "PASS"),
            "failed": sum(1 for row in rows if row["pass_fail"] == "FAIL"),
        },
    }


# --------------------------------------------------------------------------
# Phase 3 + Phase 4 — per-stage latency and throughput
# --------------------------------------------------------------------------

def phase_performance() -> dict[str, Any]:
    artifact_text = load_fixture_text("banking_payment_specimen.json")
    artifact = load_fixture("banking_payment_specimen.json")
    action = load_fixture("actions/send_payment_valid.json")
    facts = load_fixture("runtime/facts_valid.json")
    contract = artifact["contract"]

    projection = project(artifact)
    receipt = _run(artifact, action, facts).receipt

    stages = {
        "contract_parse": {
            "what": "json.loads of the raw contract artifact text",
            "summary": measure(
                lambda: json.loads(artifact_text),
                repetitions=STAGE_REPS,
                inner_batch=STAGE_INNER_BATCH,
            ),
        },
        "validation_and_binding": {
            "what": "verify_artifact: digest-scope validation plus sibling binding agreement",
            "summary": measure(
                lambda: verify_artifact(artifact),
                repetitions=STAGE_REPS,
                inner_batch=STAGE_INNER_BATCH,
            ),
        },
        "canonicalization": {
            "what": "canonical_bytes: RFC 8785 JCS serialization of the contract",
            "summary": measure(
                lambda: canonical_bytes(contract),
                repetitions=STAGE_REPS,
                inner_batch=STAGE_INNER_BATCH,
            ),
        },
        "canonical_digest": {
            "what": "contract_digest: JCS canonicalization plus SHA-256",
            "summary": measure(
                lambda: contract_digest(contract),
                repetitions=STAGE_REPS,
                inner_batch=STAGE_INNER_BATCH,
            ),
        },
        "projection": {
            "what": "project: build the deterministic action-domain projection",
            "summary": measure(
                lambda: project(artifact),
                repetitions=STAGE_REPS,
                inner_batch=STAGE_INNER_BATCH,
            ),
        },
        "projection_digest": {
            "what": "projection_digest over the realized projection",
            "summary": measure(
                lambda: projection_digest(projection),
                repetitions=STAGE_REPS,
                inner_batch=STAGE_INNER_BATCH,
            ),
        },
        "action_check": {
            "what": "check_action: validate a proposed action against the projection",
            "summary": measure(
                lambda: check_action(projection, action),
                repetitions=STAGE_REPS,
                inner_batch=STAGE_INNER_BATCH,
            ),
        },
        "decision_and_receipt": {
            "what": (
                "run_specimen: full orchestration — parse bundle, project, admit facts, "
                "decide, and emit the receipt. Supersets projection and action_check."
            ),
            "summary": measure(
                lambda: _run(artifact, action, facts),
                repetitions=E2E_REPS,
                inner_batch=1,
            ),
        },
        "receipt_verification": {
            "what": (
                "verify_receipt: independently recompute every binding from raw inputs "
                "and compare. Internally re-runs the full decision path."
            ),
            "summary": measure(
                lambda: verify_receipt(receipt, artifact, action, facts),
                repetitions=E2E_REPS,
                inner_batch=1,
            ),
        },
    }

    def full_e2e() -> None:
        parsed = json.loads(artifact_text)
        result = run_specimen(parsed, action, facts, execution_result=EXECUTION_RESULT)
        verify_receipt(result.receipt, parsed, action, facts)

    stages["complete_end_to_end"] = {
        "what": "parse → decide → emit receipt → independently verify receipt",
        "summary": measure(full_e2e, repetitions=E2E_REPS, inner_batch=1),
    }

    cold = {
        "note": (
            "Single un-warmed execution in an already-imported interpreter. The dominant "
            "one-time cost is interpreter startup and module import, reported separately "
            "in the resource profile."
        ),
        "complete_end_to_end_cold": measure_cold(full_e2e),
    }

    throughput = {
        "note": "Single-process, single-threaded, derived from warm mean latency. Not a distributed or multi-core claim.",
        "decisions_per_second": throughput_per_second(stages["decision_and_receipt"]["summary"]),
        "receipts_per_second": throughput_per_second(stages["decision_and_receipt"]["summary"]),
        "receipt_verifications_per_second": throughput_per_second(stages["receipt_verification"]["summary"]),
        "complete_e2e_transactions_per_second": throughput_per_second(stages["complete_end_to_end"]["summary"]),
        "receipts_per_second_caveat": (
            "Receipt emission is not separately callable at this commit: run_specimen "
            "decides and emits in one pass, so decisions/sec and receipts/sec are the "
            "same measurement reported twice, not two independent figures."
        ),
    }

    return {"stages": stages, "cold_vs_warm": cold, "throughput": throughput}


# --------------------------------------------------------------------------
# Phase 5 — bounded scale curves
# --------------------------------------------------------------------------

def phase_scale() -> dict[str, Any]:
    action = load_fixture("actions/send_payment_valid.json")

    action_curve = []
    for count in (1, 10, 100, 1000):
        artifact = make_action_scaled_specimen(count)
        facts = load_fixture("runtime/facts_valid.json")
        control = _run(artifact, action, facts)
        reps = 400 if count < 1000 else 60
        summary = measure(lambda a=artifact, f=facts: _run(a, action, f), repetitions=reps, warmup=10)
        action_curve.append(
            {
                "declared_actions": count,
                "decision": control.decision,
                "reason_code": control.reason_code,
                "latency": summary,
                "peak_traced_memory": measure_peak_memory(lambda a=artifact, f=facts: _run(a, action, f)),
            }
        )

    fact_curve = []
    for count in (10, 100, 1000, 10000):
        artifact, facts = make_fact_scaled_specimen(count)
        control = _run(artifact, action, facts)
        reps = 200 if count <= 100 else (40 if count == 1000 else 5)
        summary = measure(lambda a=artifact, f=facts: _run(a, action, f), repetitions=reps, warmup=3)
        fact_curve.append(
            {
                "required_facts": count,
                "decision": control.decision,
                "reason_code": control.reason_code,
                "latency": summary,
                "peak_traced_memory": measure_peak_memory(lambda a=artifact, f=facts: _run(a, action, f)),
            }
        )

    def _shape(curve: list[dict], key: str) -> str:
        """Describe growth by comparing per-unit cost at the smallest and largest points."""
        first, last = curve[0], curve[-1]
        size_ratio = last[key] / first[key]
        time_ratio = last["latency"]["mean"] / first["latency"]["mean"]
        if time_ratio < size_ratio * 0.25:
            return f"sublinear (size x{size_ratio:.0f} -> time x{time_ratio:.1f})"
        if time_ratio <= size_ratio * 1.5:
            return f"approximately linear (size x{size_ratio:.0f} -> time x{time_ratio:.1f})"
        return f"superlinear — bottleneck candidate (size x{size_ratio:.0f} -> time x{time_ratio:.1f})"

    return {
        "declared_action_scaling": {
            "dimension": "count of declared mediated actions in the projection domain",
            "levels": action_curve,
            "observed_shape": _shape(action_curve, "declared_actions"),
        },
        "required_fact_scaling": {
            "dimension": "count of required facts (contract) matched by supplied facts (bundle)",
            "levels": fact_curve,
            "observed_shape": _shape(fact_curve, "required_facts"),
        },
        "not_evaluated": {
            "multi_contract_corpora": (
                "NOT EVALUATED — the implementation evaluates one artifact per invocation; "
                "there is no multi-contract registry or cross-contract selection path at this "
                "commit whose scaling could be measured without inventing architecture."
            ),
            "concurrent_or_distributed_throughput": (
                "NOT EVALUATED — no concurrency or distribution layer exists at this commit."
            ),
            "persistent_storage_scaling": (
                "NOT EVALUATED — the runtime is stateless over in-memory inputs; there is no "
                "storage backend to scale."
            ),
        },
    }


# --------------------------------------------------------------------------
# Phase 7 — determinism
# --------------------------------------------------------------------------

def phase_determinism() -> dict[str, Any]:
    action = load_fixture("actions/send_payment_valid.json")
    artifact = load_fixture("banking_payment_specimen.json")

    findings = {}
    for label, facts_fixture in (
        ("valid_specimen", "runtime/facts_valid.json"),
        ("refused_specimen", "runtime/facts_stale.json"),
    ):
        facts = load_fixture(facts_fixture)
        results = [_run(artifact, action, facts) for _ in range(DETERMINISM_REPS)]

        decisions = {r.decision for r in results}
        reason_codes = {r.reason_code for r in results}
        receipts = [r.receipt for r in results]

        stable_fields: list[str] = []
        varying_fields: list[str] = []
        if receipts[0] is not None:
            for field in sorted(receipts[0].keys()):
                values = {json.dumps(r[field], sort_keys=True) for r in receipts}
                (stable_fields if len(values) == 1 else varying_fields).append(field)

        findings[label] = {
            "executions": DETERMINISM_REPS,
            "decision_values_observed": sorted(decisions),
            "reason_codes_observed": sorted(reason_codes),
            "decision_stable": len(decisions) == 1,
            "reason_code_stable": len(reason_codes) == 1,
            "receipt_emitted": receipts[0] is not None,
            "stable_receipt_fields": stable_fields,
            "varying_receipt_fields": varying_fields,
        }

    # Independently confirm the digest/projection primitives are stable too.
    contract = artifact["contract"]
    digests = {contract_digest(contract) for _ in range(DETERMINISM_REPS)}
    projections = {
        json.dumps(projection_to_dict(project(artifact)), sort_keys=True)
        for _ in range(DETERMINISM_REPS)
    }

    findings["primitives"] = {
        "contract_digest_distinct_values": len(digests),
        "projection_distinct_values": len(projections),
        "contract_digest_stable": len(digests) == 1,
        "projection_stable": len(projections) == 1,
    }

    valid = findings["valid_specimen"]
    fully_stable = (
        valid["decision_stable"]
        and valid["reason_code_stable"]
        and not valid["varying_receipt_fields"]
        and findings["primitives"]["contract_digest_stable"]
        and findings["primitives"]["projection_stable"]
    )

    findings["determinism_statement"] = (
        (
            "Every observed output is stable across repeated execution of a fixed specimen: "
            "decision, reason code, contract digest, projection, and all protected receipt "
            "fields including decision_time. decision_time is stable because it is bound to "
            "the fact bundle's own declared `now`, not to wall-clock time at invocation — so "
            "at this commit there is no intentionally-varying receipt field. This is "
            "determinism over fixed inputs in a single process; it is not a claim about "
            "cross-version, cross-platform, or cross-implementation reproducibility, none of "
            "which was tested."
        )
        if fully_stable
        else (
            "Determinism is NOT complete. Fields observed to vary across identical "
            f"executions: {valid['varying_receipt_fields']}. Each must be classified as "
            "intentionally variable or as a defect before any reproducibility claim is made."
        )
    )
    findings["fully_deterministic_over_fixed_inputs"] = fully_stable
    return findings


# --------------------------------------------------------------------------
# Phase 8 — adversarial battery
# --------------------------------------------------------------------------

def phase_adversarial() -> dict[str, Any]:
    rows = [_evaluate_specimen(spec) for spec in ADVERSARIAL_SPECIMENS]

    # Structural attacks that are not simple fixture swaps.
    artifact = load_fixture("banking_payment_specimen.json")
    action = load_fixture("actions/send_payment_valid.json")
    facts = load_fixture("runtime/facts_valid.json")

    # Key reordering must not change canonical identity (RFC 8785 property).
    reordered = {k: artifact[k] for k in reversed(list(artifact.keys()))}
    reordered["contract"] = {
        k: artifact["contract"][k] for k in reversed(list(artifact["contract"].keys()))
    }
    same_digest = contract_digest(reordered["contract"]) == contract_digest(artifact["contract"])
    reorder_result = _run(reordered, action, facts)
    rows.append(
        {
            "specimen": "ADV-32",
            "description": "Reordered JSON object keys must not alter canonical identity or decision",
            "category": "reordered_structured_input",
            "expected_result": "ALLOW",
            "observed_result": _classify(reorder_result),
            "pass_fail": "PASS" if (same_digest and reorder_result.decision == "ALLOW") else "FAIL",
            "failure_stage": None if same_digest else "canonicalization",
            "receipt_generated": reorder_result.receipt is not None,
            "receipt_verified": None,
            "reason_code": reorder_result.reason_code,
            "notes": f"digest invariant under key reordering: {same_digest}",
        }
    )

    # Replay: an identical request repeated must yield an identical decision.
    first = _run(artifact, action, facts)
    second = _run(artifact, action, facts)
    replay_identical = first.receipt == second.receipt and first.decision == second.decision
    rows.append(
        {
            "specimen": "ADV-33",
            "description": "Replayed identical request",
            "category": "replay",
            "expected_result": "ALLOW",
            "observed_result": _classify(second),
            "pass_fail": "PASS" if replay_identical else "FAIL",
            "failure_stage": None,
            "receipt_generated": second.receipt is not None,
            "receipt_verified": None,
            "reason_code": second.reason_code,
            "notes": (
                "Replay yields an identical receipt. NOTE: this documents determinism, not "
                "replay *protection* — there is no nonce, sequence number, or single-use "
                "semantics at this commit, so an intercepted receipt is indistinguishable "
                "from a legitimately re-derived one. Recorded as an architectural gap."
            ),
        }
    )

    # Receipt verified against a different action than the one it was issued for.
    other_action = load_fixture("actions/send_payment_out_of_enum_value.json")
    cross = verify_receipt(first.receipt, artifact, other_action, facts)
    rows.append(
        {
            "specimen": "ADV-34",
            "description": "Receipt presented against a different action than it was issued for",
            "category": "receipt_context_substitution",
            "expected_result": "REFUSE",
            "observed_result": "REFUSE" if cross.status != "PASS" else "ALLOW",
            "pass_fail": "PASS" if cross.status != "PASS" else "FAIL",
            "failure_stage": "receipt_verification",
            "receipt_generated": True,
            "receipt_verified": False,
            "reason_code": cross.reason_code,
            "notes": "",
        }
    )

    # ADV-35/36: genuine post-binding mutation with stale digests.
    for adv_id, label, mutate in (
        (
            "ADV-35",
            "Contract version altered, digest binding left stale",
            lambda art: art["contract"]["identity"].__setitem__("version", "9.9.9-attacker"),
        ),
        (
            "ADV-36",
            "Projection domain widened (amount retyped), digest binding left stale",
            lambda art: art["contract"]["projection_domain"]["actions"]["send_payment"][
                "parameters"
            ]["amount"].__setitem__("value_type", "string"),
        ),
    ):
        attacked = _stale_bound_mutation(mutate)
        outcome = _run(attacked, action, facts)
        rows.append(
            {
                "specimen": adv_id,
                "description": label,
                "category": "post_binding_mutation",
                "expected_result": "REFUSE",
                "observed_result": _classify(outcome),
                "pass_fail": "PASS" if outcome.decision != "ALLOW" else "FAIL",
                "failure_stage": "digest_binding",
                "receipt_generated": outcome.receipt is not None,
                "receipt_verified": None,
                "reason_code": outcome.reason_code,
                "notes": "",
            }
        )

    # ADV-37: admission approvals are not an authorization gate, but they must
    # still be bound into the evidence so a forged admission is distinguishable.
    forged = copy.deepcopy(artifact)
    forged["admission"]["approvals"] = [{"approval_id": "forged", "approver": "attacker"}]
    forged_result = _run(forged, action, facts)
    baseline_result = _run(artifact, action, facts)
    binding_holds = (
        forged_result.receipt is not None
        and baseline_result.receipt is not None
        and forged_result.receipt["admission_digest"] != baseline_result.receipt["admission_digest"]
        and forged_result.receipt["receipt_digest"] != baseline_result.receipt["receipt_digest"]
    )
    cross_verify = verify_receipt(baseline_result.receipt, forged, action, facts)
    rows.append(
        {
            "specimen": "ADV-37",
            "description": "Forged admission approvals must alter the bound evidence",
            "category": "admission_evidence_binding",
            "expected_result": "ALLOW",
            "observed_result": _classify(forged_result),
            "pass_fail": "PASS" if (binding_holds and cross_verify.status != "PASS") else "FAIL",
            "failure_stage": None,
            "receipt_generated": True,
            "receipt_verified": False,
            "reason_code": forged_result.reason_code,
            "notes": (
                "Decision is ALLOW because approvals are not an authorization gate at this "
                "commit (finding AC-035-F1). The evidence binding nonetheless holds: "
                f"admission_digest and receipt_digest both change ({binding_holds}), and a "
                "receipt issued for the unforged admission does not verify against the forged "
                f"one ({cross_verify.reason_code})."
            ),
        }
    )

    by_category: dict[str, dict[str, int]] = {}
    for row in rows:
        bucket = by_category.setdefault(row["category"], {"PASS": 0, "FAIL": 0})
        bucket[row["pass_fail"]] += 1

    return {
        "results": rows,
        "totals": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row["pass_fail"] == "PASS"),
            "failed": sum(1 for row in rows if row["pass_fail"] == "FAIL"),
            "not_evaluated": 0,
        },
        "by_category": by_category,
    }


# --------------------------------------------------------------------------
# Phase 9 — resource profile
# --------------------------------------------------------------------------

def phase_resources() -> dict[str, Any]:
    artifact = load_fixture("banking_payment_specimen.json")
    action = load_fixture("actions/send_payment_valid.json")
    facts = load_fixture("runtime/facts_valid.json")
    result = _run(artifact, action, facts)

    # Interpreter + import cost, measured out-of-process so it is not masked by
    # this process having already imported everything.
    startup_samples = []
    for _ in range(5):
        start = time.perf_counter()
        subprocess.run(
            [sys.executable, "-c", "import authcontract.veip"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        )
        startup_samples.append((time.perf_counter() - start) * 1000)

    def _size(value: Any) -> int:
        return len(json.dumps(value, separators=(",", ":")).encode("utf-8"))

    return {
        "process_startup": {
            "unit": "milliseconds",
            "what": "python -c 'import authcontract.veip', out-of-process, 5 samples",
            "samples": [round(s, 2) for s in startup_samples],
            "min": round(min(startup_samples), 2),
            "mean": round(sum(startup_samples) / len(startup_samples), 2),
            "max": round(max(startup_samples), 2),
        },
        "peak_memory": {
            "note": "tracemalloc peak attributable to one execution; excludes interpreter baseline",
            "single_decision": measure_peak_memory(lambda: _run(artifact, action, facts)),
            "single_verification": measure_peak_memory(
                lambda: verify_receipt(result.receipt, artifact, action, facts)
            ),
        },
        "process_max_rss": {
            "unit": "kilobytes",
            "note": "whole-process peak RSS at end of benchmark run, including interpreter and harness",
            "value": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "artifact_sizes": {
            "unit": "bytes (compact JSON encoding)",
            "contract_artifact": _size(artifact),
            "contract_body_only": _size(artifact["contract"]),
            "canonical_contract_bytes": len(canonical_bytes(artifact["contract"])),
            "action": _size(action),
            "fact_bundle": _size(facts),
            "projection": _size(projection_to_dict(project(artifact))),
            "receipt": _size(result.receipt),
        },
    }


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

CLAIM_CEILING = [
    "This benchmark measures a bounded MVP-alpha implementation on one synthetic banking specimen family.",
    "It does NOT establish production readiness.",
    "It does NOT establish regulatory or legal correctness.",
    "It does NOT establish universal source-to-rule derivation.",
    "It does NOT establish arbitrary-domain compatibility.",
    "It does NOT establish security certification.",
    "It does NOT establish distributed or concurrent scalability.",
    "It does NOT constitute a formal proof.",
    "It does NOT establish comparative superiority over any other system.",
    "Latency and throughput figures are single-process, single-machine, and environment-specific.",
]


def main() -> int:
    started = time.time()
    environment = capture_environment()

    print("AC-035 benchmark — commit", environment["commit_sha"][:12])
    print("  phase: end-to-end + correctness matrix")
    e2e = phase_e2e_and_correctness()
    print("  phase: performance")
    performance = phase_performance()
    print("  phase: scale curves")
    scale = phase_scale()
    print("  phase: determinism")
    determinism = phase_determinism()
    print("  phase: adversarial battery")
    adversarial = phase_adversarial()
    print("  phase: resource profile")
    resources = phase_resources()

    common = {
        "work_order": "AC-035",
        "environment": environment,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    write_result("AC-035-E2E-RESULTS.json", {**common, "end_to_end": e2e})
    write_result("AC-035-PERFORMANCE.json", {**common, "performance": performance, "scaling": scale})
    write_result(
        "AC-035-CORRECTNESS-MATRIX.json",
        {**common, "end_to_end_matrix": e2e["specimens"], "adversarial_matrix": adversarial},
    )
    write_result("AC-035-DETERMINISM.json", {**common, "determinism": determinism})
    write_result("AC-035-RESOURCE-PROFILE.json", {**common, "resources": resources})

    e2e_totals = e2e["totals"]
    adv_totals = adversarial["totals"]
    print()
    print(f"  E2E:         {e2e_totals['passed']}/{e2e_totals['total']} passed")
    print(f"  Adversarial: {adv_totals['passed']}/{adv_totals['total']} passed")
    print(f"  E2E p50:     {performance['stages']['complete_end_to_end']['summary']['p50']} us")
    print(f"  E2E tps:     {performance['throughput']['complete_e2e_transactions_per_second']}")
    print(f"  Determinism: {'stable' if determinism['fully_deterministic_over_fixed_inputs'] else 'NOT STABLE'}")
    print(f"  elapsed:     {time.time() - started:.1f}s")

    return 0 if (e2e_totals["failed"] == 0 and adv_totals["failed"] == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
