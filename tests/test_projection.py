"""AC-016 — machine-checkable projection domain + closed mediated-action
universe. Layered on top of R01/AC-I06; does not touch AC-I15 (facts.py)."""

import json
import pytest

from authcontract.digest import ContractDigestMismatch, DigestScopeError, contract_digest
from authcontract.projection import (
    ContractScopeConflict,
    Projection,
    ProjectionDomainError,
    UnclassifiedAction,
    check_action,
    project,
    projection_digest,
    select_matching_projection,
)

CONTRACT = {
    "identity": {"contract_id": "ac:payments:us:test-specimen", "version": "0.2.1"},
    "subject": {"system": "payment-agent", "mediated_actions": ["send_payment"]},
    "projection_domain": {
        "actions": {
            "send_payment": {
                "parameters": {
                    "beneficiary_account": {"value_type": "string", "required": True},
                    "currency": {"value_type": "string", "required": True, "enum": ["USD", "EUR"]},
                    "amount": {"value_type": "decimal(2)", "required": True},
                    "secondary_approval_present": {"value_type": "boolean", "required": True},
                }
            }
        }
    },
}


def _artifact(contract=CONTRACT, state="ACTIVE", activation_id="act:1"):
    digest = contract_digest(contract)
    return {
        "contract": contract,
        "admission": {"contract_digest": digest, "approvals": []},
        "activation": {"contract_digest": digest, "activation_id": activation_id, "state": state},
        "proof": {"contract_digest": digest},
    }


VALID_ACTION = {
    "action_type": "send_payment",
    "parameters": {
        "beneficiary_account": "acct:1",
        "currency": "USD",
        "amount": "500.00",
        "secondary_approval_present": True,
    },
}


# --------------------------------------------------------------- projection

def test_project_is_deterministic():
    artifact = _artifact()
    p1 = project(artifact)
    p2 = project(json.loads(json.dumps(artifact)))  # fresh dict, same content
    assert p1 == p2


def test_projection_digest_is_stable():
    p = project(_artifact())
    assert projection_digest(p) == projection_digest(p)


def test_projection_binds_contract_digest_and_activation_identity():
    artifact = _artifact()
    p = project(artifact)
    assert p.contract_digest == contract_digest(CONTRACT)
    assert p.activation_state == "ACTIVE"
    assert p.activation_id == "act:1"


def test_contract_mutation_changes_projection_digest():
    mutated = json.loads(json.dumps(CONTRACT))
    mutated["identity"]["version"] = "0.2.2"
    p1 = project(_artifact(CONTRACT))
    p2 = project(_artifact(mutated))
    assert p1.contract_digest != p2.contract_digest
    assert projection_digest(p1) != projection_digest(p2)


def test_admission_only_mutation_does_not_change_projection_digest():
    a1 = _artifact()
    a2 = _artifact()
    a2["admission"]["approvals"] = [{"approval_id": "approval:xyz", "approver": "ops-lead"}]
    p1 = project(a1)
    p2 = project(a2)
    assert p1.contract_digest == p2.contract_digest
    assert projection_digest(p1) == projection_digest(p2)


def test_proof_only_mutation_does_not_change_projection_digest():
    a1 = _artifact()
    a2 = _artifact()
    a2["proof"] = {"contract_digest": a2["proof"]["contract_digest"], "note": "reviewed twice"}
    assert projection_digest(project(a1)) == projection_digest(project(a2))


def test_missing_projection_domain_is_domain_escape():
    bare_contract = {"identity": {"contract_id": "ac:no-domain", "version": "0.2.1"}}
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bare_contract))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_malformed_domain_unsupported_value_type_is_rejected():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["amount"]["value_type"] = "protobuf_blob"
    with pytest.raises(ProjectionDomainError):
        project(_artifact(bad))


def test_malformed_domain_actions_not_object_is_rejected():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"] = "not-an-object"
    with pytest.raises(ProjectionDomainError):
        project(_artifact(bad))


def test_digest_scope_violation_still_propagates_through_project():
    """project() must not swallow/reinterpret R01 refusals — it layers on
    top of verify_artifact, never around it."""
    defective = json.loads(json.dumps(CONTRACT))
    defective["approvals"] = [{"approval_id": "a", "reviewed_payload_digest": "sha256:aa"}]
    with pytest.raises(DigestScopeError):
        project(_artifact(defective))


