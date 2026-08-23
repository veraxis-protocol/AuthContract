"""R10 / AC-I15 — runtime fact provenance and admissibility.

Covers the AC-008 baseline, the five AC-009 blocking findings:
  1. asserted fact_id vs FactContract
  2. trust_basis carried and verified
  3. unknown self_assertion_policy fails closed
  4. unsupported value_type fails closed
  5. corroboration_required is operative

...and the two AC-012 bounded fixes:
  6. trusted evidence binding — issuer/trust_basis/assertion_path/
     corroborator identity are decided against VerifiedEvidence, never
     against the asserting party's own claimed fields
  7. time validation — future timestamps fail closed; exactly-now and the
     stale boundary remain valid; naive/aware mismatch is an explicit
     refusal, not an uncontrolled exception
"""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from authcontract.facts import (
    AssertedFact,
    FactContract,
    FactContractInvalid,
    FactCorroborationMissing,
    FactEvidenceMismatch,
    FactFutureTimestamp,
    FactIdentityMismatch,
    FactRepresentation,
    FactSelfAsserted,
    FactStale,
    FactTimeUnverifiable,
    FactTrustBasisMismatch,
    FactTypeUnsupported,
    FactUnattested,
    VerifiedEvidence,
    admit,
)

NOW = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
SUBJECT = "payment-agent"
ISSUER = "TREASURY_APPROVAL_SERVICE"

APPROVAL = FactContract(
    fact_id="secondary_approval.present",
    value_type="boolean",
    issuer=ISSUER,
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
        trust_basis=contract.trust_basis,
        asserted_by=contract.issuer,
        asserted_at=NOW,
        assertion_path=contract.assertion_path,
    )
    base.update(over)
    return AssertedFact(**base)


def _evidence(contract, fact=None, **over):
    """Verifier-established evidence, defaulting to what `contract` requires.

    AC-020 extended `VerifiedEvidence` to also bind fact identity/value/
    asserted_by/asserted_at — `admit()` now requires these to agree with the
    caller's `AssertedFact` claim. For those four fields, this helper
    defaults to AGREEING with `fact` when one is supplied (mirroring how a
    genuine verifier would independently confirm what was actually
    asserted), or to the same contract-derived defaults `_fact()` itself
    uses otherwise. Callers who want to test a claim/verification MISMATCH
    override the relevant field(s) explicitly via `**over` — that
    independence is the point, unchanged from AC-012.
    """
    if fact is not None:
        default_fact_id = fact.fact_id
        default_value = fact.raw_value
        default_asserted_by = fact.asserted_by
        default_asserted_at = fact.asserted_at
    else:
        default_fact_id = contract.fact_id
        default_value = True
        default_asserted_by = contract.issuer
        default_asserted_at = NOW
    base = dict(
        fact_id=default_fact_id,
        value=default_value,
        asserted_by=default_asserted_by,
        asserted_at=default_asserted_at,
        issuer=contract.issuer,
        trust_basis=contract.trust_basis,
        assertion_path=contract.assertion_path,
        corroborated_by=None,
    )
    base.update(over)
    return VerifiedEvidence(**base)


def _admit(contract, fact, evidence=None, *, now=NOW):
    if evidence is None:
        # Auto-derive evidence that AGREES with the exact `fact` passed in —
        # any test that overrides `_fact(...)`'s value/asserted_by/asserted_at
        # continues to exercise the check it originally targeted (staleness,
        # self-assertion, etc.) rather than tripping the new AC-020 A2
        # claim/verification agreement check instead.
        evidence = _evidence(contract, fact)
    return admit(contract, fact, evidence=evidence, governed_subject=SUBJECT, now=now)


# ---------------------------------------------------------------- baseline

def test_valid_fact_is_admitted():
    assert _admit(APPROVAL, _fact(APPROVAL)) is True


def test_governed_subject_cannot_satisfy_its_own_control():
    """The decisive attack: the agent asserts the fact that permits it."""
    with pytest.raises(FactSelfAsserted) as exc:
        _admit(APPROVAL, _fact(APPROVAL, asserted_by=SUBJECT))
    assert exc.value.code == "RUN_FACT_SELF_ASSERTED"


