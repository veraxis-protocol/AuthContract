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

    `trust_basis` is what the asserting party CLAIMS. It is checked against
    the contract's requirement; a claim is not self-validating.
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


def _check_representation(contract: FactContract, fact: AssertedFact) -> Any:
    """Reject lossy transport. Returns the losslessly-decoded value."""
    if fact.wire_representation != contract.wire_representation:
        raise FactRepresentation(
            f"{FactRepresentation.code}: {contract.fact_id} declared "
            f"{contract.wire_representation}, arrived as {fact.wire_representation}"
        )

    decimal_match = _DECIMAL_TYPE.match(contract.value_type)
    if decimal_match:
        scale = int(decimal_match.group(1))
        # A float has already lost information before we can inspect it.
        if isinstance(fact.raw_value, float):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} declared "
                f"{contract.value_type} but arrived as float — host decoder "
                "flattened the value before evaluation"
            )
        if isinstance(fact.raw_value, bool):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} declared "
                f"{contract.value_type} but arrived as bool"
            )
        try:
            value = Decimal(str(fact.raw_value))
        except InvalidOperation as exc:
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} is not decimal"
            ) from exc
        if not value.is_finite():
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} is not finite"
            )
        if -value.as_tuple().exponent > scale:
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} exceeds declared "
                f"scale {scale}"
            )
        return value

    if contract.value_type == "boolean":
        if not isinstance(fact.raw_value, bool):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} is not boolean"
            )
        return fact.raw_value

    if contract.value_type == "integer":
        # bool is a subclass of int; reject it explicitly.
        if isinstance(fact.raw_value, bool) or not isinstance(fact.raw_value, int):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} is not an integer"
            )
        return fact.raw_value

    if contract.value_type == "string":
        if not isinstance(fact.raw_value, str):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} is not a string"
            )
        return fact.raw_value

    # Unreachable: _validate_contract already refused unknown types. Kept as a
    # fail-closed backstop so a future type addition cannot silently pass through.
    raise FactTypeUnsupported(
        f"{FactTypeUnsupported.code}: {contract.fact_id} has unhandled value type "
        f"'{contract.value_type}'"
    )


def _check_corroboration(contract: FactContract, fact: AssertedFact) -> None:
    """Independent confirmation. Independence is enforced, not assumed."""
    if not fact.corroborated_by:
        raise FactCorroborationMissing(
            f"{FactCorroborationMissing.code}: {contract.fact_id} requires "
            "corroboration; none supplied"
        )
    if fact.corroborated_by == fact.asserted_by:
        raise FactCorroborationMissing(
            f"{FactCorroborationMissing.code}: {contract.fact_id} corroboration "
            "is not independent — corroborator is the asserting party"
        )


def admit(
    contract: FactContract,
    fact: AssertedFact,
    *,
    governed_subject: str,
    now: datetime,
) -> Any:
    """Run the AC-I15 admissibility gate. Returns the value, or raises.

    Check order is deliberate:
      1. contract well-formedness — never evaluate against a broken contract
      2. fact identity          — never evaluate the wrong fact
      3. representation         — a lossily transported value cannot be judged
      4. issuer / trust basis / path
      5. freshness
      6. self-assertion policy
      7. corroboration requirement
    """
    _validate_contract(contract)

    if fact.fact_id != contract.fact_id:
        raise FactIdentityMismatch(
            f"{FactIdentityMismatch.code}: contract governs '{contract.fact_id}' "
            f"but fact asserts '{fact.fact_id}'"
        )

    value = _check_representation(contract, fact)

    if fact.issuer != contract.issuer:
        raise FactUnattested(
            f"{FactUnattested.code}: {contract.fact_id} requires issuer "
            f"{contract.issuer}, got {fact.issuer}"
        )

    if fact.trust_basis != contract.trust_basis:
        raise FactTrustBasisMismatch(
            f"{FactTrustBasisMismatch.code}: {contract.fact_id} requires trust "
            f"basis '{contract.trust_basis}', asserted with '{fact.trust_basis}'"
        )

    if fact.assertion_path != contract.assertion_path:
        raise FactUnattested(
            f"{FactUnattested.code}: {contract.fact_id} requires assertion path "
            f"{contract.assertion_path}, arrived via {fact.assertion_path}"
        )

    if now - fact.asserted_at > contract.freshness:
        raise FactStale(
            f"{FactStale.code}: {contract.fact_id} is older than "
            f"{contract.freshness}"
        )

    if fact.asserted_by == governed_subject:
        policy = contract.self_assertion_policy
        if policy == "PROHIBITED":
            raise FactSelfAsserted(
                f"{FactSelfAsserted.code}: {contract.fact_id} was asserted by "
                f"the governed subject '{governed_subject}'; policy is PROHIBITED"
            )
        if policy == "PERMITTED_WITH_CORROBORATION":
            _check_corroboration(contract, fact)
            if fact.corroborated_by == governed_subject:
                raise FactCorroborationMissing(
                    f"{FactCorroborationMissing.code}: {contract.fact_id} "
                    "corroboration collusion — corroborator is the governed subject"
                )

    # Applies regardless of who asserted the fact (AC-009 finding 5).
    if contract.corroboration_required:
        _check_corroboration(contract, fact)
        if fact.corroborated_by == governed_subject:
            raise FactCorroborationMissing(
                f"{FactCorroborationMissing.code}: {contract.fact_id} "
                "corroboration collusion — corroborator is the governed subject"
            )

    return value
