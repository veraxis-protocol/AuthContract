"""R01 / AC-I06 — digest acyclicity and cross-object binding."""

import pytest

from authcontract.digest import (
    ContractDigestMismatch,
    DigestScopeError,
    contract_digest,
    verify_artifact,
)

CONTRACT = {
    "identity": {"contract_id": "ac:payments:us:specimen-1", "version": "0.2.1"},
    "subject": {"system": "payment-agent", "mediated_actions": ["send_payment"]},
    "controls": [{"control_id": "PAY-APPROVAL-017", "kind": "REQUIRE"}],
}


def test_digest_is_deterministic():
    assert contract_digest(CONTRACT) == contract_digest(dict(CONTRACT))


def test_digest_is_key_order_independent():
    reordered = {k: CONTRACT[k] for k in reversed(list(CONTRACT))}
    assert contract_digest(reordered) == contract_digest(CONTRACT)


def test_v01_defect_is_rejected():
    """The exact v0.1 structure: approvals inside the hashed object,
    carrying a digest of the object that contains them."""
    defective = dict(CONTRACT)
    defective["approvals"] = [
        {"approval_id": "approval:001", "reviewed_payload_digest": "sha256:..."}
    ]
    with pytest.raises(DigestScopeError) as exc:
        contract_digest(defective)
    assert exc.value.code == "AC_DIGEST_SCOPE"


def test_sibling_objects_rejected_inside_contract():
    for sibling in ("admission", "activation", "derivations", "proof"):
        bad = dict(CONTRACT)
        bad[sibling] = {"contract_digest": "sha256:..."}
        with pytest.raises(DigestScopeError):
            contract_digest(bad)


def test_nested_self_reference_is_rejected():
    """Depth must not defeat the check."""
    bad = dict(CONTRACT)
    bad["lineage"] = {"history": [{"record": {"contract_digest": "sha256:..."}}]}
    with pytest.raises(DigestScopeError):
        contract_digest(bad)


def test_source_anchor_digests_are_permitted():
    """source_digest/anchor_digest reference OTHER artifacts — not self."""
    ok = dict(CONTRACT)
    ok["sources"] = [{"source_id": "src:treasury:v12", "source_digest": "sha256:ab"}]
    assert contract_digest(ok).startswith("sha256:")


def test_valid_artifact_verifies():
    digest = contract_digest(CONTRACT)
    artifact = {
        "contract": CONTRACT,
        "admission": {"contract_digest": digest, "approvals": []},
        "activation": {"contract_digest": digest, "state": "ACTIVE"},
        "proof": {"contract_digest": digest},
    }
    assert verify_artifact(artifact) == digest


def test_cross_object_substitution_is_rejected():
    """AC-A22: valid admission paired with a different contract."""
    other = dict(CONTRACT)
    other["identity"] = {"contract_id": "ac:other", "version": "0.2.1"}
    artifact = {
        "contract": other,
        "admission": {"contract_digest": contract_digest(CONTRACT)},
    }
    with pytest.raises(ContractDigestMismatch) as exc:
        verify_artifact(artifact)
    assert exc.value.code == "AC_DIGEST"


def test_sibling_without_binding_is_rejected():
    artifact = {"contract": CONTRACT, "admission": {"approvals": []}}
    with pytest.raises(ContractDigestMismatch):
        verify_artifact(artifact)
