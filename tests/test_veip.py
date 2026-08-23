"""AC-019 / C-08 — minimal VEIP-bound runtime decision + AEP-style receipt.

Unit-level tests against authcontract.veip directly. Composes the existing,
unmodified digest/projection/facts gates — none of digest.py, facts.py, or
projection.py is touched by this test file or by veip.py itself.
"""

import json
from datetime import timedelta
from decimal import Decimal
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
ARTIFACT = json.loads((FIXTURES / "banking_payment_specimen.json").read_text())
SUSPENDED_ARTIFACT = json.loads((FIXTURES / "banking_payment_specimen_suspended.json").read_text())
ACTION = json.loads((FIXTURES / "actions" / "send_payment_valid.json").read_text())
UNKNOWN_ACTION = json.loads((FIXTURES / "actions" / "send_payment_unknown_action_type.json").read_text())
DOMAIN_ESCAPE_ACTION = json.loads((FIXTURES / "actions" / "send_payment_unknown_parameter.json").read_text())
FACTS_VALID = json.loads((FIXTURES / "runtime" / "facts_valid.json").read_text())


def _run(artifact=ARTIFACT, action=ACTION, facts=FACTS_VALID, execution_result="SIMULATED_SUCCESS"):
    return run_specimen(artifact, action, facts, execution_result=execution_result)


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


# ---------------------------------------------- B9 mandatory negative paths

def test_required_fact_missing_refuses_no_receipt():
    result = _run(facts={"now": FACTS_VALID["now"], "facts": []})
    assert result.decision == "REFUSED"
    assert result.reason_code == FactBundleIncomplete.code
    assert result.receipt is None


def test_self_asserted_prohibited_refuses():
    facts = json.loads((FIXTURES / "runtime" / "facts_self_asserted_prohibited.json").read_text())
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == FactSelfAsserted.code
    assert result.receipt is None


def test_stale_fact_refuses():
    facts = json.loads((FIXTURES / "runtime" / "facts_stale.json").read_text())
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == FactStale.code
    assert result.receipt is None


def test_lossy_representation_refuses():
    facts = json.loads((FIXTURES / "runtime" / "facts_lossy_representation.json").read_text())
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == "RUN_FACT_REPRESENTATION"
    assert result.receipt is None


def test_future_timestamp_refuses():
    facts = json.loads((FIXTURES / "runtime" / "facts_future_timestamp.json").read_text())
    result = _run(facts=facts)
    assert result.decision == "REFUSED"
    assert result.reason_code == FactFutureTimestamp.code
    assert result.receipt is None


def test_unverifiable_naive_timestamp_refuses():
    facts = json.loads((FIXTURES / "runtime" / "facts_naive_timestamp.json").read_text())
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


# ------------------------------------------------------ B8 mutation matrix

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
    ("decision", "DENY"),
    ("execution_result", "NOT_EXECUTED"),  # valid label, but wrong for this receipt
])
def test_b8_single_field_mutation_is_detected(field, bad_value):
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
    mutated_facts["facts"][0]["evidence"] = mutated_facts["facts"][0]["evidence"]
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


def test_admission_only_mutation_does_not_change_receipt_digests():
    """Mirrors AC-016's own admission/proof-only-mutation invariant: since
    veip.py never reads admission/proof, an admission-only-changed artifact
    must still produce byte-identical receipt digests."""
    mutated_artifact = json.loads(json.dumps(ARTIFACT))
    mutated_artifact["admission"]["approvals"] = [{"approval_id": "approval:xyz", "approver": "ops-lead"}]
    r1 = _run()
    r2 = _run(artifact=mutated_artifact)
    assert r1.receipt["contract_digest"] == r2.receipt["contract_digest"]
    assert r1.receipt["projection_digest"] == r2.receipt["projection_digest"]
    assert r1.receipt["runtime_fact_set_digest"] == r2.receipt["runtime_fact_set_digest"]
    assert r1.receipt["exact_action_digest"] == r2.receipt["exact_action_digest"]