def test_wrong_issuer_is_rejected():
    """Issuer identity is decided against verified evidence, not the claim."""
    with pytest.raises(FactUnattested):
        _admit(APPROVAL, _fact(APPROVAL), _evidence(APPROVAL, issuer="SOMEONE_ELSE"))


def test_stale_fact_is_rejected():
    with pytest.raises(FactStale):
        _admit(APPROVAL, _fact(APPROVAL, asserted_at=NOW - timedelta(minutes=16)))


def test_fresh_boundary_is_admitted():
    assert _admit(APPROVAL, _fact(APPROVAL, asserted_at=NOW - timedelta(minutes=15))) is True


def test_wrong_assertion_path_is_rejected():
    with pytest.raises(FactUnattested):
        _admit(APPROVAL, _fact(APPROVAL), _evidence(APPROVAL, assertion_path="UNATTESTED"))


def test_float_ingestion_is_rejected():
    """R02 residue. The hazard is NOT in Rego — OPA v1.19.1 preserves
    json.Number and showed 0/5 divergences. It is a host decoder that
    flattens decimal(2) to float before the engine ever sees it."""
    flattened = _fact(AMOUNT, raw_value=50000.0000000000001)
    with pytest.raises(FactRepresentation) as exc:
        _admit(AMOUNT, flattened)
    assert exc.value.code == "RUN_FACT_REPRESENTATION"
    assert "flattened" in str(exc.value)


def test_decimal_string_is_admitted_losslessly():
    assert _admit(AMOUNT, _fact(AMOUNT, raw_value="50000.01")) == Decimal("50000.01")


def test_scale_overflow_is_rejected():
    with pytest.raises(FactRepresentation):
        _admit(AMOUNT, _fact(AMOUNT, raw_value="50000.001"))


# ------------------------------------------- AC-009 #1: fact_id verification

def test_fact_id_mismatch_is_rejected():
    """A fact for a different control must not satisfy this contract."""
    wrong = _fact(APPROVAL, fact_id="some.other.fact")
    with pytest.raises(FactIdentityMismatch) as exc:
        _admit(APPROVAL, wrong)
    assert exc.value.code == "RUN_FACT_IDENTITY_MISMATCH"


def test_fact_id_substitution_attack_is_rejected():
    """Hostile: a genuine, fresh, correctly-issued fact — for the wrong control."""
    smuggled = _fact(APPROVAL, fact_id="unrelated.but.true.flag", raw_value=True)
    with pytest.raises(FactIdentityMismatch):
        _admit(APPROVAL, smuggled)


# ------------------------------------------- AC-009 #2: trust_basis verified

def test_wrong_trust_basis_is_rejected():
    with pytest.raises(FactTrustBasisMismatch) as exc:
        _admit(APPROVAL, _fact(APPROVAL), _evidence(APPROVAL, trust_basis="self_declared"))
    assert exc.value.code == "RUN_FACT_TRUST_BASIS"


def test_empty_trust_basis_is_rejected():
    with pytest.raises(FactTrustBasisMismatch):
        _admit(APPROVAL, _fact(APPROVAL), _evidence(APPROVAL, trust_basis=""))


def test_correct_trust_basis_is_admitted():
    assert _admit(APPROVAL, _fact(APPROVAL), _evidence(APPROVAL, trust_basis="signed_approval_record")) is True


# --------------------------------- AC-009 #3: unknown policy fails CLOSED

def test_unknown_self_assertion_policy_fails_closed():
    """A typo in the contract must not silently permit self-assertion."""
    typo = replace(APPROVAL, self_assertion_policy="PROHIBITTED")
    with pytest.raises(FactContractInvalid) as exc:
        _admit(typo, _fact(typo, asserted_by=SUBJECT))
    assert exc.value.code == "RUN_FACT_CONTRACT_INVALID"


def test_unknown_policy_fails_closed_even_for_third_party_assertion():
    """Fails closed regardless of who asserted — the contract itself is broken."""
    bad = replace(APPROVAL, self_assertion_policy="ALLOW_ALL")
    with pytest.raises(FactContractInvalid):
        _admit(bad, _fact(bad))


