"""Git merge-result admissibility gate. Implements AC-018 / C-07 / D-006.

Consumes an AuthContract evaluation conclusion plus a verified Git
composition context and produces a deterministic PASS/REFUSED result.

D-006, verbatim: PASS maps to success; FAIL/UNRESOLVED/ERROR are
merge-blocking; required AuthContract checks never use neutral/skipped for
blocking states; final merge composition must be adjudicated, not only an
isolated PR head.

This module never trusts a caller-supplied claim that a merge result is
verified. `current_base_sha` is always re-resolved from live Git ref state
(a local checkout in the live GitHub Actions path; a temporary synthetic
repository in tests) at adjudication time, and `merge_result_sha` must
provably contain both the current base and the PR head as ancestors before
any conclusion mapping is applied. An isolated PR-head evaluation, a stale
expected base, or a merge result that does not actually bind the current
base/head is refused with GIT_MERGE_RESULT_UNVERIFIED before conclusion
mapping is ever considered.

Bounded GitHub-first MVP mechanism (D-011): this establishes only a TESTED
implementation for this repository and synthetic Git histories, not
universal Git-provider correctness or GitHub as a long-term trust root.
"""

from __future__ import annotations

import subprocess
from typing import Any

#: The only AuthContract evaluation conclusions this gate understands as
#: admissible. Anything else (NEUTRAL, SKIPPED, CANCELLED, missing, or any
#: other value) is refused before any Git verification is attempted.
ADMISSIBLE_CONCLUSIONS = frozenset({"PASS", "FAIL", "UNRESOLVED", "ERROR"})

#: Context fields required to attempt Git verification, beyond `conclusion`.
REQUIRED_CONTEXT_FIELDS = (
    "repository",
    "event_type",
    "base_ref",
    "expected_base_sha",
    "head_sha",
    "merge_result_sha",
    "evaluated_sha",
)

_ECHO_FIELDS = (
    "repository",
    "event_type",
    "base_ref",
    "expected_base_sha",
    "head_sha",
    "merge_result_sha",
    "evaluated_sha",
)


class GitGateRefusal(ValueError):
    """Base class for all git-gate refusals. `context` carries whatever of
    the adjudication context was resolved before the refusal fired, for a
    maximally informative REFUSED result — never less than the raw input
    context, and current_base_sha once resolution succeeds."""
    code = "GIT_GATE_REFUSAL"

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        super().__init__(message)
        self.context = context or {}


class NeutralConclusion(GitGateRefusal):
    """GIT_NEUTRAL_CONCLUSION — NEUTRAL/SKIPPED/CANCELLED/missing/unknown
    conclusion. Never becomes a green required check."""
    code = "GIT_NEUTRAL_CONCLUSION"


class MergeResultUnverified(GitGateRefusal):
    """GIT_MERGE_RESULT_UNVERIFIED — the final/test merge composition could
    not be established against the current base and PR head."""
    code = "GIT_MERGE_RESULT_UNVERIFIED"


class GitFail(GitGateRefusal):
    """GIT_FAIL — AuthContract conclusion is FAIL, over a verified merge result."""
    code = "GIT_FAIL"


class GitUnresolved(GitGateRefusal):
    """GIT_UNRESOLVED — AuthContract conclusion is UNRESOLVED, over a verified merge result."""
    code = "GIT_UNRESOLVED"


class GitError(GitGateRefusal):
    """GIT_ERROR — AuthContract conclusion is ERROR, over a verified merge result."""
    code = "GIT_ERROR"


_BLOCKING_CONCLUSION_CLASSES: dict[str, type[GitGateRefusal]] = {
    "FAIL": GitFail,
    "UNRESOLVED": GitUnresolved,
    "ERROR": GitError,
}


class _GitPlumbingError(Exception):
    """Internal: a `git` subprocess invocation failed (non-zero exit)."""


