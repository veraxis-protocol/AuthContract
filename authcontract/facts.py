"""Runtime fact admissibility gate. Implements AC-I15 / R10.

The v0.1 specification named "required facts/evidence" without governing who
may assert them. A control requiring `secondary_approval.present == true` is
decorative if the governed agent may supply that fact.

This gate runs BEFORE policy evaluation. A fact that fails any check never
reaches the engine.

Also enforces the surviving form of R02: the original float64 counterexample
was refuted against OPA v1.19.1 (0/5 divergences), because OPA preserves
json.Number. The real hazard is a host decoder flattening decimal(scale)
before the engine sees it. That is a representation failure, caught here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


class FactInadmissible(Exception):
    """Base: fact rejected before policy evaluation."""
    code = "RUN_FACT_INADMISSIBLE"


class FactUnattested(FactInadmissible):
    code = "RUN_FACT_UNATTESTED"


class FactStale(FactInadmissible):
    code = "RUN_FACT_STALE"


class FactRepresentation(FactInadmissible):
    code = "RUN_FACT_REPRESENTATION"


class FactSelfAsserted(FactInadmissible):
    code = "RUN_FACT_SELF_ASSERTED"


@dataclass(frozen=True)
class FactContract:
    """AC-I15 declaration. Every field is required; none defaults silently."""
    fact_id: str
    value_type: str                  # e.g. "decimal(2)", "boolean", "instant"
    issuer: str
    trust_basis: str
    freshness: timedelta
    assertion_path: str
    self_assertion_policy: str       # PROHIBITED | PERMITTED_WITH_CORROBORATION | PERMITTED
    wire_representation: str         # e.g. "decimal_string", "json_boolean"
    corroboration_required: bool = False


@dataclass(frozen=True)
class AssertedFact:
    """A fact as it actually arrived at the boundary."""
    fact_id: str
    raw_value: Any
    wire_representation: str
    issuer: str
    asserted_by: str
    asserted_at: datetime
    assertion_path: str
    corroborated_by: str | None = None


def _check_representation(contract: FactContract, fact: AssertedFact) -> Any:
    """Reject lossy transport. Returns the losslessly-decoded value."""
    if fact.wire_representation != contract.wire_representation:
        raise FactRepresentation(
            f"{FactRepresentation.code}: {contract.fact_id} declared "
            f"{contract.wire_representation}, arrived as {fact.wire_representation}"
        )

    if contract.value_type.startswith("decimal("):
        scale = int(contract.value_type[8:-1])
        # A float has already lost information before we can inspect it.
        if isinstance(fact.raw_value, float):
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} declared "
                f"{contract.value_type} but arrived as float — host decoder "
                "flattened the value before evaluation"
            )
        try:
            value = Decimal(str(fact.raw_value))
        except InvalidOperation as exc:
            raise FactRepresentation(
                f"{FactRepresentation.code}: {contract.fact_id} is not decimal"
            ) from exc
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

    return fact.raw_value


def admit(
    contract: FactContract,
    fact: AssertedFact,
    *,
    governed_subject: str,
    now: datetime,
) -> Any:
    """Run the AC-I15 admissibility gate. Returns the value, or raises.

    Order is deliberate: representation is checked first, because a lossily
    transported value cannot be meaningfully evaluated for anything else.
    """
    value = _check_representation(contract, fact)

    if fact.issuer != contract.issuer:
        raise FactUnattested(
            f"{FactUnattested.code}: {contract.fact_id} requires issuer "
            f"{contract.issuer}, got {fact.issuer}"
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
            if not fact.corroborated_by:
                raise FactUnattested(
                    f"{FactUnattested.code}: {contract.fact_id} self-asserted "
                    "without required corroboration"
                )
            if fact.corroborated_by == governed_subject:
                raise FactUnattested(
                    f"{FactUnattested.code}: {contract.fact_id} corroboration "
                    "collusion — corroborator is the governed subject"
                )

    return value