def test_empty_policy_fails_closed():
    with pytest.raises(FactContractInvalid):
        _admit(replace(APPROVAL, self_assertion_policy=""), _fact(APPROVAL))


def test_permitted_policy_allows_self_assertion():
    """PERMITTED is a known policy and must still work."""
    permissive = replace(APPROVAL, self_assertion_policy="PERMITTED")
    assert _admit(permissive, _fact(permissive, asserted_by=SUBJECT)) is True


# ------------------------------- AC-009 #4: unsupported type fails CLOSED

def test_unsupported_value_type_fails_closed():
    """An unvalidatable type must be refused, not passed through raw."""
    exotic = replace(APPROVAL, value_type="protobuf_blob")
    with pytest.raises(FactTypeUnsupported) as exc:
        _admit(exotic, _fact(exotic, raw_value=object()))
    assert exc.value.code == "RUN_FACT_TYPE_UNSUPPORTED"


def test_malformed_decimal_type_fails_closed():
    with pytest.raises(FactTypeUnsupported):
        _admit(replace(AMOUNT, value_type="decimal()"), _fact(AMOUNT, raw_value="1.00"))


def test_instant_type_not_yet_supported_fails_closed():
    """`instant` is declared in the spec but not implemented here.
    It must refuse rather than admit unchecked."""
    with pytest.raises(FactTypeUnsupported):
        _admit(replace(APPROVAL, value_type="instant"), _fact(APPROVAL, raw_value="x"))


def test_integer_type_is_supported():
    c = replace(APPROVAL, value_type="integer", wire_representation="json_integer")
    assert _admit(c, _fact(c, raw_value=42)) == 42


def test_bool_is_not_an_integer():
    """bool subclasses int in Python; it must not satisfy `integer`."""
    c = replace(APPROVAL, value_type="integer", wire_representation="json_integer")
    with pytest.raises(FactRepresentation):
        _admit(c, _fact(c, raw_value=True))


def test_bool_is_not_a_decimal():
    with pytest.raises(FactRepresentation):
        _admit(AMOUNT, _fact(AMOUNT, raw_value=True))


def test_string_type_is_supported():
    c = replace(APPROVAL, value_type="string", wire_representation="json_string")
    assert _admit(c, _fact(c, raw_value="ok")) == "ok"


def test_non_finite_decimal_is_rejected():
    with pytest.raises(FactRepresentation):
        _admit(AMOUNT, _fact(AMOUNT, raw_value="NaN"))


# --------------------------- AC-009 #5: corroboration_required operative

def test_corroboration_required_without_corroborator_is_rejected():
    """Third-party assertion, but the contract demands corroboration."""
    c = replace(APPROVAL, corroboration_required=True)
    with pytest.raises(FactCorroborationMissing) as exc:
        _admit(c, _fact(c))
    assert exc.value.code == "RUN_FACT_CORROBORATION_MISSING"


def test_corroboration_required_with_independent_corroborator_is_admitted():
    c = replace(APPROVAL, corroboration_required=True)
    assert _admit(c, _fact(c), _evidence(c, corroborated_by="INTERNAL_AUDIT")) is True


def test_corroboration_by_the_asserter_is_not_independent():
    """Self-corroboration is not corroboration."""
    c = replace(APPROVAL, corroboration_required=True)
    with pytest.raises(FactCorroborationMissing) as exc:
        _admit(c, _fact(c), _evidence(c, corroborated_by=ISSUER))
    assert "not independent" in str(exc.value)


def test_corroboration_by_governed_subject_is_collusion():
    c = replace(APPROVAL, corroboration_required=True)
    with pytest.raises(FactCorroborationMissing) as exc:
        _admit(c, _fact(c), _evidence(c, corroborated_by=SUBJECT))
    assert "collusion" in str(exc.value)


# ---------------------- self-assertion + corroboration interaction

