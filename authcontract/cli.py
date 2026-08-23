"""`authcontract verify|project|check-action` — CLI over the digest (R01/
AC-I06) and projection/action-closure (AC-016) gates.

MVP-alpha scope only. Does not implement VEIP binding, AEP reconstruction,
or production provenance verification — those are later gates.

Same fail-closed discipline as `digest.py`/`facts.py`/`projection.py`: an
unrecognised top-level shape, action, or parameter is a refusal, never a
silently-ignored field that could produce a false PASS.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from .digest import ContractDigestMismatch, DigestScopeError, verify_artifact
from .projection import (
    ProjectionDomainError,
    UnclassifiedAction,
    check_action,
    project,
    projection_digest,
    projection_to_dict,
)

#: The only top-level fields `verify_artifact` understands. Anything else is
#: rejected rather than silently ignored — an ignored field could hide a
#: change that should have caused a refusal.
ALLOWED_TOP_LEVEL_KEYS = frozenset(
    {"contract", "admission", "activation", "derivations", "proof"}
)
SIBLING_KEYS = ("admission", "activation", "derivations", "proof")


def _validate_structure(artifact: Any) -> str | None:
    """Return a refusal message, or None if the shape is acceptable."""
    if not isinstance(artifact, dict):
        return "top-level artifact must be a JSON object"

    unknown = sorted(set(artifact) - ALLOWED_TOP_LEVEL_KEYS)
    if unknown:
        return f"unsupported top-level field(s): {unknown}"

    if "contract" not in artifact:
        return "artifact has no `contract` object"
    if not isinstance(artifact["contract"], dict):
        return "`contract` must be a JSON object"

    for sibling in SIBLING_KEYS:
        if sibling in artifact and not isinstance(artifact[sibling], dict):
            return f"`{sibling}` must be a JSON object"

    return None


def _refused(code: str, message: str, fixture_name: str) -> dict[str, Any]:
    return {
        "status": "REFUSED",
        "reason_code": code,
        "message": message,
        "fixture": fixture_name,
    }


def _load_json_file(path: str, label: str) -> tuple[Any, tuple[str, str] | None]:
    """Read+parse one JSON file. Returns (parsed, None), or (None, (code,
    message)) on failure — never raises."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return None, ("AC_IO_ERROR", f"cannot read {label}: {exc}")
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, ("AC_INVALID_JSON", f"{label} is not valid JSON: {exc}")


def verify_fixture(path: str) -> tuple[dict[str, Any], bool]:
    """Verify one fixture file. Returns (result, passed)."""
    fixture_name = os.path.basename(path)

    artifact, error = _load_json_file(path, "fixture")
    if error is not None:
        code, message = error
        return _refused(code, message, fixture_name), False

    structure_error = _validate_structure(artifact)
    if structure_error is not None:
        return _refused("AC_INVALID_STRUCTURE", structure_error, fixture_name), False

    try:
        digest = verify_artifact(artifact)
    except DigestScopeError as exc:
        return _refused(exc.code, str(exc), fixture_name), False
    except ContractDigestMismatch as exc:
        return _refused(exc.code, str(exc), fixture_name), False
    except Exception as exc:  # fail closed on anything this CLI didn't anticipate
        return _refused("AC_INTERNAL_ERROR", str(exc), fixture_name), False

    return {
        "status": "PASS",
        "reason_code": "OK",
        "contract_digest": digest,
        "fixture": fixture_name,
    }, True


def _project_from_fixture(
    path: str,
) -> tuple[Any, dict[str, Any] | None]:
    """Shared by `project` and `check-action`: load+verify+project one
    fixture. Returns (Projection, None) on success, or (None, refusal_dict)."""
    fixture_name = os.path.basename(path)

    artifact, error = _load_json_file(path, "fixture")
    if error is not None:
        code, message = error
        return None, _refused(code, message, fixture_name)

    structure_error = _validate_structure(artifact)
    if structure_error is not None:
        return None, _refused("AC_INVALID_STRUCTURE", structure_error, fixture_name)

    try:
        proj = project(artifact)
    except (DigestScopeError, ContractDigestMismatch, ProjectionDomainError) as exc:
        return None, _refused(exc.code, str(exc), fixture_name)
    except Exception as exc:  # fail closed on anything this CLI didn't anticipate
        return None, _refused("AC_INTERNAL_ERROR", str(exc), fixture_name)

    return proj, None


def project_fixture(path: str) -> tuple[dict[str, Any], bool]:
    """`authcontract project <fixture>`. Returns (result, passed)."""
    fixture_name = os.path.basename(path)
    proj, error = _project_from_fixture(path)
    if error is not None:
        return error, False

    return {
        "status": "PASS",
        "reason_code": "OK",
        "projection_digest": projection_digest(proj),
        "fixture": fixture_name,
        **projection_to_dict(proj),
    }, True


def check_action_cli(fixture_path: str, action_path: str) -> tuple[dict[str, Any], bool]:
    """`authcontract check-action <fixture> <action-json>`. Returns
    (result, passed). `<action-json>` is a path to a committed JSON file
    (not inline JSON text), matching `<fixture>`'s own convention."""
    fixture_name = os.path.basename(fixture_path)
    action_name = os.path.basename(action_path)

    proj, error = _project_from_fixture(fixture_path)
    if error is not None:
        return error, False

    action, load_error = _load_json_file(action_path, "action")
    if load_error is not None:
        code, message = load_error
        return _refused(code, message, fixture_name), False

    try:
        validated = check_action(proj, action)
    except (UnclassifiedAction, ProjectionDomainError) as exc:
        return _refused(exc.code, str(exc), fixture_name), False
    except Exception as exc:  # fail closed on anything this CLI didn't anticipate
        return _refused("AC_INTERNAL_ERROR", str(exc), fixture_name), False

    return {
        "status": "PASS",
        "reason_code": "OK",
        "contract_digest": proj.contract_digest,
        "projection_digest": projection_digest(proj),
        "action_type": action.get("action_type") if isinstance(action, dict) else None,
        "parameters_validated": sorted(validated),
        "fixture": fixture_name,
        "action_file": action_name,
    }, True


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="authcontract")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="Verify one bounded synthetic JSON AuthContract artifact"
    )
    verify_parser.add_argument("fixture", help="Path to the JSON artifact")

    project_parser = subparsers.add_parser(
        "project", help="Compute the deterministic operational projection of one fixture"
    )
    project_parser.add_argument("fixture", help="Path to the JSON artifact")

    check_action_parser = subparsers.add_parser(
        "check-action",
        help="Check one action against a fixture's projection domain (closed mediated-action universe)",
    )
    check_action_parser.add_argument("fixture", help="Path to the JSON artifact")
    check_action_parser.add_argument("action", help="Path to a JSON action file")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        result, passed = verify_fixture(args.fixture)
        print(json.dumps(result, sort_keys=True))
        return 0 if passed else 1

    if args.command == "project":
        result, passed = project_fixture(args.fixture)
        print(json.dumps(result, sort_keys=True))
        return 0 if passed else 1

    if args.command == "check-action":
        result, passed = check_action_cli(args.fixture, args.action)
        print(json.dumps(result, sort_keys=True))
        return 0 if passed else 1

    parser.error(f"unknown command: {args.command}")
    return 2  # pragma: no cover - argparse.error() exits before this


if __name__ == "__main__":
    import sys

    sys.exit(main())
