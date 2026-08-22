"""R10 / AC-I15 — runtime fact provenance and admissibility."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from authcontract.facts import (
    AssertedFact,
    FactContract,
    FactRepresentation,
    FactSelfAsserted,
    FactStale,
    FactUnattested,
    admit,
)

NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
SUBJECT = "payment-agent"

APPROVAL = FactContract(
    fact_id="secondary_approval.present",
    value_type="boolean",
    issuer="TREASURY_APPROVAL_SERVICE",
    trust_basis="signed_approval_record",
    freshness=timedelta(minutes=15),
    assertion_path="ATTESTED_CHANNEL",
    self_assertion_policy="PROHIBITED",
    wire_representation="json_boolean",
)

AMOUNT = FactContract(
    fact_id="payment.amount",
    value_type="decimal(2)",
    issuer="LEDGER",
    trust_basis="ledger_record",
    freshness=timedelta(minutes=5),
    assertion_path="ATTESTED_CHANNEL",
    self_assertion_policy="PROHIBITED",
    wire_representation="decimal_string",
)


def _fact(contract, **over):
    base = dict(
        fact_id=contract.fact_id,
        raw_value=True,
        wire_representation=contract.wire_representation,
        issuer=contract.issuer,
        asserted_by="TREASURY_APPROVAL_SERVICE",
        asserted_at=NOW,
        assertion_path="ATTESTED_CHANNEL",
    )
    base.update(over)
    return AssertedFact(**base)


def test_valid_fact_is_admitted():
    assert admit(APPROVAL, _fact(APPROVAL), governed_subject=SUBJECT, now=NOW) is True


def test_governed_subject_cannot_satisfy_its_own_control():
    """The decisive attack: the agent asserts the fact that permits it."""
    forged = _fact(APPROVAL, asserted_by=SUBJECT)
    with pytest.raises(FactSelfAsserted) as exc:
        admit(APPROVAL, forged, governed_subject=SUBJECT, now=NOW)
    assert exc.value.code == "RUN_FACT_SELF_ASSERTED"


def test_wrong_issuer_is_rejected():
    with pytest.raises(FactUnattested):
        admit(APPROVAL, _fact(APPROVAL, issuer="SOMEONE_ELSE"),
              governed_subject=SUBJECT, now=NOW)


def test_stale_fact_is_rejected():
    old = _fact(APPROVAL, asserted_at=NOW - timedelta(minutes=16))
    with pytest.raises(FactStale):
        admit(APPROVAL, old, governed_subject=SUBJECT, now=NOW)


def test_fresh_boundary_is_admitted():
    edge = _fact(APPROVAL, asserted_at=NOW - timedelta(minutes=15))
    assert admit(APPROVAL, edge, governed_subject=SUBJECT, now=NOW) is True


def test_wrong_assertion_path_is_rejected():
    with pytest.raises(FactUnattested):
        admit(APPROVAL, _fact(APPROVAL, assertion_path="UNATTESTED"),
              governed_subject=SUBJECT, now=NOW)


def test_float_ingestion_is_rejected():
    """R02 residue. The hazard is NOT in Rego — OPA v1.19.1 preserves
    json.Number and showed 0/5 divergences. It is a host decoder that
    flattens decimal(2) to float before the engine ever sees it."""
    flattened = _fact(AMOUNT, raw_value=50000.0000000000001,
                      asserted_by="LEDGER", issuer="LEDGER")
    with pytest.raises(FactRepresentation) as exc:
        admit(AMOUNT, flattened, governed_subject=SUBJECT, now=NOW)
    assert exc.value.code == "RUN_FACT_REPRESENTATION"
    assert "flattened" in str(exc.value)


def test_decimal_string_is_admitted_losslessly():
    good = _fact(AMOUNT, raw_value="50000.01", asserted_by="LEDGER", issuer="LEDGER")
    assert admit(AMOUNT, good, governed_subject=SUBJECT, now=NOW) == Decimal("50000.01")


def test_scale_overflow_is_rejected():
    over = _fact(AMOUNT, raw_value="50000.001", asserted_by="LEDGER", issuer="LEDGER")
    with pytest.raises(FactRepresentation):
        admit(AMOUNT, over, governed_subject=SUBJECT, now=NOW)


def test_corroboration_collusion_is_rejected():
    contract = FactContract(
        **{**APPROVAL.__dict__, "self_assertion_policy": "PERMITTED_WITH_CORROBORATION"}
    )
    colluding = _fact(contract, asserted_by=SUBJECT, corroborated_by=SUBJECT)
    with pytest.raises(FactUnattested) as exc:
        admit(contract, colluding, governed_subject=SUBJECT, now=NOW)
    assert "collusion" in str(exc.value)


def test_self_assertion_without_corroboration_is_rejected():
    contract = FactContract(
        **{**APPROVAL.__dict__, "self_assertion_policy": "PERMITTED_WITH_CORROBORATION"}
    )
    with pytest.raises(FactUnattested):
        admit(contract, _fact(contract, asserted_by=SUBJECT),
              governed_subject=SUBJECT, now=NOW)


def test_self_assertion_with_independent_corroboration_is_admitted():
    contract = FactContract(
        **{**APPROVAL.__dict__, "self_assertion_policy": "PERMITTED_WITH_CORROBORATION"}
    )
    ok = _fact(contract, asserted_by=SUBJECT, corroborated_by="TREASURY_APPROVAL_SERVICE")
    assert admit(contract, ok, governed_subject=SUBJECT, now=NOW) is True