def test_sibling_digest_mismatch_still_propagates_through_project():
    artifact = _artifact()
    artifact["admission"]["contract_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ContractDigestMismatch):
        project(artifact)


# ------------------------------------------------------- closed action universe

def test_valid_action_is_accepted():
    p = project(_artifact())
    validated = check_action(p, VALID_ACTION)
    assert set(validated) == {"beneficiary_account", "currency", "amount", "secondary_approval_present"}


def test_unknown_action_type_is_unclassified():
    p = project(_artifact())
    action = dict(VALID_ACTION, action_type="issue_refund")
    with pytest.raises(UnclassifiedAction) as exc:
        check_action(p, action)
    assert exc.value.code == "RUN_UNCLASSIFIED_ACTION"


def test_unknown_parameter_is_domain_escape():
    p = project(_artifact())
    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["memo"] = "not declared"
    with pytest.raises(ProjectionDomainError) as exc:
        check_action(p, action)
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_missing_required_parameter_is_domain_escape():
    p = project(_artifact())
    action = json.loads(json.dumps(VALID_ACTION))
    del action["parameters"]["currency"]
    with pytest.raises(ProjectionDomainError):
        check_action(p, action)


def test_optional_parameter_may_be_omitted():
    contract = json.loads(json.dumps(CONTRACT))
    contract["projection_domain"]["actions"]["send_payment"]["parameters"]["memo"] = {
        "value_type": "string", "required": False
    }
    p = project(_artifact(contract))
    validated = check_action(p, VALID_ACTION)
    assert "memo" not in validated


def test_float_for_decimal_is_rejected_before_decision_evaluation():
    """R02-style hazard, mirrored at the action-parameter boundary."""
    p = project(_artifact())
    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["amount"] = 500.0000000000001
    with pytest.raises(ProjectionDomainError) as exc:
        check_action(p, action)
    assert "decimal string" in str(exc.value)


def test_decimal_scale_overflow_is_rejected():
    p = project(_artifact())
    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["amount"] = "500.001"
    with pytest.raises(ProjectionDomainError):
        check_action(p, action)


def test_bool_is_not_an_integer_parameter():
    contract = json.loads(json.dumps(CONTRACT))
    contract["projection_domain"]["actions"]["send_payment"]["parameters"]["retry_count"] = {
        "value_type": "integer", "required": False
    }
    p = project(_artifact(contract))
    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["retry_count"] = True
    with pytest.raises(ProjectionDomainError):
        check_action(p, action)


def test_out_of_enum_value_is_rejected():
    p = project(_artifact())
    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["currency"] = "GBP"
    with pytest.raises(ProjectionDomainError):
        check_action(p, action)


def test_non_object_parameters_is_rejected():
    p = project(_artifact())
    action = {"action_type": "send_payment", "parameters": "not-an-object"}
    with pytest.raises(ProjectionDomainError):
        check_action(p, action)


# ------------------------------------------------ overlapping ACTIVE contracts

CONTRACT_B = {
    "identity": {"contract_id": "ac:payments:us:test-specimen-b", "version": "0.2.1"},
    "subject": {"system": "refund-agent", "mediated_actions": ["send_payment"]},
    "projection_domain": CONTRACT["projection_domain"],
}


def test_one_active_match_proceeds():
    p = project(_artifact())
    result = select_matching_projection([p], "send_payment")
    assert result is p


def test_zero_matches_is_unclassified():
    p = project(_artifact())
    with pytest.raises(UnclassifiedAction) as exc:
        select_matching_projection([p], "issue_refund")
    assert exc.value.code == "RUN_UNCLASSIFIED_ACTION"


def test_empty_candidate_list_is_unclassified():
    with pytest.raises(UnclassifiedAction):
        select_matching_projection([], "send_payment")


def test_two_overlapping_active_matches_is_scope_conflict():
    p1 = project(_artifact(CONTRACT))
    p2 = project(_artifact(CONTRACT_B))
    with pytest.raises(ContractScopeConflict) as exc:
        select_matching_projection([p1, p2], "send_payment")
    assert exc.value.code == "CONTRACT_SCOPE_CONFLICT"


def test_conflict_is_order_independent():
    """No implicit first-match: the conflict fires regardless of list order."""
    p1 = project(_artifact(CONTRACT))
    p2 = project(_artifact(CONTRACT_B))
    with pytest.raises(ContractScopeConflict):
        select_matching_projection([p1, p2], "send_payment")
    with pytest.raises(ContractScopeConflict):
        select_matching_projection([p2, p1], "send_payment")


def test_suspended_candidate_does_not_count_as_active_match():
    active = project(_artifact(CONTRACT, state="ACTIVE"))
    suspended = project(_artifact(CONTRACT_B, state="SUSPENDED"))
    # Only one ACTIVE candidate declares the action -> proceeds, not a conflict.
    result = select_matching_projection([active, suspended], "send_payment")
    assert result is active


def test_revoked_candidate_does_not_count_as_active_match():
    revoked = project(_artifact(CONTRACT, state="REVOKED"))
    with pytest.raises(UnclassifiedAction):
        select_matching_projection([revoked], "send_payment")


def test_all_candidates_inactive_is_unclassified_not_conflict():
    suspended1 = project(_artifact(CONTRACT, state="SUSPENDED"))
    suspended2 = project(_artifact(CONTRACT_B, state="SUSPENDED"))
    with pytest.raises(UnclassifiedAction):
        select_matching_projection([suspended1, suspended2], "send_payment")
