"""Runtime fact admissibility gate. Implements AC-I15 / R10.

The v0.1 specification named "required facts/evidence" without governing who
may assert them. A control requiring `secondary_approval.present == true` is
decorative if the governed agent may supply that fact.

This gate runs BEFORE policy evaluation. A fact that fails any check never
reaches the engine.

Design rule, applied throughout: every unrecognised input fails CLOSED. An
unknown value type, an unknown self-assertion policy, or a malformed contract
is a refusal, never a pass-through. A gate that admits what it does not
understand is not a gate.

Also enforces the surviving form of R02: the original float64 counterexample
was refuted against OPA v1.19.1 (0/5 divergences), because OPA preserves
json.Number. The real hazard is a host decoder flattening decimal(scale)
before the engine sees it. That is a representation failure, caught here.

AC-020 / F1 repair: AC-012 already established that issuer/trust-basis/path/
corroborator decisions must use `VerifiedEvidence`, never `AssertedFact`'s own
claimed text. It did not establish that VERIFIED context binds fact identity,
the operative value, the asserting identity, or the assertion timestamp —
`admit()` used `fact.raw_value`/`fact.asserted_at`/`fact.asserted_by`/
`fact.fact_id` (all caller CLAIMS) for those decisions, which let a caller
substitute a false value/time/asserter/identity while presenting an otherwise
matching verifier context. `VerifiedEvidence` now also binds fact identity,
the verified operative value, the verified asserting identity, and the
verified assertion timestamp; `admit()` requires the caller's claim to agree
with this verified context (else `FactEvidenceMismatch`, AC-020 A2), and every
identity/freshness/self-assertion/value decision is now made against the
VERIFIED fields, never the claimed ones. `VerifiedEvidence` remains an
interface boundary supplied by a trusted verifier — this proves internal
consistency between what was claimed and what was verified, not signatures,
channel authentication, or institutional provenance (AC-020 A7).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

#: Self-assertion policies this implementation understands. Anything else
#: is a contract defect and fails closed (AC-009 finding 3).
VALID_SELF_ASSERTION_POLICIES = frozenset(
    {"PROHIBITED", "PERMITTED_WITH_CORROBORATION", "PERMITTED"}
)

#: Value types this implementation can validate losslessly. Anything else
#: fails closed rather than passing through raw (AC-009 finding 4).
SUPPORTED_SIMPLE_TYPES = frozenset({"boolean", "string", "integer"})

_DECIMAL_TYPE = re.compile(r"^decimal\((\d+)\)$")


class FactInadmissible(Exception):
    """Base: fact rejected before policy evaluation."""
    code = "RUN_FACT_INADMISSIBLE"


class FactIdentityMismatch(FactInadmissible):
    code = "RUN_FACT_IDENTITY_MISMATCH"


class FactUnattested(FactInadmissible):
    code = "RUN_FACT_UNATTESTED"


class FactStale(FactInadmissible):
    code = "RUN_FACT_STALE"


class FactRepresentation(FactInadmissible):
    code = "RUN_FACT_REPRESENTATION"


class FactSelfAsserted(FactInadmissible):
    code = "RUN_FACT_SELF_ASSERTED"


class FactTrustBasisMismatch(FactInadmissible):
    code = "RUN_FACT_TRUST_BASIS"


class FactTypeUnsupported(FactInadmissible):
    code = "RUN_FACT_TYPE_UNSUPPORTED"


class FactContractInvalid(FactInadmissible):
    code = "RUN_FACT_CONTRACT_INVALID"


class FactCorroborationMissing(FactInadmissible):
    code = "RUN_FACT_CORROBORATION_MISSING"


class FactFutureTimestamp(FactInadmissible):
    code = "RUN_FACT_FUTURE_TIMESTAMP"


class FactTimeUnverifiable(FactInadmissible):
    code = "RUN_FACT_TIME_UNVERIFIABLE"


class FactEvidenceMismatch(FactInadmissible):
    """AC-020 A2 — the caller-claimed `AssertedFact` semantics (operative
    value, asserting identity, or assertion timestamp) disagree with the
    verifier-established `VerifiedEvidence` context. A caller cannot
    substitute a false value/time/asserter while presenting an otherwise
    matching verifier context."""
    code = "RUN_FACT_EVIDENCE_MISMATCH"


@dataclass(frozen=True)
class FactContract:
    """AC-I15 declaration. Every field is required; none defaults silently."""
    fact_id: str
    value_type: str                  # "boolean" | "string" | "integer" | "decimal(N)"
    issuer: str
    trust_basis: str
    freshness: timedelta
    assertion_path: str
    self_assertion_policy: str       # see VALID_SELF_ASSERTION_POLICIES
    wire_representation: str         # e.g. "decimal_string", "json_boolean"
    corroboration_required: bool = False


@dataclass(frozen=True)
class AssertedFact:
    """A fact as it actually arrived at the boundary.

    Every field on this object is the asserting party's own CLAIM. None of
    it is authoritative on its own — `issuer`, `trust_basis`, `assertion_path`
    and `corroborated_by` here exist for audit/logging only. `admit()` binds
    its issuer/trust-basis/path/corroboration decisions to the caller-supplied
    `VerifiedEvidence` instead (AC-012 finding 1): caller-provided text alone
    must never be sufficient to establish that context.
    """
    fact_id: str
    raw_value: Any
    wire_representation: str
    issuer: str
    trust_basis: str
    asserted_by: str
    asserted_at: datetime
    assertion_path: str
    corroborated_by: str | None = None


@dataclass(frozen=True)
class VerifiedEvidence:
    """Evidence context established by the trusted verification boundary.

    Constructed ONLY by whatever actually verifies provenance for this
    deployment (signature/channel authentication, corroborator identity
    lookup, etc.) — never by the party asserting the fact, and never derived
    from `AssertedFact`'s own claimed fields. This is the smallest explicit
    separation between "claimed" and "verified" suitable for MVP-alpha: a
    real verifier is expected to construct this; nothing here performs
    cryptographic verification itself.

    AC-020 A1 extends this beyond issuer/trust_basis/assertion_path/
    corroborated_by to also bind the exact assertion semantics `admit()`
    actually adjudicates: which fact this evidence is bound to, what the
    verified operative value is, who the verified asserting identity is, and
    when the verified assertion occurred. Evidence verified for one
    `fact_id` must never be replayable as another (A6); `value` is expressed
    in the same wire-format domain as `AssertedFact.raw_value` and decoded
    via the governing `FactContract.value_type`, the same way an asserted
    value is (A1/A5).
    """
    fact_id: str
    value: Any
    asserted_by: str
    asserted_at: datetime
    issuer: str
    trust_basis: str
    assertion_path: str
    corroborated_by: str | None = None


def _validate_contract(contract: FactContract) -> None:
    """Reject a malformed contract before evaluating anything against it."""
    if contract.self_assertion_policy not in VALID_SELF_ASSERTION_POLICIES:
        raise FactContractInvalid(
            f"{FactContractInvalid.code}: {contract.fact_id} declares unknown "
            f"self_assertion_policy '{contract.self_assertion_policy}'; "
            f"known policies are {sorted(VALID_SELF_ASSERTION_POLICIES)}"
        )

    if not (
        contract.value_type in SUPPORTED_SIMPLE_TYPES
        or _DECIMAL_TYPE.match(contract.value_type)
    ):
        raise FactTypeUnsupported(
            f"{FactTypeUnsupported.code}: {contract.fact_id} declares value type "
            f"'{contract.value_type}', which this implementation cannot validate "
            "losslessly; refusing rather than admitting unchecked"
        )


def _decode_raw_value(contract: FactContract, raw_value: Any, *, source: str) -> Any:
    """Decode a raw wire-format value into its typed Python form, per
    `contract.value_type`. Shared by both the caller-claimed
    `AssertedFact.raw_value` (via `_check_representation`, after its own
    `wire_representation` match) and the verifier-established
    `VerifiedEvidence.value` (AC-020 A1/A5) — the same lossless-decode rules
    apply to both, so a value can never be judged before it is known to be
    representable at all.
    """
    decimal_match = _DECIMAL_TYPE.match(contract.value_type)
    if decimal_match:
        scale = int(decimal_match.group(1))
        # A float has already lost information before we can inspect it.
        if isinstance(raw_value, float):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) declared "
                f"{contract.value_type} but arrived as float — host decoder "
                "flattened the value before evaluation"
            )
        if isinstance(raw_value, bool):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) declared "
                f"{contract.value_type} but arrived as bool"
            )
        try:
            value = Decimal(str(raw_value))
        except InvalidOperation as exc:
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) is not decimal"
            ) from exc
        if not value.is_finite():
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) is not finite"
            )
        if -value.as_tuple().exponent > scale:
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) exceeds "
                f"declared scale {scale}"
            )
        return value

    if contract.value_type == "boolean":
        if not isinstance(raw_value, bool):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) is not boolean"
            )
        return raw_value

    if contract.value_type == "integer":
        # bool is a subclass of int; reject it explicitly.
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) is not an integer"
            )
        return raw_value

    if contract.value_type == "string":
        if not isinstance(raw_value, str):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} ({source}) is not a string"
            )
        return raw_value

    # Unreachable: _validate_contract already refused unknown types. Kept as a
    # fail-closed backstop so a future type addition cannot silently pass through.
    raise FactTypeUnsupported(
        f"{FactTypeUnsupported.code}: {contract.fact_id} has unhandled value type "
        f"'{contract.value_type}'"
    )


def _check_representation(contract: FactContract, fact: AssertedFact) -> Any:
    """Reject lossy transport for the caller-claimed value. Returns the
    losslessly-decoded value."""
    if fact.wire_representation != contract.wire_representation:
        raise FactRepresentation(
            f"{FactRepresentation.code}: {contract.fact_id} declared "
            f"{contract.wire_representation}, arrived as {fact.wire_representation}"
        )
    return _decode_raw_value(contract, fact.raw_value, source="asserted")


def _check_corroboration(contract: FactContract, evidence: VerifiedEvidence) -> None:
    """Independent confirmation. Independence is enforced, not assumed.

    Corroborator identity AND asserting identity both come from `evidence`
    — never from the fact's own claimed `corroborated_by`/`asserted_by`. A
    self-asserted corroborator is not corroboration (AC-012 finding 1), and
    independence must be judged against the VERIFIED asserting identity, not
    a caller's claim about who asserted the fact (AC-020 A3) — a caller
    cannot manufacture apparent independence by lying about the asserter.
    """
    if not evidence.corroborated_by:
        raise FactCorroborationMissing(
            f"{FactCorroborationMissing.code}: {contract.fact_id} requires "
            "corroboration; none verified"
        )
    if evidence.corroborated_by == evidence.asserted_by:
        raise FactCorroborationMissing(
            f"{FactCorroborationMissing.code}: {contract.fact_id} corroboration "
            "is not independent — corroborator is the verified asserting party"
        )


def _check_freshness(contract: FactContract, asserted_at: datetime, now: datetime) -> None:
    """Time validation. Fails closed on a future timestamp or an
    unverifiable comparison, rather than raising an uncontrolled exception.

    `asserted_at` must be the VERIFIED assertion timestamp (AC-020 A4) — by
    the time this is called, `admit()` has already required it to agree
    exactly with the caller's claimed `AssertedFact.asserted_at`, so a
    caller cannot make stale evidence fresh merely by relabelling its own
    claimed timestamp.
    """
    try:
        age = now - asserted_at
    except TypeError as exc:
        raise FactTimeUnverifiable(
            f"{FactTimeUnverifiable.code}: {contract.fact_id} verified assertion "
            f"time ({asserted_at!r}) is not comparable to `now` ({now!r}) — "
            "naive/aware datetime mismatch"
        ) from exc

    if age < timedelta(0):
        raise FactFutureTimestamp(
            f"{FactFutureTimestamp.code}: {contract.fact_id} verified assertion "
            f"time is {-age} in the future relative to `now`"
        )

    if age > contract.freshness:
        raise FactStale(
            f"{FactStale.code}: {contract.fact_id} is older than "
            f"{contract.freshness}"
        )


def admit(
    contract: FactContract,
    fact: AssertedFact,
    *,
    evidence: VerifiedEvidence,
    governed_subject: str,
    now: datetime,
) -> Any:
    """Run the AC-I15 admissibility gate. Returns the VERIFIED value, or raises.

    `evidence` must come from the trusted verification boundary, never be
    derived from `fact`'s own claimed fields — issuer, trust basis,
    assertion path, corroborator identity, fact identity, operative value,
    asserting identity, and assertion timestamp are ALL decided against
    `evidence`, never against the asserting party's own text (AC-012
    finding 1; AC-020 A1-A6). `fact` is required to agree with `evidence`
    on identity/value/asserter/time (else `FactEvidenceMismatch`) — a caller
    cannot substitute a false value, time, asserter, or fact identity while
    presenting an otherwise matching verifier context.

    Check order is deliberate:
      1. contract well-formedness  — never evaluate against a broken contract
      2. fact identity vs contract — never evaluate the wrong fact
      3. evidence identity vs contract — evidence verified for one fact_id
         cannot govern another (A6)
      4. representation (both claimed and verified value) — a lossily
         transported value cannot be judged
      5. issuer / trust basis / path (verified, not claimed)
      6. claimed-vs-verified agreement: value, asserted_by, asserted_at
         (A2) — fails closed on ANY disagreement
      7. freshness, using the VERIFIED assertion time (A4) — fails closed
         on future timestamps and on unverifiable (naive/aware) comparisons,
         not just staleness
      8. self-assertion policy, using the VERIFIED asserting identity (A3)
      9. corroboration requirement (verified corroborator identity)

    Returns the VERIFIED operative value (A5), not the caller's raw claim —
    by this point the two are already proven equal, but binding the return
    value to the verified side keeps the invariant explicit rather than
    incidental.
    """
    _validate_contract(contract)

    if fact.fact_id != contract.fact_id:
        raise FactIdentityMismatch(
            f"{FactIdentityMismatch.code}: contract governs '{contract.fact_id}' "
            f"but fact asserts '{fact.fact_id}'"
        )

    if evidence.fact_id != contract.fact_id:
        raise FactIdentityMismatch(
            f"{FactIdentityMismatch.code}: contract governs '{contract.fact_id}' "
            f"but verified evidence is bound to '{evidence.fact_id}' — evidence "
            "verified for one fact cannot be replayed as another (AC-020 A6)"
        )

    asserted_value = _check_representation(contract, fact)
    verified_value = _decode_raw_value(contract, evidence.value, source="verified")

    if evidence.issuer != contract.issuer:
        raise FactUnattested(
            f"{FactUnattested.code}: {contract.fact_id} requires issuer "
            f"{contract.issuer}, verified issuer is {evidence.issuer}"
        )

    if evidence.trust_basis != contract.trust_basis:
        raise FactTrustBasisMismatch(
            f"{FactTrustBasisMismatch.code}: {contract.fact_id} requires trust "
            f"basis '{contract.trust_basis}', verified trust basis is "
            f"'{evidence.trust_basis}'"
        )

    if evidence.assertion_path != contract.assertion_path:
        raise FactUnattested(
            f"{FactUnattested.code}: {contract.fact_id} requires assertion path "
            f"{contract.assertion_path}, verified path is {evidence.assertion_path}"
        )

    if asserted_value != verified_value:
        raise FactEvidenceMismatch(
            f"{FactEvidenceMismatch.code}: {contract.fact_id} claimed value "
            f"{asserted_value!r} disagrees with verifier-established value "
            f"{verified_value!r}"
        )

    if fact.asserted_by != evidence.asserted_by:
        raise FactEvidenceMismatch(
            f"{FactEvidenceMismatch.code}: {contract.fact_id} claimed asserted_by "
            f"{fact.asserted_by!r} disagrees with verified asserting identity "
            f"{evidence.asserted_by!r}"
        )

    if fact.asserted_at != evidence.asserted_at:
        raise FactEvidenceMismatch(
            f"{FactEvidenceMismatch.code}: {contract.fact_id} claimed asserted_at "
            f"{fact.asserted_at!r} disagrees with verified assertion time "
            f"{evidence.asserted_at!r}"
        )

    _check_freshness(contract, evidence.asserted_at, now)

    if evidence.asserted_by == governed_subject:
        policy = contract.self_assertion_policy
        if policy == "PROHIBITED":
            raise FactSelfAsserted(
                f"{FactSelfAsserted.code}: {contract.fact_id} was asserted by "
                f"the governed subject '{governed_subject}' (verified); policy "
                "is PROHIBITED"
            )
        if policy == "PERMITTED_WITH_CORROBORATION":
            _check_corroboration(contract, evidence)
            if evidence.corroborated_by == governed_subject:
                raise FactCorroborationMissing(
                    f"{FactCorroborationMissing.code}: {contract.fact_id} "
                    "corroboration collusion — corroborator is the governed subject"
                )

    # Applies regardless of who asserted the fact (AC-009 finding 5).
    if contract.corroboration_required:
        _check_corroboration(contract, evidence)
        if evidence.corroborated_by == governed_subject:
            raise FactCorroborationMissing(
                f"{FactCorroborationMissing.code}: {contract.fact_id} "
                "corroboration collusion — corroborator is the governed subject"
            )

    return verified_value