def test_corroboration_collusion_is_rejected():
    c = replace(APPROVAL, self_assertion_policy="PERMITTED_WITH_CORROBORATION")
    # asserted_by=SUBJECT must also be verified (AC-020 A2/A3) for this to
    # exercise genuine self-assertion collusion rather than a bare mismatch.
    with pytest.raises(FactCorroborationMissing) as exc:
        _admit(
            c,
            _fact(c, asserted_by=SUBJECT),
            _evidence(c, asserted_by=SUBJECT, corroborated_by=SUBJECT),
        )
    assert exc.value.code == "RUN_FACT_CORROBORATION_MISSING"


def test_self_assertion_without_corroboration_is_rejected():
    c = replace(APPROVAL, self_assertion_policy="PERMITTED_WITH_CORROBORATION")
    with pytest.raises(FactCorroborationMissing):
        _admit(c, _fact(c, asserted_by=SUBJECT))


def test_self_assertion_with_independent_corroboration_is_admitted():
    c = replace(APPROVAL, self_assertion_policy="PERMITTED_WITH_CORROBORATION")
    # asserted_by=SUBJECT must also be verified (AC-020 A2/A3) — otherwise
    # this would trip the new claim/verification mismatch check instead.
    assert _admit(
        c,
        _fact(c, asserted_by=SUBJECT),
        _evidence(c, asserted_by=SUBJECT, corroborated_by=ISSUER),
    ) is True


def test_both_gates_apply_together():
    """PERMITTED self-assertion still cannot bypass corroboration_required."""
    c = replace(APPROVAL, self_assertion_policy="PERMITTED", corroboration_required=True)
    with pytest.raises(FactCorroborationMissing):
        _admit(c, _fact(c, asserted_by=SUBJECT))


# ------------------------------------------------ check-order guarantees

def test_contract_validity_precedes_fact_checks():
    """A broken contract is refused even when the fact is also wrong."""
    broken = replace(APPROVAL, self_assertion_policy="NONSENSE")
    with pytest.raises(FactContractInvalid):
        _admit(broken, _fact(broken, fact_id="wrong", issuer="wrong"))


def test_identity_precedes_representation():
    """Wrong fact_id is reported as identity, not representation."""
    with pytest.raises(FactIdentityMismatch):
        _admit(AMOUNT, _fact(AMOUNT, fact_id="other", raw_value=1.5))


# ------------------------------------------- AC-012 #1: trusted evidence binding

def test_claimed_issuer_alone_does_not_establish_issuer_identity():
    """The decisive AC-012 attack: fact.issuer is correct on its face, but
    nothing verified it — evidence disagrees, and evidence must win."""
    fact = _fact(APPROVAL, issuer=ISSUER)  # caller's own claim: correct-looking
    evidence = _evidence(APPROVAL, issuer="SOMEONE_ELSE")  # verifier disagrees
    with pytest.raises(FactUnattested):
        _admit(APPROVAL, fact, evidence)


def test_claimed_trust_basis_alone_does_not_establish_trust_basis():
    fact = _fact(APPROVAL, trust_basis="signed_approval_record")
    evidence = _evidence(APPROVAL, trust_basis="self_declared")
    with pytest.raises(FactTrustBasisMismatch):
        _admit(APPROVAL, fact, evidence)


def test_claimed_assertion_path_alone_does_not_establish_assertion_path():
    fact = _fact(APPROVAL, assertion_path="ATTESTED_CHANNEL")
    evidence = _evidence(APPROVAL, assertion_path="UNATTESTED")
    with pytest.raises(FactUnattested):
        _admit(APPROVAL, fact, evidence)


def test_claimed_corroborator_alone_does_not_establish_corroborator_identity():
    """Fact claims a plausible independent corroborator; verifier found none."""
    c = replace(APPROVAL, corroboration_required=True)
    fact = _fact(c, corroborated_by="INTERNAL_AUDIT")
    evidence = _evidence(c, corroborated_by=None)
    with pytest.raises(FactCorroborationMissing):
        _admit(c, fact, evidence)


def test_verified_evidence_matching_contract_is_admitted():
    """Positive path: evidence genuinely establishes what the contract requires."""
    assert _admit(APPROVAL, _fact(APPROVAL), _evidence(APPROVAL)) is True


