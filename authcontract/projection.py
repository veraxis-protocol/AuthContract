"""Machine-checkable projection domain + closed mediated-action universe.

Implements AC-016, layered strictly on top of `digest.verify_artifact` (R01/
AC-I06) — this module never recomputes or reinterprets contract_digest or
sibling-binding rules; it only adds one further gate stage after digest
verification succeeds: (1) a deterministic operational projection with an
explicit, machine-checkable domain, and (2) a closed mediated-action
universe checked against that projection before any later runtime decision
layer (VEIP, out of scope here — see module docstring in cli.py).

Deliberately does NOT touch `facts.py` (AC-I15). A contract's
`required_facts` declaration is carried through unexamined by this module so
that fact admissibility stays exercisable via `facts.admit()` on its own —
projection/action-closure and fact admissibility are two separate gates, not
one merged check. Mixing them would blur exactly the boundary AC-016 asks to
keep distinct.

Same fail-closed discipline throughout: an unrecognised action type, an
unknown or missing parameter, an out-of-domain value, or an ambiguous
ACTIVE-contract match is a refusal, never a best-effort pass-through.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

import rfc8785

from .digest import verify_artifact
from .facts import SUPPORTED_SIMPLE_TYPES

#: Mirrors facts.py's decimal(N) pattern. Kept as a separate constant
#: (rather than importing facts._DECIMAL_TYPE) because action parameters
#: here are plain JSON values, not wire-framed AssertedFact instances — the
#: two validators are intentionally parallel, not shared, per this module's
#: deliberate separation from AC-I15.
_DECIMAL_TYPE = re.compile(r"^decimal\((\d+)\)$")


class ProjectionDomainError(ValueError):
    """RUN_DOMAIN_ESCAPE — input/action/parameter/value outside the
    declared projection domain, or the domain declaration itself is
    malformed/unsupported."""
    code = "RUN_DOMAIN_ESCAPE"


class UnclassifiedAction(ValueError):
    """RUN_UNCLASSIFIED_ACTION — action type is not in the closed
    mediated-action universe for the ACTIVE candidate(s) considered."""
    code = "RUN_UNCLASSIFIED_ACTION"


class ContractScopeConflict(ValueError):
    """CONTRACT_SCOPE_CONFLICT — more than one ACTIVE contract/projection
    matches the same mediated action with no declared precedence."""
    code = "CONTRACT_SCOPE_CONFLICT"


class InactiveContract(ValueError):
    """RUN_INACTIVE_CONTRACT — AC-017 F1. The action pre-decision gate
    refuses because the projection's activation_state is not exactly
    "ACTIVE" (including SUSPENDED, REVOKED, missing, or any unrecognised
    value). project() may still construct a Projection for an inactive
    contract for inspection/overlap purposes; only check_action refuses."""
    code = "RUN_INACTIVE_CONTRACT"


#: AC-017 F2 — the bounded schema actually implemented. A key outside these
#: sets is refused, never silently ignored.
PROJECTION_DOMAIN_ALLOWED_KEYS = frozenset({"actions"})
ACTION_SPEC_ALLOWED_KEYS = frozenset({"parameters"})
PARAMETER_SPEC_ALLOWED_KEYS = frozenset({"value_type", "required", "enum"})
ACTION_INPUT_ALLOWED_KEYS = frozenset({"action_type", "parameters"})


@dataclass(frozen=True)
class Projection:
    """Deterministic operational projection of one verified artifact.

    A pure function of contract + activation only — admission/derivations/
    proof are never read here, so changes to those siblings (which do not
    alter contract_digest per R01) cannot alter operational semantics
    either, unless the projection domain itself explicitly depends on them
    (it does not, in this bounded implementation).
    """
    contract_digest: str
    activation_state: str | None
    activation_id: str | None
    domain: dict[str, Any]


def _validate_value_type(value_type: Any) -> None:
    if value_type in SUPPORTED_SIMPLE_TYPES or (
        isinstance(value_type, str) and _DECIMAL_TYPE.match(value_type)
    ):
        return
    raise ProjectionDomainError(
        f"{ProjectionDomainError.code}: projection domain declares unsupported "
        f"value_type {value_type!r}"
    )


def _strict_type_equal(a: Any, b: Any) -> bool:
    """Equality that never collapses across types.

    AC-017 F3: plain Python `==`/`in` lets `True == 1` and `Decimal('1') ==
    1` succeed, which can make a malformed or wrong-type value falsely
    appear to be an in-domain enum member. `type(a) is type(b)` is checked
    first so no numeric-tower or Decimal coercion can smuggle a match
    through.
    """
    return type(a) is type(b) and a == b


def _validate_enum_members(action_type: str, param_name: str, value_type: str, enum: list) -> None:
    """AC-017 F3: every enum member must itself satisfy `value_type` under
    strict type semantics — validated once, at domain-validation time, so a
    malformed enum can never even reach action evaluation."""
    decimal_match = _DECIMAL_TYPE.match(value_type) if isinstance(value_type, str) else None

    for member in enum:
        where = f"enum member {member!r} of {action_type}.{param_name}"
        if decimal_match:
            scale = int(decimal_match.group(1))
            if type(member) is not str:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: {where} must be a decimal string "
                    f"for {value_type}, not {type(member).__name__}"
                )
            try:
                decimal_member = Decimal(member)
            except InvalidOperation as exc:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: {where} is not a valid decimal string"
                ) from exc
            if not decimal_member.is_finite():
                raise ProjectionDomainError(f"{ProjectionDomainError.code}: {where} is not finite")
            if -decimal_member.as_tuple().exponent > scale:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: {where} exceeds declared scale {scale}"
                )
        elif value_type == "boolean":
            if type(member) is not bool:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: {where} must be a bool, not "
                    f"{type(member).__name__}"
                )
        elif value_type == "integer":
            # type(x) is int already excludes bool: type(True) is bool, not int.
            if type(member) is not int:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: {where} must be an int (never a "
                    f"bool), got {type(member).__name__}"
                )
        elif value_type == "string":
            if type(member) is not str:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: {where} must be a str, not "
                    f"{type(member).__name__}"
                )


def _validate_domain_shape(domain: Any) -> None:
    """Refuse a malformed/unsupported domain declaration rather than
    silently accepting whatever shape happens to be present.

    AC-017 F2: every level enforces its exact allowed key set — an unknown
    key anywhere in projection_domain/action-spec/parameter-spec is a
    refusal, never a silently-ignored field.
    """
    if not isinstance(domain, dict):
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: projection_domain must be an object"
        )

    unknown_domain_keys = sorted(set(domain) - PROJECTION_DOMAIN_ALLOWED_KEYS)
    if unknown_domain_keys:
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: projection_domain has unsupported "
            f"field(s) {unknown_domain_keys}"
        )

    actions = domain.get("actions")
    if not isinstance(actions, dict) or not actions:
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: projection_domain.actions must be a "
            "non-empty object"
        )

    for action_type, action_spec in actions.items():
        if not action_type or not isinstance(action_type, str):
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: action type {action_type!r} must be "
                "a non-empty string"
            )
        if not isinstance(action_spec, dict):
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: action '{action_type}' spec must "
                "be an object"
            )
        unknown_action_keys = sorted(set(action_spec) - ACTION_SPEC_ALLOWED_KEYS)
        if unknown_action_keys:
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: action '{action_type}' has "
                f"unsupported field(s) {unknown_action_keys}"
            )

        parameters = action_spec.get("parameters")
        if not isinstance(parameters, dict):
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: action '{action_type}' has no "
                "parameters object"
            )
        for param_name, param_spec in parameters.items():
            if not param_name or not isinstance(param_name, str):
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: parameter name {param_name!r} of "
                    f"action '{action_type}' must be a non-empty string"
                )
            if not isinstance(param_spec, dict):
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: parameter '{param_name}' of "
                    f"action '{action_type}' spec must be an object"
                )
            unknown_param_keys = sorted(set(param_spec) - PARAMETER_SPEC_ALLOWED_KEYS)
            if unknown_param_keys:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: parameter '{param_name}' of "
                    f"action '{action_type}' has unsupported field(s) {unknown_param_keys}"
                )

            value_type = param_spec.get("value_type")
            _validate_value_type(value_type)

            if "required" in param_spec and type(param_spec["required"]) is not bool:
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: parameter '{param_name}' of "
                    f"action '{action_type}' declares non-boolean `required` "
                    f"({type(param_spec['required']).__name__})"
                )

            enum = param_spec.get("enum")
            if enum is not None:
                if not isinstance(enum, list):
                    raise ProjectionDomainError(
                        f"{ProjectionDomainError.code}: parameter '{param_name}' of "
                        f"action '{action_type}' has a non-list enum"
                    )
                _validate_enum_members(action_type, param_name, value_type, enum)


def project(artifact: dict[str, Any]) -> Projection:
    """Verify `artifact`, then deterministically project it.

    All-or-nothing: any refusal below raises before a partial/best-effort
    Projection is ever returned.
    """
    contract_digest = verify_artifact(artifact)  # raises DigestScopeError / ContractDigestMismatch

    contract = artifact["contract"]
    domain = contract.get("projection_domain")
    _validate_domain_shape(domain)

    activation = artifact.get("activation")
    activation_state = activation.get("state") if isinstance(activation, dict) else None
    activation_id = activation.get("activation_id") if isinstance(activation, dict) else None

    return Projection(
        contract_digest=contract_digest,
        activation_state=activation_state,
        activation_id=activation_id,
        domain=domain,
    )


def projection_to_dict(projection: Projection) -> dict[str, Any]:
    """Stable, JSON-serializable representation. Used both for the CLI's
    `project` output and as the input to `projection_digest`."""
    return {
        "contract_digest": projection.contract_digest,
        "activation_id": projection.activation_id,
        "activation_state": projection.activation_state,
        "domain": projection.domain,
    }


def projection_digest(projection: Projection) -> str:
    """`sha256:<hex>` over RFC 8785 JCS(projection_to_dict(projection)).

    Deterministic and separately computable from the projection alone —
    identical projections always hash identically, regardless of key order
    in the source JSON.
    """
    import hashlib

    return "sha256:" + hashlib.sha256(rfc8785.dumps(projection_to_dict(projection))).hexdigest()


def _check_value(action_type: str, param_name: str, spec: dict[str, Any], value: Any) -> Any:
    value_type = spec.get("value_type")

    decimal_match = _DECIMAL_TYPE.match(value_type) if isinstance(value_type, str) else None
    if decimal_match:
        scale = int(decimal_match.group(1))
        if isinstance(value, float) or isinstance(value, bool) or not isinstance(value, str):
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} declared "
                f"{value_type} but must arrive as a decimal string, got "
                f"{type(value).__name__}"
            )
        try:
            decimal_value = Decimal(value)
        except InvalidOperation as exc:
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} is not a "
                "valid decimal string"
            ) from exc
        if not decimal_value.is_finite():
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} is not finite"
            )
        if -decimal_value.as_tuple().exponent > scale:
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} exceeds "
                f"declared scale {scale}"
            )
        normalized: Any = decimal_value
    elif value_type == "boolean":
        if not isinstance(value, bool):
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} is not boolean"
            )
        normalized = value
    elif value_type == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} is not an integer"
            )
        normalized = value
    elif value_type == "string":
        if not isinstance(value, str):
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} is not a string"
            )
        normalized = value
    else:  # pragma: no cover - unreachable, _validate_domain_shape already refused this
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: {action_type}.{param_name} has unhandled "
            f"value_type {value_type!r}"
        )

    enum = spec.get("enum")
    if enum is not None:
        if decimal_match:
            # Enum members are validated decimal strings (F3); compare on
            # the Decimal level so "500" and "500.00" are recognised as the
            # same declared value, without ever falling back to Python's
            # cross-type `==` on the raw member string.
            in_enum = any(_strict_type_equal(normalized, Decimal(member)) for member in enum)
        else:
            in_enum = any(_strict_type_equal(normalized, member) for member in enum)
        if not in_enum:
            raise ProjectionDomainError(
                f"{ProjectionDomainError.code}: {action_type}.{param_name} = {value!r} is "
                f"not one of the declared values {enum!r}"
            )

    return normalized


def check_action(projection: Projection, action: dict[str, Any]) -> dict[str, Any]:
    """Pre-decision boundary gate. Returns validated/typed parameters, or
    raises InactiveContract / UnclassifiedAction / ProjectionDomainError.
    Never falls through to a wildcard/catch-all action class.

    AC-017 F1: refuses unless `projection.activation_state == "ACTIVE"` —
    checked before the action is evaluated against the domain at all, so a
    SUSPENDED/REVOKED/missing/unrecognised activation state can never reach
    PASS regardless of how well-formed the action itself is. `project()`
    still constructs Projections for inactive contracts (needed for
    inspection and `select_matching_projection`'s overlap checks) — only
    this pre-decision gate enforces activation.
    """
    if not isinstance(action, dict):
        raise ProjectionDomainError(f"{ProjectionDomainError.code}: action must be an object")

    unknown_action_keys = sorted(set(action) - ACTION_INPUT_ALLOWED_KEYS)
    if unknown_action_keys:
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: action has unsupported top-level "
            f"field(s) {unknown_action_keys}"
        )

    if projection.activation_state != "ACTIVE":
        raise InactiveContract(
            f"{InactiveContract.code}: projection activation_state is "
            f"{projection.activation_state!r}, not ACTIVE — the action "
            "pre-decision gate refuses any action under an inactive contract"
        )

    action_type = action.get("action_type")
    if not action_type or not isinstance(action_type, str):
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: action_type {action_type!r} must be a "
            "non-empty string"
        )

    actions = projection.domain.get("actions", {})
    if action_type not in actions:
        raise UnclassifiedAction(
            f"{UnclassifiedAction.code}: '{action_type}' is not in the closed "
            "mediated-action universe for this projection"
        )

    schema = actions[action_type]["parameters"]
    parameters = action.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: {action_type} parameters must be an object"
        )

    unknown = sorted(set(parameters) - set(schema))
    if unknown:
        raise ProjectionDomainError(
            f"{ProjectionDomainError.code}: {action_type} has unsupported "
            f"parameter(s) {unknown}"
        )

    validated: dict[str, Any] = {}
    for name, spec in schema.items():
        if name not in parameters:
            if spec.get("required", False):
                raise ProjectionDomainError(
                    f"{ProjectionDomainError.code}: {action_type} is missing required "
                    f"parameter '{name}'"
                )
            continue
        validated[name] = _check_value(action_type, name, spec, parameters[name])

    return validated


def select_matching_projection(
    candidates: list[Projection], action_type: str
) -> Projection:
    """The bounded overlap check required by AC-016 section E.

    Only ACTIVE candidates whose domain declares `action_type` are
    considered. Zero -> UnclassifiedAction (out of scope). More than one,
    with no declared precedence/composition mechanism implemented in this
    bounded step -> ContractScopeConflict. Never picks by load order,
    list position, or any other implicit first-match rule.
    """
    matches = [
        p for p in candidates
        if p.activation_state == "ACTIVE" and action_type in p.domain.get("actions", {})
    ]

    if len(matches) == 0:
        raise UnclassifiedAction(
            f"{UnclassifiedAction.code}: no ACTIVE contract declares action "
            f"'{action_type}'"
        )
    if len(matches) > 1:
        raise ContractScopeConflict(
            f"{ContractScopeConflict.code}: {len(matches)} ACTIVE contracts match "
            f"action '{action_type}' with no declared precedence/composition rule"
        )
    return matches[0]
