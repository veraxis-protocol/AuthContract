"""AC-017 — repairs three independently established false-green paths in
AC-016 (candidate fd4e7dc10c17bc3b422e5f7cf9a2964cb9113f23), without
reopening the architecture:

  F1  check_action did not enforce activation_state == "ACTIVE"
  F2  unsupported declaration/action fields were silently ignored
  F3  enum membership was not type-safe (Python's True == 1, Decimal == int)

Test numbering below matches AC-017's own "Mandatory tests" numbering (1-17)
so the return record's expected/observed matrix can cite these directly.
"""

import json

import pytest

from authcontract.digest import contract_digest
from authcontract.projection import (
    ContractScopeConflict,
    InactiveContract,
    ProjectionDomainError,
    UnclassifiedAction,
    check_action,
    project,
    select_matching_projection,
)

CONTRACT = {
    "identity": {"contract_id": "ac:payments:us:ac017-specimen", "version": "0.2.1"},
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

VALID_ACTION = {
    "action_type": "send_payment",
    "parameters": {
        "beneficiary_account": "acct:1",
        "currency": "USD",
        "amount": "500.00",
        "secondary_approval_present": True,
    },
}


def _artifact(contract=CONTRACT, state="ACTIVE", activation_id="act:1", omit_state=False):
    digest = contract_digest(contract)
    activation = {"contract_digest": digest, "activation_id": activation_id}
    if not omit_state:
        activation["state"] = state
    return {
        "contract": contract,
        "admission": {"contract_digest": digest, "approvals": []},
        "activation": activation,
        "proof": {"contract_digest": digest},
    }


# ===================================================================
# F1 — check_action must enforce activation_state == "ACTIVE"
# ===================================================================

def test_01_active_projection_valid_action_passes():
    p = project(_artifact(state="ACTIVE"))
    validated = check_action(p, VALID_ACTION)
    assert set(validated) == {"beneficiary_account", "currency", "amount", "secondary_approval_present"}


def test_02_suspended_projection_same_action_is_refused():
    p = project(_artifact(state="SUSPENDED"))
    with pytest.raises(InactiveContract) as exc:
        check_action(p, VALID_ACTION)
    assert exc.value.code == "RUN_INACTIVE_CONTRACT"


def test_03_revoked_projection_same_action_is_refused():
    p = project(_artifact(state="REVOKED"))
    with pytest.raises(InactiveContract) as exc:
        check_action(p, VALID_ACTION)
    assert exc.value.code == "RUN_INACTIVE_CONTRACT"


def test_04_missing_activation_state_cannot_pass():
    p = project(_artifact(omit_state=True))
    assert p.activation_state is None
    with pytest.raises(InactiveContract):
        check_action(p, VALID_ACTION)


def test_04b_unrecognised_activation_state_cannot_pass():
    """Not just SUSPENDED/REVOKED specifically — any value other than the
    exact string "ACTIVE" refuses, including a typo or unknown state."""
    p = project(_artifact(state="PENDING_REVIEW"))
    with pytest.raises(InactiveContract):
        check_action(p, VALID_ACTION)


def test_05_select_matching_projection_inactive_candidate_behavior_unchanged():
    """F1 touches only check_action; select_matching_projection's existing
    ACTIVE-only filtering (already covered in test_projection.py) must
    still behave identically — a SUSPENDED-only candidate list is still
    UnclassifiedAction (out of scope), never ContractScopeConflict."""
    suspended = project(_artifact(state="SUSPENDED"))
    with pytest.raises(UnclassifiedAction):
        select_matching_projection([suspended], "send_payment")


def test_project_still_constructs_projections_for_inactive_contracts():
    """F1 explicitly permits project() to keep building SUSPENDED/REVOKED
    Projections for inspection/overlap — only check_action refuses."""
    p = project(_artifact(state="SUSPENDED"))
    assert p.activation_state == "SUSPENDED"


def test_check_action_cli_nonzero_on_suspended(tmp_path):
    """`authcontract check-action` against a SUSPENDED fixture returns
    non-zero REFUSED — exercised via the CLI layer, not just projection.py."""
    from authcontract.cli import check_action_cli

    fixture = tmp_path / "suspended.json"
    fixture.write_text(json.dumps(_artifact(state="SUSPENDED")))
    action = tmp_path / "action.json"
    action.write_text(json.dumps(VALID_ACTION))

    result, passed = check_action_cli(str(fixture), str(action))
    assert passed is False
    assert result["reason_code"] == "RUN_INACTIVE_CONTRACT"


# ===================================================================
# F2 — bounded schema: unknown fields at every level are refused
# ===================================================================

def test_06_unknown_projection_domain_field_is_refused():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["extra_field"] = "not allowed"
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_07_unknown_action_spec_field_is_refused():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["extra_field"] = "nope"
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_08_unknown_parameter_spec_field_is_refused():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["amount"]["extra_field"] = "nope"
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_09_non_boolean_required_is_refused():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["amount"]["required"] = "true"
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_09b_numeric_required_is_refused():
    """Not just strings — a truthy number must not be treated as valid
    boolean configuration either."""
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["amount"]["required"] = 1
    with pytest.raises(ProjectionDomainError):
        project(_artifact(bad))


def test_10_unknown_top_level_action_field_is_refused():
    p = project(_artifact())
    action = json.loads(json.dumps(VALID_ACTION))
    action["extra_field"] = "not allowed"
    with pytest.raises(ProjectionDomainError) as exc:
        check_action(p, action)
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_11_existing_valid_specimen_still_passes():
    p = project(_artifact())
    validated = check_action(p, VALID_ACTION)
    assert validated["currency"] == "USD"


# ===================================================================
# F3 — enum membership must be type-safe
# ===================================================================

def test_12_integer_enum_with_bool_member_is_malformed_domain():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["retry_count"] = {
        "value_type": "integer", "required": False, "enum": [True]
    }
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_13_boolean_enum_with_int_member_is_malformed_domain():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["secondary_approval_present"]["enum"] = [1]
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_14_string_enum_with_int_member_is_malformed_domain():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["currency"]["enum"] = [1]
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_15_decimal_enum_with_numeric_member_is_malformed_domain():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["amount"]["enum"] = [500]
    with pytest.raises(ProjectionDomainError) as exc:
        project(_artifact(bad))
    assert exc.value.code == "RUN_DOMAIN_ESCAPE"


def test_15b_decimal_enum_with_float_member_is_malformed_domain():
    bad = json.loads(json.dumps(CONTRACT))
    bad["projection_domain"]["actions"]["send_payment"]["parameters"]["amount"]["enum"] = [500.0]
    with pytest.raises(ProjectionDomainError):
        project(_artifact(bad))


def test_16_valid_string_enum_behaves_exactly():
    p = project(_artifact())
    validated = check_action(p, VALID_ACTION)
    assert validated["currency"] == "USD"

    rejected_action = json.loads(json.dumps(VALID_ACTION))
    rejected_action["parameters"]["currency"] = "GBP"
    with pytest.raises(ProjectionDomainError):
        check_action(p, rejected_action)


def test_17_integer_value_must_not_match_boolean_enum_true():
    """The decisive F3 regression: a boolean parameter declares enum=[True]
    (now valid under F3's type-checked enum). Supplying integer 1 must be
    refused — never silently accepted via True == 1."""
    contract = json.loads(json.dumps(CONTRACT))
    contract["projection_domain"]["actions"]["send_payment"]["parameters"]["secondary_approval_present"]["enum"] = [True]
    p = project(_artifact(contract))

    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["secondary_approval_present"] = 1
    with pytest.raises(ProjectionDomainError):
        check_action(p, action)


def test_17b_bool_value_must_not_match_integer_enum_one():
    """Symmetric regression: an integer parameter declares enum=[1]; a bool
    True (which Python treats as == 1) must not satisfy it."""
    contract = json.loads(json.dumps(CONTRACT))
    contract["projection_domain"]["actions"]["send_payment"]["parameters"]["retry_count"] = {
        "value_type": "integer", "required": False, "enum": [1]
    }
    p = project(_artifact(contract))

    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["retry_count"] = True
    with pytest.raises(ProjectionDomainError):
        check_action(p, action)


def test_17c_strict_type_equal_primitive_rejects_bool_int_collapse():
    """Unit-level regression on the comparison primitive itself, independent
    of the type gate in _check_value — locks the fix down even if check
    ordering is ever refactored."""
    from authcontract.projection import _strict_type_equal

    assert _strict_type_equal(1, True) is False
    assert _strict_type_equal(True, 1) is False
    assert _strict_type_equal(True, True) is True
    assert _strict_type_equal(1, 1) is True
    assert _strict_type_equal(0, False) is False


def test_decimal_enum_matches_across_equivalent_representations():
    """Positive control for the F3 decimal-enum fix: '500.00' and '500' are
    the same declared value at scale 2 and must still match — the fix must
    not become over-strict about representation, only about type."""
    contract = json.loads(json.dumps(CONTRACT))
    contract["projection_domain"]["actions"]["send_payment"]["parameters"]["amount"]["enum"] = ["500.00"]
    p = project(_artifact(contract))

    action = json.loads(json.dumps(VALID_ACTION))
    action["parameters"]["amount"] = "500.00"
    validated = check_action(p, action)
    assert str(validated["amount"]) == "500.00"