# ------------------------------------------- AC-012 #2: time validation

def test_future_timestamp_fails_closed():
    fact = _fact(APPROVAL, asserted_at=NOW + timedelta(seconds=1))
    with pytest.raises(FactFutureTimestamp) as exc:
        _admit(APPROVAL, fact)
    assert exc.value.code == "RUN_FACT_FUTURE_TIMESTAMP"


def test_far_future_timestamp_fails_closed():
    fact = _fact(APPROVAL, asserted_at=NOW + timedelta(days=1))
    with pytest.raises(FactFutureTimestamp):
        _admit(APPROVAL, fact)


def test_exactly_now_remains_valid():
    assert _admit(APPROVAL, _fact(APPROVAL, asserted_at=NOW)) is True


def test_one_second_past_freshness_boundary_is_rejected():
    """Mutation check: boundary must be `>`, not `>=` — one second past must fail."""
    with pytest.raises(FactStale):
        _admit(APPROVAL, _fact(APPROVAL, asserted_at=NOW - timedelta(minutes=15, seconds=1)))


def test_one_second_before_freshness_boundary_is_admitted():
    """Mutation check: boundary must not be stricter than declared freshness."""
    assert _admit(APPROVAL, _fact(APPROVAL, asserted_at=NOW - timedelta(minutes=14, seconds=59))) is True


def test_naive_asserted_at_against_aware_now_is_explicit_refusal():
    """A naive/aware mismatch must return a named refusal, not raise TypeError."""
    naive_fact = _fact(APPROVAL, asserted_at=datetime(2026, 8, 22, 12, 0))
    with pytest.raises(FactTimeUnverifiable) as exc:
        _admit(APPROVAL, naive_fact)
    assert exc.value.code == "RUN_FACT_TIME_UNVERIFIABLE"


def test_naive_now_against_aware_asserted_at_is_explicit_refusal():
    """Same mismatch, the other direction — `now` itself supplied naive."""
    aware_fact = _fact(APPROVAL, asserted_at=NOW)
    naive_now = datetime(2026, 8, 22, 12, 0)
    with pytest.raises(FactTimeUnverifiable):
        _admit(APPROVAL, aware_fact, now=naive_now)


def test_future_check_precedes_staleness_check():
    """A timestamp cannot be simultaneously reported as both; future wins
    because it is checked first and staleness cannot apply to a negative age."""
    fact = _fact(APPROVAL, asserted_at=NOW + timedelta(hours=1))
    with pytest.raises(FactFutureTimestamp):
        _admit(APPROVAL, fact)


# ------------------------------------------- AC-020 A1-A6: verified assertion binding
#
# F1: `admit()` previously used AssertedFact's own CLAIMED raw_value/
# asserted_at/asserted_by/fact_id as the operative semantics, even though
# VerifiedEvidence never bound any of them. These tests exercise the repair
# directly at the facts.py boundary (test_veip.py/test_cli_veip.py exercise
# the same defect at the orchestration/CLI level against the banking
# specimen). Each constructs `fact` and `evidence` INDEPENDENTLY and
# deliberately mismatched — auto-derivation via `_admit`'s default evidence
# is bypassed on purpose here, since the whole point is disagreement.

def test_verified_value_false_beats_claimed_value_true():
    """D2 (facts.py level): verifier says false; caller claims true."""
    fact = _fact(APPROVAL, raw_value=True)
    evidence = _evidence(APPROVAL, fact, value=False)
    with pytest.raises(FactEvidenceMismatch) as exc:
        _admit(APPROVAL, fact, evidence)
    assert exc.value.code == "RUN_FACT_EVIDENCE_MISMATCH"


def test_admitted_value_is_the_verified_value_not_the_claim():
    """A5: even when they compare equal, the returned value is bound to
    `evidence`'s exact representation, not merely passed through from
    `fact` — proven via two decimal strings that are numerically equal but
    carry a different internal (trailing-zero) representation, both within
    the contract's declared scale."""
    fact = _fact(AMOUNT, raw_value="50000.1")
    evidence = _evidence(AMOUNT, fact, value="50000.10")
    result = _admit(AMOUNT, fact, evidence)
    assert result == Decimal("50000.10")
    assert result.as_tuple() == Decimal("50000.10").as_tuple()
    assert result.as_tuple() != Decimal("50000.1").as_tuple()


