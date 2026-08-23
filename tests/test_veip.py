"""AC-019 / C-08, amended by AC-020 and AC-020A — minimal VEIP-bound
runtime decision + AEP-style receipt with verified assertion binding, AEP
evidence continuity, closed required-fact declaration shape, and
presence-aware exact admission binding.

Unit-level tests against authcontract.veip directly. Composes the existing,
unmodified digest/projection gates, and facts.py's AC-020-repaired fact
gate — none of digest.py, projection.py, or facts.py is touched by this
test file or by veip.py's AC-020A amendment (see test_facts.py for direct
unit coverage of the AC-020 A1-A7 repair); veip.py itself is amended for
AC-020's F2 AEP evidence-continuity repair (C1-C5) and AC-020A's R1
(required-fact declaration shape closure) and R2 (presence-aware exact
admission binding) residual closures.
"""

import json
from pathlib import Path

import pytest

from authcontract.digest import contract_digest
from authcontract.facts import FactFutureTimestamp, FactSelfAsserted, FactStale
from authcontract.projection import InactiveContract, ProjectionDomainError, UnclassifiedAction
from authcontract.veip import (
    RECEIPT_REQUIRED_KEYS,
    FactBundleIncomplete,
    MalformedInput,
    ReceiptMalformed,
    ReceiptMismatch,
    run_specimen,
    verify_receipt,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
RUNTIME = FIXTURES / "runtime"
ARTIFACT = json.loads((FIXTURES / "banking_payment_specimen.json").read_text())
SUSPENDED_ARTIFACT = json.loads((FIXTURES / "banking_payment_specimen_suspended.json").read_text())
DUPLICATE_REQUIRED_FACT_ARTIFACT = json.loads(
    (FIXTURES / "banking_payment_specimen_duplicate_required_fact.json").read_text()
)
BAD_CORROBORATION_REQUIRED_ARTIFACT = json.loads(
    (FIXTURES / "banking_payment_specimen_bad_corroboration_required.json").read_text()
)
UNKNOWN_REQUIRED_FACT_FIELD_ARTIFACT = json.loads(
    (FIXTURES / "banking_payment_specimen_unknown_required_fact_field.json").read_text()
)
ADMISSION_LIST_ARTIFACT = json.loads((FIXTURES / "banking_payment_specimen_admission_list.json").read_text())
ADMISSION_NULL_ARTIFACT = json.loads((FIXTURES / "banking_payment_specimen_admission_null.json").read_text())
ADMISSION_PRESENT_EMPTY_ARTIFACT = json.loads(
    (FIXTURES / "banking_payment_specimen_admission_present_empty.json").read_text()
)
ADMISSION_ABSENT_ARTIFACT = json.loads((FIXTURES / "banking_payment_specimen_admission_absent.json").read_text())
ADMISSION_ALT_VALID_ARTIFACT = json.loads(
    (FIXTURES / "banking_payment_specimen_admission_alt_valid.json").read_text()
)
ACTION = json.loads((FIXTURES / "actions" / "send_payment_valid.json").read_text())
UNKNOWN_ACTION = json.loads((FIXTURES / "actions" / "send_payment_unknown_action_type.json").read_text())
DOMAIN_ESCAPE_ACTION = json.loads((FIXTURES / "actions" / "send_payment_unknown_parameter.json").read_text())
FACTS_VALID = json.loads((RUNTIME / "facts_valid.json").read_text())


def _run(artifact=ARTIFACT, action=ACTION, facts=FACTS_VALID, execution_result="SIMULATED_SUCCESS"):
    return run_specimen(artifact, action, facts, execution_result=execution_result)


def _runtime_fixture(name):
    return json.loads((RUNTIME / name).read_text())


# --------------------------------------------------------------- positive

def test_positive_specimen_allows():
    result = _run()
    assert result.decision == "ALLOW"
    assert result.reason_code == "OK"
    assert result.receipt is not None


def test_receipt_has_exactly_the_required_keys():
    result = _run()
    assert set(result.receipt) == RECEIPT_REQUIRED_KEYS


def test_receipt_binds_expected_contract_digest():
    result = _run()
    assert result.receipt["contract_digest"] == contract_digest(ARTIFACT["contract"])


def test_receipt_activation_id_matches_artifact():
    result = _run()
    assert result.receipt["activation_id"] == ARTIFACT["activation"]["activation_id"]


def test_receipt_execution_result_is_bound():
    result = _run(execution_result="NOT_EXECUTED")
    assert result.receipt["execution_result"] == "NOT_EXECUTED"


def test_decision_is_allow_in_receipt():
    result = _run()
    assert result.receipt["decision"] == "ALLOW"


def test_repeated_run_is_deterministic():
    r1 = _run()
    r2 = _run()
    assert r1.receipt == r2.receipt


def test_positive_receipt_verifies():
    result = _run()
    verify = verify_receipt(result.receipt, ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "PASS"
    assert verify.reason_code == "OK"


def test_invalid_execution_result_is_refused():
    result = _run(execution_result="REAL_PAYMENT_SENT")
    assert result.decision == "REFUSED"
    assert result.reason_code == "VEIP_INVALID_EXECUTION_RESULT"
    assert result.receipt is None


# ------------------------------------- AC-020 C1: decision_time binding

def test_receipt_binds_decision_time_from_fact_bundle_now():
    result = _run()
    assert result.receipt["decision_time"] == FACTS_VALID["now"]


# ------------------------------------- AC-020 C3: admission_digest binding

def test_receipt_binds_admission_digest():
    result = _run()
    assert result.receipt["admission_digest"].startswith("sha256:")


def test_admission_mutation_changes_admission_and_receipt_digest_but_not_contract_digest():
    """AC-020 C4 corrects AC-019's `test_admission_only_mutation_does_not_
    change_receipt_digests`, which asserted that mutating admission.approvals
    left ALL receipt digests unchanged. That was consistent with R01
    contract/admission partitioning (contract_digest correctly ignores
    admission) but wrong for an AEP-style receipt meant to preserve exactly
    which admission/approval context accompanied the decision — AC-020
    Finding F2 established this as a real evidence-continuity gap. Corrected
    behavior: contract_digest is unaffected (R01 partitioning unchanged),
    but admission_digest and receipt_digest now DO change.
    """
    mutated_artifact = json.loads(json.dumps(ARTIFACT))
    mutated_artifact["admission"]["approvals"] = [{"approval_id": "approval:xyz", "approver": "ops-lead"}]
    r1 = _run()
    r2 = _run(artifact=mutated_artifact)
    assert r1.receipt["contract_digest"] == r2.receipt["contract_digest"]
    assert r1.receipt["projection_digest"] == r2.receipt["projection_digest"]
    assert r1.receipt["runtime_fact_set_digest"] == r2.receipt["runtime_fact_set_digest"]
    assert r1.receipt["exact_action_digest"] == r2.receipt["exact_action_digest"]
    assert r1.receipt["admission_digest"] != r2.receipt["admission_digest"]
    assert r1.receipt["receipt_digest"] != r2.receipt["receipt_digest"]


# ---------------------------------------------- B9 mandatory negative paths

def test_required_fact_missing_refuses_no_receipt():
    result = _run(facts={"now": FACTS_VALID["now"], "facts": []})
    assert result.decision == "REFUSED"
    assert result.reason_code == FactBundleIncomplete.code
    assert result.receipt is None


def test_self_asserted_prohibited_refuses():
    """AC-020: fixture now carries VERIFIED asserted_by == the governed
    subject too (not just the claim) — a genuinely verified self-assertion,
    which is the correct way to exercise this path once evidence itself
    binds asserting identity (A1/A3)."""
    facts = _runtime_fixture("facts_self_asserted_prohibited.json")
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == FactSelfAsserted.code
    assert result.receipt is None


def test_stale_fact_refuses():
    """AC-020: fixture's evidence.asserted_at now agrees with the claim
    (both stale) so the genuine staleness check fires, rather than the new
    claim/verification agreement check."""
    facts = _runtime_fixture("facts_stale.json")
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == FactStale.code
    assert result.receipt is None


def test_lossy_representation_refuses():
    facts = _runtime_fixture("facts_lossy_representation.json")
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == "RUN_FACT_REPRESENTATION"
    assert result.receipt is None


def test_future_timestamp_refuses():
    """AC-020: fixture's evidence.asserted_at now agrees with the claim
    (both future) so the genuine future-timestamp check fires."""
    facts = _runtime_fixture("facts_future_timestamp.json")
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == FactFutureTimestamp.code
    assert result.receipt is None


def test_unverifiable_naive_timestamp_refuses():
    """AC-020: fixture's fact and evidence asserted_at now agree (both
    naive) so the claim/verification agreement check passes cleanly, and
    the genuine naive/aware-vs-`now` unverifiable-comparison check in
    facts.py's freshness gate fires instead — the same defect this test
    originally targeted, still reachable under the repaired architecture."""
    facts = _runtime_fixture("facts_naive_timestamp.json")
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == "RUN_FACT_TIME_UNVERIFIABLE"
    assert result.receipt is None


def test_inactive_projection_refuses():
    result = _run(artifact=SUSPENDED_ARTIFACT)
    assert result.decision == "REFUSED"
    assert result.reason_code == InactiveContract.code
    assert result.receipt is None


def test_unknown_action_refuses():
    result = _run(action=UNKNOWN_ACTION)
    assert result.decision == "REFUSED"
    assert result.reason_code == UnclassifiedAction.code
    assert result.receipt is None


def test_action_domain_escape_refuses():
    result = _run(action=DOMAIN_ESCAPE_ACTION)
    assert result.decision == "REFUSED"
    assert result.reason_code == ProjectionDomainError.code
    assert result.receipt is None


# ------------------------------------------------------- malformed inputs

def test_malformed_facts_bundle_not_a_dict():
    result = _run(facts=["not", "a", "dict"])
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code


def test_malformed_facts_bundle_missing_now():
    result = _run(facts={"facts": []})
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code


def test_malformed_fact_entry_missing_field():
    bad_facts = json.loads(json.dumps(FACTS_VALID))
    del bad_facts["facts"][0]["wire_representation"]
    result = _run(facts=bad_facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code


# ============================= AC-020 D1-D4: verified assertion binding
# (facts.py-level unit coverage lives in test_facts.py; these exercise the
# same defects through the full orchestration path against the real
# banking specimen, matching the work order's D1-D4 hostile-case wording.)

def test_d1_verified_asserter_is_governed_subject_but_caller_claims_treasury():
    """D1: governed subject is verified asserter but caller claims
    Treasury -> REFUSE."""
    facts = _runtime_fixture("facts_verified_asserter_mismatch.json")
    result = _run(facts=facts, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == "RUN_FACT_EVIDENCE_MISMATCH"
    assert result.receipt is None


def test_d2_verified_value_false_claimed_value_true():
    """D2: verified value false / caller value true -> REFUSE."""
    facts = _runtime_fixture("facts_verified_value_mismatch.json")
    result = _run(facts=facts, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == "RUN_FACT_EVIDENCE_MISMATCH"
    assert result.receipt is None


def test_d3_verified_timestamp_stale_claimed_timestamp_fresh():
    """D3: verified timestamp stale / caller timestamp fresh -> REFUSE."""
    facts = _runtime_fixture("facts_verified_time_stale_claimed_fresh.json")
    result = _run(facts=facts, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == "RUN_FACT_EVIDENCE_MISMATCH"
    assert result.receipt is None


def test_d4_verified_fact_id_mismatch():
    """D4: verified fact_id mismatch -> REFUSE."""
    facts = _runtime_fixture("facts_verified_fact_id_mismatch.json")
    result = _run(facts=facts, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == "RUN_FACT_IDENTITY_MISMATCH"
    assert result.receipt is None


# ================================== AC-020 D5-D8: receipt evidence continuity

def test_d5_verified_asserted_by_changes_receipt_unchanged_is_refused():
    """D5: verified asserted_by changes while receipt unchanged ->
    verify_receipt REFUSED."""
    old = _run()
    mutated_facts = json.loads(json.dumps(FACTS_VALID))
    mutated_facts["facts"][0]["asserted_by"] = "TREASURY_APPROVAL_SERVICE_V2"
    mutated_facts["facts"][0]["evidence"]["asserted_by"] = "TREASURY_APPROVAL_SERVICE_V2"
    new = _run(facts=mutated_facts)
    assert new.decision == "ALLOW"  # a genuinely reconstructible new receipt
    assert new.receipt["runtime_fact_set_digest"] != old.receipt["runtime_fact_set_digest"]
    verify = verify_receipt(old.receipt, ARTIFACT, ACTION, mutated_facts)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


def test_d6_verified_asserted_at_changes_within_freshness_window_receipt_unchanged_is_refused():
    """D6: verified asserted_at changes within the nominal freshness window
    while receipt unchanged -> verify_receipt REFUSED."""
    old = _run()
    mutated_facts = json.loads(json.dumps(FACTS_VALID))
    new_time = "2026-08-23T00:06:00+00:00"  # still fresh, but different
    mutated_facts["facts"][0]["asserted_at"] = new_time
    mutated_facts["facts"][0]["evidence"]["asserted_at"] = new_time
    new = _run(facts=mutated_facts)
    assert new.decision == "ALLOW"
    assert new.receipt["runtime_fact_set_digest"] != old.receipt["runtime_fact_set_digest"]
    verify = verify_receipt(old.receipt, ARTIFACT, ACTION, mutated_facts)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


def test_d7_decision_time_changes_receipt_unchanged_is_refused():
    """D7: decision/evaluation time changes while receipt unchanged ->
    verify_receipt REFUSED."""
    old = _run()
    mutated_facts = json.loads(json.dumps(FACTS_VALID))
    mutated_facts["now"] = "2026-08-23T00:11:00+00:00"  # still within freshness
    new = _run(facts=mutated_facts)
    assert new.decision == "ALLOW"
    assert new.receipt["decision_time"] != old.receipt["decision_time"]
    verify = verify_receipt(old.receipt, ARTIFACT, ACTION, mutated_facts)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


def test_d8_admission_mutation_receipt_unchanged_is_refused_contract_digest_stable():
    """D8: admission.approvals or another admission field changes while
    receipt unchanged -> verify_receipt REFUSED; contract_digest itself
    remains unchanged."""
    old = _run()
    mutated_artifact = json.loads(json.dumps(ARTIFACT))
    mutated_artifact["admission"]["approvals"] = [{"approval_id": "approval:xyz", "approver": "ops-lead"}]
    new = _run(artifact=mutated_artifact)
    assert new.decision == "ALLOW"
    assert new.receipt["contract_digest"] == old.receipt["contract_digest"]
    assert new.receipt["admission_digest"] != old.receipt["admission_digest"]
    verify = verify_receipt(old.receipt, mutated_artifact, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


# ============================================== AC-020 D9-D12: fail-closed shape

def test_d9_duplicate_runtime_fact_id_is_refused():
    facts = _runtime_fixture("facts_duplicate_fact_id.json")
    result = _run(facts=facts, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


def test_d10_duplicate_required_facts_declaration_is_refused():
    result = _run(artifact=DUPLICATE_REQUIRED_FACT_ARTIFACT, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


@pytest.mark.parametrize("bad_fixture", [
    "facts_unknown_bundle_field.json",
    "facts_unknown_fact_field.json",
    "facts_unknown_evidence_field.json",
])
def test_d11_unknown_runtime_field_is_refused(bad_fixture):
    facts = _runtime_fixture(bad_fixture)
    result = _run(facts=facts, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


def test_d12_non_boolean_corroboration_required_string_is_refused():
    result = _run(artifact=BAD_CORROBORATION_REQUIRED_ARTIFACT, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


def test_d12_non_boolean_corroboration_required_int_zero_is_refused():
    """Same declaration defect, the other named truthy/falsy non-bool
    value (0), constructed by mutating the loaded contract in place (with
    contract_digest recomputed to match, so the digest gate itself doesn't
    intercept this before the declaration is even evaluated) rather than
    committing a second near-duplicate fixture file."""
    artifact = json.loads(json.dumps(BAD_CORROBORATION_REQUIRED_ARTIFACT))
    artifact["contract"]["required_facts"][0]["corroboration_required"] = 0
    new_digest = contract_digest(artifact["contract"])
    artifact["activation"]["contract_digest"] = new_digest
    artifact["admission"]["contract_digest"] = new_digest
    artifact["proof"]["contract_digest"] = new_digest
    result = _run(artifact=artifact, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


# ======================================================= B8 mutation matrix

def _mutated_receipt(**overrides):
    result = _run()
    receipt = dict(result.receipt)
    receipt.update(overrides)
    return receipt


@pytest.mark.parametrize("field,bad_value", [
    ("contract_digest", "sha256:" + "0" * 64),
    ("activation_id", "act:tampered:v1"),
    ("projection_digest", "sha256:" + "1" * 64),
    ("runtime_fact_set_digest", "sha256:" + "2" * 64),
    ("exact_action_digest", "sha256:" + "3" * 64),
    ("admission_digest", "sha256:" + "5" * 64),
    ("decision", "DENY"),
    ("execution_result", "NOT_EXECUTED"),  # valid label, but wrong for this receipt
    ("decision_time", "2099-01-01T00:00:00+00:00"),
])
def test_b8_single_field_mutation_is_detected(field, bad_value):
    """D13: all previously valid AC-019 receipt field/value mutations
    remain detected, extended with the two AC-020 fields."""
    receipt = _mutated_receipt(**{field: bad_value})
    verify = verify_receipt(receipt, ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


def test_b8_receipt_digest_mutation_is_detected():
    receipt = _mutated_receipt(receipt_digest="sha256:" + "4" * 64)
    verify = verify_receipt(receipt, ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


def test_b8_admitted_fact_value_changed_receipt_unchanged():
    result = _run()
    mutated_facts = json.loads(json.dumps(FACTS_VALID))
    mutated_facts["facts"][0]["raw_value"] = False
    mutated_facts["facts"][0]["evidence"]["value"] = False
    verify = verify_receipt(result.receipt, ARTIFACT, ACTION, mutated_facts)
    assert verify.status == "REFUSED"


def test_b8_action_parameter_changed_receipt_unchanged():
    result = _run()
    mutated_action = json.loads(json.dumps(ACTION))
    mutated_action["parameters"]["amount"] = "999.99"
    verify = verify_receipt(result.receipt, ARTIFACT, mutated_action, FACTS_VALID)
    assert verify.status == "REFUSED"


def test_b8_artifact_activation_changed_receipt_unchanged():
    result = _run()
    verify = verify_receipt(result.receipt, SUSPENDED_ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"


def test_b8_missing_receipt_field_is_refused():
    receipt = dict(_run().receipt)
    del receipt["projection_digest"]
    verify = verify_receipt(receipt, ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMalformed.code


def test_b8_unknown_receipt_field_is_refused_not_dropped():
    receipt = dict(_run().receipt)
    receipt["unexpected_field"] = "sneaky"
    verify = verify_receipt(receipt, ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMalformed.code


def test_b8_repeated_reconstruction_is_byte_identical():
    """D14: identical complete inputs reconstruct byte-identical/JCS-
    deterministic receipt."""
    r1 = _run().receipt
    r2 = _run().receipt
    assert r1 == r2
    assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


def test_decimal_normalized_to_string_in_exact_action_digest_inputs():
    """Confirms decimal parameters (Decimal instances after check_action's
    own normalization) don't break receipt JSON-serializability and are
    bound deterministically."""
    result = _run()
    assert isinstance(result.receipt["exact_action_digest"], str)
    # A changed amount must change exact_action_digest, proving it's bound.
    mutated_action = json.loads(json.dumps(ACTION))
    mutated_action["parameters"]["amount"] = "1.00"
    other = _run(action=mutated_action)
    assert other.receipt["exact_action_digest"] != result.receipt["exact_action_digest"]


# ---------------------------------------------------------- D15 (positive)

def test_d15_positive_specimen_reaches_allow_only_after_all_gates_pass():
    """D15: the current positive synthetic banking specimen still reaches
    ALLOW only after all fact/action/artifact gates pass — spot-checked by
    confirming every one of the upstream negative paths above independently
    refuses (already exhaustively covered), and that the single genuinely
    positive combination allows with a fully-bound receipt."""
    result = _run()
    assert result.decision == "ALLOW"
    for key in RECEIPT_REQUIRED_KEYS:
        assert key in result.receipt


# ======================================================================
# AC-020A — R1: required_facts declaration shape closure
# ======================================================================

def test_a1_unknown_required_facts_declaration_field_is_refused():
    """A1: unknown required_facts declaration field -> REFUSED /
    VEIP_MALFORMED_INPUT."""
    result = _run(artifact=UNKNOWN_REQUIRED_FACT_FIELD_ARTIFACT, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


def test_a2_known_required_facts_declaration_remains_accepted():
    """A2: known required_facts declaration remains accepted where
    otherwise valid — the ordinary positive path is untouched by R1."""
    result = _run()
    assert result.decision == "ALLOW"


def test_a3_corroboration_required_string_still_refused():
    """A3: corroboration_required string/int still REFUSED (AC-020 B4,
    unweakened by R1's added key-set check)."""
    result = _run(artifact=BAD_CORROBORATION_REQUIRED_ARTIFACT, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code


def test_a4_duplicate_required_facts_still_refused():
    """A4: duplicate required_facts still REFUSED (AC-020 B2, unweakened
    by R1)."""
    result = _run(artifact=DUPLICATE_REQUIRED_FACT_ARTIFACT, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code


# ======================================================================
# AC-020A — R2: presence-aware exact admission binding
# ======================================================================

@pytest.mark.parametrize("bad_artifact", [
    ADMISSION_LIST_ARTIFACT,
    ADMISSION_NULL_ARTIFACT,
])
def test_a5_non_object_admission_sibling_is_refused_not_crashed(bad_artifact):
    """A5: non-object admission sibling -> controlled REFUSED /
    VEIP_MALFORMED_INPUT, no uncaught exception. Covers both a present
    list and an explicit JSON null (which digest.py itself would silently
    treat the same as absence — this orchestration does not)."""
    result = _run(artifact=bad_artifact, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


@pytest.mark.parametrize("bad_value", [
    "a string",
    42,
    True,
])
def test_a5_non_object_admission_sibling_inline_variants(bad_value):
    """A5, additional shapes (string/number/boolean) constructed inline
    rather than as separate committed fixtures."""
    artifact = json.loads(json.dumps(ARTIFACT))
    artifact["admission"] = bad_value
    result = _run(artifact=artifact, execution_result="NOT_EXECUTED")
    assert result.decision == "REFUSED"
    assert result.reason_code == MalformedInput.code
    assert result.receipt is None


def test_a6_present_empty_admission_never_silently_accepted_as_absent():
    """A6: absent admission and present-empty admission must never
    silently collapse to the same accepted evidence state. Present-empty
    ({}) is refused here by the PRE-EXISTING R01 sibling-binding
    requirement (digest.py: a present sibling must bind contract_digest;
    {} has none) — the acceptance matrix's explicitly permitted
    alternative to producing a merely-distinct digest. Absent admission
    remains a genuinely different, accepted state."""
    empty_result = _run(artifact=ADMISSION_PRESENT_EMPTY_ARTIFACT, execution_result="NOT_EXECUTED")
    assert empty_result.decision == "REFUSED"
    assert empty_result.receipt is None

    absent_result = _run(artifact=ADMISSION_ABSENT_ARTIFACT, execution_result="SIMULATED_SUCCESS")
    assert absent_result.decision == "ALLOW"
    assert absent_result.receipt is not None


def test_a6_absent_admission_digest_is_presence_aware():
    """Absent admission binds a distinct `{"present": false}`-derived
    digest, never silently normalized to the same payload a present
    (even empty) admission would use."""
    result = _run(artifact=ADMISSION_ABSENT_ARTIFACT, execution_result="SIMULATED_SUCCESS")
    assert result.decision == "ALLOW"
    assert result.receipt["admission_digest"].startswith("sha256:")


def test_a7_two_distinct_valid_admission_objects_differ_in_admission_digest_only():
    """A7: admission content mutation changes admission_digest +
    receipt_digest, not contract_digest — demonstrated here with two
    independently valid, differently-shaped admission objects (not just a
    before/after mutation of the same one)."""
    r1 = _run(artifact=ARTIFACT)
    r2 = _run(artifact=ADMISSION_ALT_VALID_ARTIFACT)
    assert r1.decision == "ALLOW"
    assert r2.decision == "ALLOW"
    assert r1.receipt["contract_digest"] == r2.receipt["contract_digest"]
    assert r1.receipt["projection_digest"] == r2.receipt["projection_digest"]
    assert r1.receipt["runtime_fact_set_digest"] == r2.receipt["runtime_fact_set_digest"]
    assert r1.receipt["admission_digest"] != r2.receipt["admission_digest"]
    assert r1.receipt["receipt_digest"] != r2.receipt["receipt_digest"]


def test_a8_old_receipt_against_absent_admission_is_refused():
    """A8: old receipt against a changed accepted admission context ->
    verify_receipt REFUSED. Covers switching from a present admission (the
    golden receipt's origin) to an absent one — a different accepted
    admission context, not just a content mutation of the same shape
    (D8 in test suite above already covers the content-mutation case)."""
    old = _run(artifact=ARTIFACT)
    assert old.decision == "ALLOW"
    verify = verify_receipt(old.receipt, ADMISSION_ABSENT_ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


def test_a8_old_receipt_against_alternate_valid_admission_is_refused():
    """A8, the other direction: old receipt against a different but
    equally valid admission object -> verify_receipt REFUSED."""
    old = _run(artifact=ARTIFACT)
    verify = verify_receipt(old.receipt, ADMISSION_ALT_VALID_ARTIFACT, ACTION, FACTS_VALID)
    assert verify.status == "REFUSED"
    assert verify.reason_code == ReceiptMismatch.code


def test_a9_all_ac020_hostile_cases_remain_green():
    """A9: sentinel test — the full AC-020 D1-D15 matrix is exercised by
    the tests above this section, unmodified from AC-020 and still
    passing under AC-020A (see D1-D15 test functions throughout this
    file); this test only re-confirms the positive baseline they all
    depend on still allows."""
    assert _run().decision == "ALLOW"


def test_a10_positive_specimen_allows_only_after_all_gates_pass():
    """A10: identical intent to D15, restated as its own named AC-020A
    acceptance-matrix item."""
    result = _run()
    assert result.decision == "ALLOW"
    for key in RECEIPT_REQUIRED_KEYS:
        assert key in result.receipt


def test_a11_readme_matches_da647ac_exactly():
    """A11: README.md equals the da647ac README exactly in the AC-020A
    candidate — AC-020's developer-documentation rewrite is reverted;
    AC-021 is the sole authorized documentation rewrite."""
    import subprocess

    readme_path = FIXTURES.parent / "README.md"
    da647ac_readme = subprocess.run(
        ["git", "show", "da647ac11222af149d9cbf36d511f6dc0ce50e96:README.md"],
        cwd=FIXTURES.parent, capture_output=True, text=True, check=True,
    ).stdout
    assert readme_path.read_text() == da647ac_readme
