"""`authcontract verify <fixture>` — CLI surface over `verify_artifact` (R01/AC-I06).

MVP-alpha scope only: parses one bounded synthetic JSON artifact and reports
a deterministic PASS/REFUSED result. Does not implement projection, VEIP
binding, AEP reconstruction, or production provenance verification — those
are later gates.

Same fail-closed discipline as `digest.py`/`facts.py`: an unrecognised
top-level shape is a refusal, never a silently-ignored field that could
produce a false PASS.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from .digest import ContractDigestMismatch, DigestScopeError, verify_artifact

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


def verify_fixture(path: str) -> tuple[dict[str, Any], bool]:
    """Verify one fixture file. Returns (result, passed)."""
    fixture_name = os.path.basename(path)

    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError as exc:
        return _refused("AC_IO_ERROR", f"cannot read fixture: {exc}", fixture_name), False

    try:
        artifact = json.loads(raw)
    except json.JSONDecodeError as exc:
        return _refused("AC_INVALID_JSON", f"fixture is not valid JSON: {exc}", fixture_name), False

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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="authcontract")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="Verify one bounded synthetic JSON AuthContract artifact"
    )
    verify_parser.add_argument("fixture", help="Path to the JSON artifact")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        result, passed = verify_fixture(args.fixture)
        print(json.dumps(result, sort_keys=True))
        return 0 if passed else 1

    parser.error(f"unknown command: {args.command}")
    return 2  # pragma: no cover - argparse.error() exits before this


if __name__ == "__main__":
    import sys

    sys.exit(main())
