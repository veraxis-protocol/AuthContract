"""`authcontract verify|project|check-action|git-gate|run-specimen|
verify-receipt` — the AuthContract developer CLI.

Checks whether a rule is supported by its source, whether an action is
covered by the rule, whether a PR's merge result was actually what got
tested, and whether a runtime decision plus its proof receipt hold up to
independent re-verification. Every command prints one deterministic JSON
object and exits non-zero on any refusal — never a silently-ignored field
that could produce a false PASS.

Bounded reference implementation, tested for one synthetic banking
specimen. Does not implement production provenance verification, real
payment execution, or general correctness beyond that specimen.

Underneath: `verify`/`project`/`check-action` cover canonical rule
identity (R01/AC-I06) and projection/action-closure (AC-016); `git-gate`
covers Git merge-result admissibility (AC-018/C-07/D-006); `run-specimen`/
`verify-receipt` cover the bounded runtime decision and AEP-style receipt
(AC-019/C-08, amended by AC-020's verified assertion binding and AC-020A's
declaration-shape/admission-binding closure). See docs/DEVELOPER-LANGUAGE.md
for why this docstring leads with plain language.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any

from .digest import ContractDigestMismatch, DigestScopeError, verify_artifact
from .git_gate import GitGateRefusal, adjudicate
from .projection import (
    InactiveContract,
    ProjectionDomainError,
    UnclassifiedAction,
    check_action,
    project,
    projection_digest,
    projection_to_dict,
)
from .veip import ALLOWED_EXECUTION_RESULTS, run_specimen, verify_receipt

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
    except (InactiveContract, UnclassifiedAction, ProjectionDomainError) as exc:
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


_GIT_GATE_FIELDS = (
    "conclusion",
    "repository",
    "event_type",
    "base_ref",
    "base_sha",
    "current_base_sha",
    "head_sha",
    "merge_result_sha",
    "evaluated_sha",
)


def _git_gate_refused(code: str, message: str, context_name: str) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "REFUSED", "reason_code": code, "message": message}
    for field in _GIT_GATE_FIELDS:
        result[field] = None
    result["context_file"] = context_name
    return result


def git_gate_cli(context_path: str, repo_path: str) -> tuple[dict[str, Any], bool]:
    """`authcontract git-gate <context.json> [--repo <path>]`. Returns
    (result, passed). Adjudicates an AuthContract evaluation conclusion
    against Git merge composition verified live in `repo_path` — never
    trusts a caller-asserted "verified" claim in the context file itself.
    """
    context_name = os.path.basename(context_path)

    raw, error = _load_json_file(context_path, "context")
    if error is not None:
        code, message = error
        return _git_gate_refused(code, message, context_name), False

    if not isinstance(raw, dict):
        return _git_gate_refused(
            "GIT_MERGE_RESULT_UNVERIFIED", "context must be a JSON object", context_name
        ), False

    try:
        result = adjudicate(raw, repo_path)
    except GitGateRefusal as exc:
        refused: dict[str, Any] = {
            "status": "REFUSED",
            "reason_code": exc.code,
            "message": str(exc),
        }
        refused.update(exc.context)
        refused["context_file"] = context_name
        return refused, False
    except Exception as exc:  # fail closed on anything this CLI didn't anticipate
        return _git_gate_refused("AC_INTERNAL_ERROR", str(exc), context_name), False

    result["context_file"] = context_name
    return result, True


def _labeled_refused(code: str, message: str, **labels: str) -> dict[str, Any]:
    result: dict[str, Any] = {"status": "REFUSED", "reason_code": code, "message": message}
    result.update(labels)
    return result


def run_specimen_cli(
    artifact_path: str, action_path: str, facts_path: str, execution_result: str
) -> tuple[dict[str, Any], bool]:
    """`authcontract run-specimen <artifact> <action> <facts> --execution-result <...>`.
    Returns (result, passed). Composes verify -> project -> check_action ->
    fact admission -> receipt issuance; never converts an upstream refusal
    into ALLOW."""
    labels = {
        "artifact": os.path.basename(artifact_path),
        "action_file": os.path.basename(action_path),
        "facts_file": os.path.basename(facts_path),
    }

    artifact, error = _load_json_file(artifact_path, "artifact")
    if error is not None:
        code, message = error
        return _labeled_refused(code, message, **labels), False
    structure_error = _validate_structure(artifact)
    if structure_error is not None:
        return _labeled_refused("AC_INVALID_STRUCTURE", structure_error, **labels), False

    action, error = _load_json_file(action_path, "action")
    if error is not None:
        code, message = error
        return _labeled_refused(code, message, **labels), False

    facts, error = _load_json_file(facts_path, "facts")
    if error is not None:
        code, message = error
        return _labeled_refused(code, message, **labels), False

    try:
        result = run_specimen(artifact, action, facts, execution_result=execution_result)
    except Exception as exc:  # fail closed on anything this CLI didn't anticipate
        return _labeled_refused("AC_INTERNAL_ERROR", str(exc), **labels), False

    if result.decision != "ALLOW":
        return _labeled_refused(result.reason_code, result.message or "", **labels), False

    return {
        "status": "PASS",
        "decision": "ALLOW",
        "reason_code": "OK",
        "receipt": result.receipt,
        **labels,
    }, True


def verify_receipt_cli(
    receipt_path: str, artifact_path: str, action_path: str, facts_path: str
) -> tuple[dict[str, Any], bool]:
    """`authcontract verify-receipt <receipt> <artifact> <action> <facts>`.
    Returns (result, passed). Independently recomputes every binding from
    the raw inputs — never trusts a digest merely because it is present in
    the receipt file."""
    labels = {
        "receipt": os.path.basename(receipt_path),
        "artifact": os.path.basename(artifact_path),
        "action_file": os.path.basename(action_path),
        "facts_file": os.path.basename(facts_path),
    }

    receipt, error = _load_json_file(receipt_path, "receipt")
    if error is not None:
        code, message = error
        return _labeled_refused(code, message, **labels), False

    artifact, error = _load_json_file(artifact_path, "artifact")
    if error is not None:
        code, message = error
        return _labeled_refused(code, message, **labels), False
    structure_error = _validate_structure(artifact)
    if structure_error is not None:
        return _labeled_refused("AC_INVALID_STRUCTURE", structure_error, **labels), False

    action, error = _load_json_file(action_path, "action")
    if error is not None:
        code, message = error
        return _labeled_refused(code, message, **labels), False

    facts, error = _load_json_file(facts_path, "facts")
    if error is not None:
        code, message = error
        return _labeled_refused(code, message, **labels), False

    try:
        result = verify_receipt(receipt, artifact, action, facts)
    except Exception as exc:  # fail closed on anything this CLI didn't anticipate
        return _labeled_refused("AC_INTERNAL_ERROR", str(exc), **labels), False

    if result.status != "PASS":
        return _labeled_refused(result.reason_code, result.message or "", **labels), False

    return {"status": "PASS", "reason_code": "OK", **labels}, True


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="authcontract")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="Verify one rule artifact's canonical identity"
    )
    verify_parser.add_argument("fixture", help="Path to the JSON artifact")

    project_parser = subparsers.add_parser(
        "project", help="Project a rule into its declared runtime action domain"
    )
    project_parser.add_argument("fixture", help="Path to the JSON artifact")

    check_action_parser = subparsers.add_parser(
        "check-action",
        help="Check whether an action is covered by a rule's declared action domain",
    )
    check_action_parser.add_argument("fixture", help="Path to the JSON artifact")
    check_action_parser.add_argument("action", help="Path to a JSON action file")

    git_gate_parser = subparsers.add_parser(
        "git-gate",
        help="Check a CI result against the version that would actually merge",
    )
    git_gate_parser.add_argument("context", help="Path to a JSON git-gate context file")
    git_gate_parser.add_argument(
        "--repo",
        default=".",
        help="Path to the Git repository to verify merge composition against (default: current directory)",
    )

    run_specimen_parser = subparsers.add_parser(
        "run-specimen",
        help="Run the rule/fact/action check end to end and issue a proof receipt on PASS",
    )
    run_specimen_parser.add_argument("artifact", help="Path to the JSON artifact")
    run_specimen_parser.add_argument("action", help="Path to a JSON action file")
    run_specimen_parser.add_argument("facts", help="Path to a JSON facts/evidence bundle")
    run_specimen_parser.add_argument(
        "--execution-result",
        required=True,
        choices=sorted(ALLOWED_EXECUTION_RESULTS),
        help="Bounded synthetic execution outcome to bind into the receipt",
    )

    verify_receipt_parser = subparsers.add_parser(
        "verify-receipt",
        help="Re-run the evidence: recompute a receipt from source and compare",
    )
    verify_receipt_parser.add_argument("receipt", help="Path to a JSON receipt")
    verify_receipt_parser.add_argument("artifact", help="Path to the JSON artifact")
    verify_receipt_parser.add_argument("action", help="Path to a JSON action file")
    verify_receipt_parser.add_argument("facts", help="Path to a JSON facts/evidence bundle")

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

    if args.command == "git-gate":
        result, passed = git_gate_cli(args.context, args.repo)
        print(json.dumps(result, sort_keys=True))
        return 0 if passed else 1

    if args.command == "run-specimen":
        result, passed = run_specimen_cli(args.artifact, args.action, args.facts, args.execution_result)
        print(json.dumps(result, sort_keys=True))
        return 0 if passed else 1

    if args.command == "verify-receipt":
        result, passed = verify_receipt_cli(args.receipt, args.artifact, args.action, args.facts)
        print(json.dumps(result, sort_keys=True))
        return 0 if passed else 1

    parser.error(f"unknown command: {args.command}")
    return 2  # pragma: no cover - argparse.error() exits before this


if __name__ == "__main__":
    import sys

    sys.exit(main())