def test_verified_asserted_by_disagreeing_with_claim_is_rejected():
    """D1 (facts.py level): the TRUE verified asserter is the governed
    subject, but the caller claims a third party asserted it — caught by
    the claim/verification agreement check (A2) before self-assertion
    policy is even evaluated; the true asserter being the governed subject
    means self-assertion detection (A3) would independently also refuse
    this scenario if the mismatch check were somehow bypassed."""
    fact = _fact(APPROVAL, asserted_by=ISSUER)  # caller claims a third party
    evidence = _evidence(APPROVAL, fact, asserted_by=SUBJECT)  # verifier: it was the governed subject
    with pytest.raises(FactEvidenceMismatch) as exc:
        _admit(APPROVAL, fact, evidence)
    assert exc.value.code == "RUN_FACT_EVIDENCE_MISMATCH"


def test_verified_stale_time_beats_claimed_fresh_time():
    """D3 (facts.py level): verifier's assertion time is stale; caller
    claims a fresh one. Caught by the agreement check before staleness is
    even evaluated — a caller cannot launder a stale fact by relabelling
    its own claimed timestamp."""
    fact = _fact(APPROVAL, asserted_at=NOW - timedelta(minutes=1))  # claims fresh
    evidence = _evidence(APPROVAL, fact, asserted_at=NOW - timedelta(minutes=16))  # verified: stale
    with pytest.raises(FactEvidenceMismatch) as exc:
        _admit(APPROVAL, fact, evidence)
    assert exc.value.code == "RUN_FACT_EVIDENCE_MISMATCH"


def test_evidence_fact_id_disagreeing_with_contract_is_rejected():
    """D4 / A6: evidence verified for a DIFFERENT fact cannot be replayed
    against this contract, even when the caller's own fact_id claim matches
    the contract exactly."""
    fact = _fact(APPROVAL)  # fact.fact_id == APPROVAL.fact_id, as required
    evidence = _evidence(APPROVAL, fact, fact_id="unrelated.other.fact")
    with pytest.raises(FactIdentityMismatch) as exc:
        _admit(APPROVAL, fact, evidence)
    assert exc.value.code == "RUN_FACT_IDENTITY_MISMATCH"


def test_evidence_replayed_across_fact_ids_is_rejected_even_when_value_true():
    """A6, hostile framing: genuine, fresh, correctly-issued VERIFIED
    evidence for one fact cannot satisfy a DIFFERENT contract's fact_id,
    even when the verified value would otherwise be exactly what that other
    contract wants."""
    other = replace(APPROVAL, fact_id="some.other.fact")
    fact = _fact(APPROVAL)
    evidence = _evidence(APPROVAL, fact, fact_id=other.fact_id, value=True)
    with pytest.raises(FactIdentityMismatch):
        _admit(APPROVAL, fact, evidence)


def test_claimed_asserted_by_alone_no_longer_drives_self_assertion():
    """The AC-020 defect, directly: before this repair, a caller claiming
    asserted_by=SUBJECT while evidence.asserted_by legitimately verified a
    THIRD PARTY would incorrectly self-refuse (false positive) — or worse,
    a caller claiming a third party while the true verified asserter was
    the governed subject would incorrectly ALLOW (false negative, the real
    F1 defect). Confirms the true-negative direction no longer occurs: a
    verified third-party asserter is not self-assertion merely because the
    caller's own claim disagrees, since disagreement itself refuses first."""
    fact = _fact(APPROVAL, asserted_by=SUBJECT)  # caller falsely claims the subject asserted it
    evidence = _evidence(APPROVAL, fact, asserted_by=ISSUER)  # verifier: it was really the issuer
    with pytest.raises(FactEvidenceMismatch):
        _admit(APPROVAL, fact, evidence)