def _git(*args: str, cwd: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise _GitPlumbingError(
            f"git {' '.join(args)} failed in {cwd!r}: {proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def _resolve_current_base_sha(repo_path: str, base_ref: str) -> str | None:
    """Best-effort resolution of the CURRENT tip of `base_ref`, tried in
    order of preference: a freshly-fetched remote-tracking ref (the live
    GitHub Actions path, after `git fetch origin <base_ref>`), then a local
    branch (the synthetic-repo test path), then a raw revision (fallback).
    Never trusts a value the caller supplied — always re-derived from Git
    ref state in `repo_path` at call time.
    """
    for ref in (f"refs/remotes/origin/{base_ref}", f"refs/heads/{base_ref}", base_ref):
        try:
            return _git("rev-parse", "--verify", ref, cwd=repo_path)
        except _GitPlumbingError:
            continue
    return None


def _object_exists(repo_path: str, sha: str) -> bool:
    try:
        _git("cat-file", "-e", sha, cwd=repo_path)
        return True
    except _GitPlumbingError:
        return False


def _is_ancestor(repo_path: str, ancestor_sha: str, descendant_sha: str) -> bool:
    try:
        _git("merge-base", "--is-ancestor", ancestor_sha, descendant_sha, cwd=repo_path)
        return True
    except _GitPlumbingError:
        return False


def adjudicate(context: dict[str, Any], repo_path: str) -> dict[str, Any]:
    """Adjudicate one Git composition context against `repo_path`'s live
    Git object/ref state. Returns the PASS result dict, or raises a
    GitGateRefusal subclass (never both).
    """
    conclusion = context.get("conclusion")

    # Whatever of the context is present is echoed into every refusal,
    # regardless of where adjudication stops — never less informative than
    # the raw input, even on the earliest possible refusal.
    echoed: dict[str, Any] = {"conclusion": conclusion}
    for field in _ECHO_FIELDS:
        echoed[field if field != "expected_base_sha" else "base_sha"] = context.get(field)
    echoed["current_base_sha"] = None

    if conclusion not in ADMISSIBLE_CONCLUSIONS:
        raise NeutralConclusion(
            f"{NeutralConclusion.code}: AuthContract conclusion {conclusion!r} is not "
            "admissible (must be exactly one of PASS, FAIL, UNRESOLVED, ERROR)",
            echoed,
        )

    for field in REQUIRED_CONTEXT_FIELDS:
        value = context.get(field)
        if not value or not isinstance(value, str):
            raise MergeResultUnverified(
                f"{MergeResultUnverified.code}: context field {field!r} is missing or "
                "malformed",
                echoed,
            )

    base_ref = context["base_ref"]
    expected_base_sha = context["expected_base_sha"]
    head_sha = context["head_sha"]
    merge_result_sha = context["merge_result_sha"]
    evaluated_sha = context["evaluated_sha"]

    current_base_sha = _resolve_current_base_sha(repo_path, base_ref)
    if current_base_sha is None:
        raise MergeResultUnverified(
            f"{MergeResultUnverified.code}: cannot resolve current base ref {base_ref!r} "
            "in the repository at adjudication time",
            echoed,
        )
    echoed["current_base_sha"] = current_base_sha

    if expected_base_sha != current_base_sha:
        raise MergeResultUnverified(
            f"{MergeResultUnverified.code}: expected base {expected_base_sha} is stale — "
            f"current base is {current_base_sha}",
            echoed,
        )

    if merge_result_sha == head_sha or evaluated_sha == head_sha:
        raise MergeResultUnverified(
            f"{MergeResultUnverified.code}: evaluated SHA is the isolated PR head, not a "
            "verified merge result — isolated PR-head evaluation is insufficient",
            echoed,
        )

    if not _object_exists(repo_path, merge_result_sha):
        raise MergeResultUnverified(
            f"{MergeResultUnverified.code}: merge_result_sha {merge_result_sha} is not a "
            "known object in the repository",
            echoed,
        )

    if not _is_ancestor(repo_path, current_base_sha, merge_result_sha):
        raise MergeResultUnverified(
            f"{MergeResultUnverified.code}: merge_result_sha does not contain/bind the "
            f"current base {current_base_sha}",
            echoed,
        )

    if not _is_ancestor(repo_path, head_sha, merge_result_sha):
        raise MergeResultUnverified(
            f"{MergeResultUnverified.code}: merge_result_sha does not contain/bind the "
            f"PR head {head_sha}",
            echoed,
        )

    if conclusion == "PASS":
        return {"status": "PASS", "reason_code": "OK", **echoed}

    refusal_cls = _BLOCKING_CONCLUSION_CLASSES[conclusion]
    raise refusal_cls(
        f"{refusal_cls.code}: AuthContract evaluation conclusion is {conclusion} over a "
        "verified merge result",
        echoed,
    )
