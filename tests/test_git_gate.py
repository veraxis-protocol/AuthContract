"""AC-018 / C-07 / D-006 — Git merge-result admissibility gate.

Covers AC-018 section F (a reproducible synthetic stale-base/merge-
composition test against a temporary Git repository, never the live main
branch) and section G (the conclusion-mapping test matrix). Test numbering
in comments matches AC-018's own numbering so the return record's
expected/observed matrix can cite these directly.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from authcontract.cli import git_gate_cli, main
from authcontract.git_gate import (
    GitError,
    GitFail,
    GitUnresolved,
    MergeResultUnverified,
    NeutralConclusion,
    adjudicate,
)


def _git(*args: str, cwd: str) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert proc.returncode == 0, f"git {args} failed: {proc.stderr}"
    return proc.stdout.strip()


def _init_repo(path: str) -> None:
    _git("init", "-q", cwd=path)
    _git("symbolic-ref", "HEAD", "refs/heads/main", cwd=path)
    _git("config", "user.email", "test@example.com", cwd=path)
    _git("config", "user.name", "AC-018 Test", cwd=path)


def _commit(path: str, message: str, filename: str, content: str) -> str:
    (Path(path) / filename).write_text(content)
    _git("add", filename, cwd=path)
    _git("commit", "-q", "-m", message, cwd=path)
    return _git("rev-parse", "HEAD", cwd=path)


def _context(
    conclusion,
    base_sha,
    head_sha,
    merge_result_sha,
    evaluated_sha=None,
    base_ref="main",
    repository="veraxis-protocol/AuthContract",
    event_type="pull_request",
):
    return {
        "conclusion": conclusion,
        "repository": repository,
        "event_type": event_type,
        "base_ref": base_ref,
        "expected_base_sha": base_sha,
        "head_sha": head_sha,
        "merge_result_sha": merge_result_sha,
        "evaluated_sha": evaluated_sha if evaluated_sha is not None else merge_result_sha,
    }


@pytest.fixture
def verified_scenario(tmp_path):
    """base B (current tip of main) + head H, correctly merged as B+H.
    Everything an admissible PASS context needs, ready for `conclusion` to
    be swapped per-test in the G matrix."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(str(repo))
    sha_base = _commit(str(repo), "base", "base.txt", "base")

    _git("checkout", "-b", "pr-head", cwd=str(repo))
    sha_head = _commit(str(repo), "head", "head.txt", "head")

    _git("checkout", "-b", "merge-test", "main", cwd=str(repo))
    _git("merge", "--no-ff", "pr-head", "-m", "merge H into base", cwd=str(repo))
    sha_merge = _git("rev-parse", "HEAD", cwd=str(repo))

    _git("checkout", "main", cwd=str(repo))

    return {
        "repo_path": str(repo),
        "base_sha": sha_base,
        "head_sha": sha_head,
        "merge_result_sha": sha_merge,
    }


# ===================================================================
# Section F — reproducible synthetic stale-base / merge-composition test
# ===================================================================

def test_f_stale_base_merge_result_is_refused(tmp_path):
    """F.1-6: base A; PR head H from A; merge result for A+H; base
    independently advances to B; the A-based merge result presented while
    current base is B MUST refuse with GIT_MERGE_RESULT_UNVERIFIED."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(str(repo))

    # F.1 create base A
    sha_a = _commit(str(repo), "base A", "base.txt", "A")

    # F.2 create PR head H from A
    _git("checkout", "-b", "pr-head", cwd=str(repo))
    sha_h = _commit(str(repo), "head H", "head.txt", "H")

    # F.3 construct/evaluate a merge result for A+H (on a side branch —
    # never touches main directly, so main is free to advance independently)
    _git("checkout", "-b", "merge-test-AH", "main", cwd=str(repo))
    _git("merge", "--no-ff", "pr-head", "-m", "merge H into A", cwd=str(repo))
    sha_merge_ah = _git("rev-parse", "HEAD", cwd=str(repo))

    # F.4 advance base to B independently
    _git("checkout", "main", cwd=str(repo))
    sha_b = _commit(str(repo), "base B", "base2.txt", "B")

    # F.5 present the stale A-based merge result while current base is B
    context = _context("PASS", base_sha=sha_a, head_sha=sha_h, merge_result_sha=sha_merge_ah)

    # F.6 gate MUST REFUSE with GIT_MERGE_RESULT_UNVERIFIED
    with pytest.raises(MergeResultUnverified) as exc:
        adjudicate(context, str(repo))
    assert exc.value.code == "GIT_MERGE_RESULT_UNVERIFIED"
    assert exc.value.context["current_base_sha"] == sha_b
    assert exc.value.context["base_sha"] == sha_a


def test_f_correctly_reconstructed_merge_against_current_base_passes(tmp_path):
    """Continuation of the same repository: prove a correctly reconstructed
    merge result against the CURRENT base (B) proceeds when conclusion is
    PASS — the positive control for the stale-base negative above."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(str(repo))
    sha_a = _commit(str(repo), "base A", "base.txt", "A")
    _git("checkout", "-b", "pr-head", cwd=str(repo))
    sha_h = _commit(str(repo), "head H", "head.txt", "H")
    _git("checkout", "-b", "merge-test-AH", "main", cwd=str(repo))
    _git("merge", "--no-ff", "pr-head", "-m", "merge H into A", cwd=str(repo))
    _git("checkout", "main", cwd=str(repo))
    sha_b = _commit(str(repo), "base B", "base2.txt", "B")

    # Correctly reconstructed merge result against the CURRENT base B.
    _git("checkout", "-b", "merge-test-BH", "main", cwd=str(repo))
    _git("merge", "--no-ff", "pr-head", "-m", "merge H into B", cwd=str(repo))
    sha_merge_bh = _git("rev-parse", "HEAD", cwd=str(repo))
    _git("checkout", "main", cwd=str(repo))

    context = _context("PASS", base_sha=sha_b, head_sha=sha_h, merge_result_sha=sha_merge_bh)
    result = adjudicate(context, str(repo))
    assert result["status"] == "PASS"
    assert result["reason_code"] == "OK"
    assert result["current_base_sha"] == sha_b


# ===================================================================
# Section G — conclusion-mapping test matrix
# ===================================================================

def test_g1_pass_with_verified_merge_result_succeeds(verified_scenario):
    context = _context("PASS", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    result = adjudicate(context, verified_scenario["repo_path"])
    assert result["status"] == "PASS"
    assert result["reason_code"] == "OK"


def test_g2_fail_with_verified_merge_result_is_refused(verified_scenario):
    context = _context("FAIL", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    with pytest.raises(GitFail) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_FAIL"


def test_g3_unresolved_with_verified_merge_result_is_refused(verified_scenario):
    context = _context("UNRESOLVED", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    with pytest.raises(GitUnresolved) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_UNRESOLVED"


def test_g4_error_with_verified_merge_result_is_refused(verified_scenario):
    context = _context("ERROR", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    with pytest.raises(GitError) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_ERROR"


def test_g5_neutral_is_refused(verified_scenario):
    context = _context("NEUTRAL", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    with pytest.raises(NeutralConclusion) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_NEUTRAL_CONCLUSION"


def test_g6_skipped_is_refused(verified_scenario):
    context = _context("SKIPPED", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    with pytest.raises(NeutralConclusion) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_NEUTRAL_CONCLUSION"


def test_g7_missing_conclusion_is_refused(verified_scenario):
    context = _context(None, **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    del context["conclusion"]
    with pytest.raises(NeutralConclusion) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_NEUTRAL_CONCLUSION"


def test_g8_unknown_conclusion_is_refused(verified_scenario):
    context = _context("BOGUS_CONCLUSION", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    with pytest.raises(NeutralConclusion) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_NEUTRAL_CONCLUSION"


def test_g8b_cancelled_is_refused(verified_scenario):
    context = _context("CANCELLED", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    with pytest.raises(NeutralConclusion) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_NEUTRAL_CONCLUSION"


def test_g9_evaluated_sha_is_isolated_head_only_is_refused(verified_scenario):
    """merge_result_sha is a genuinely valid merge, but evaluated_sha claims
    only the PR head was actually tested — must still refuse."""
    context = _context(
        "PASS",
        base_sha=verified_scenario["base_sha"],
        head_sha=verified_scenario["head_sha"],
        merge_result_sha=verified_scenario["merge_result_sha"],
        evaluated_sha=verified_scenario["head_sha"],
    )
    with pytest.raises(MergeResultUnverified) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_MERGE_RESULT_UNVERIFIED"


def test_g10_stale_base_is_refused(tmp_path):
    """Standalone G10 construction (independent of the shared F scenario
    above), mirroring the exact stale-base setup."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(str(repo))
    sha_a = _commit(str(repo), "base A", "base.txt", "A")
    _git("checkout", "-b", "pr-head", cwd=str(repo))
    sha_h = _commit(str(repo), "head H", "head.txt", "H")
    _git("checkout", "-b", "merge-test", "main", cwd=str(repo))
    _git("merge", "--no-ff", "pr-head", "-m", "merge", cwd=str(repo))
    sha_merge = _git("rev-parse", "HEAD", cwd=str(repo))
    _git("checkout", "main", cwd=str(repo))
    _commit(str(repo), "base advances", "base2.txt", "advanced")  # main moves past A

    context = _context("PASS", base_sha=sha_a, head_sha=sha_h, merge_result_sha=sha_merge)
    with pytest.raises(MergeResultUnverified) as exc:
        adjudicate(context, str(repo))
    assert exc.value.code == "GIT_MERGE_RESULT_UNVERIFIED"


def test_g11_merge_result_missing_base_ancestry_is_refused(tmp_path):
    """merge_result_sha exists but is a totally disconnected (orphan)
    history — does not descend from the current base at all."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(str(repo))
    sha_base = _commit(str(repo), "base", "base.txt", "base")
    _git("checkout", "-b", "pr-head", cwd=str(repo))
    sha_head = _commit(str(repo), "head", "head.txt", "head")

    _git("checkout", "--orphan", "disconnected", cwd=str(repo))
    _git("rm", "-rf", "--cached", ".", cwd=str(repo))
    for leftover in ("base.txt", "head.txt"):
        (Path(repo) / leftover).unlink(missing_ok=True)
    sha_orphan = _commit(str(repo), "disconnected history", "other.txt", "unrelated")
    _git("checkout", "-f", "main", cwd=str(repo))

    context = _context("PASS", base_sha=sha_base, head_sha=sha_head, merge_result_sha=sha_orphan)
    with pytest.raises(MergeResultUnverified) as exc:
        adjudicate(context, str(repo))
    assert exc.value.code == "GIT_MERGE_RESULT_UNVERIFIED"
    assert "current base" in str(exc.value)


def test_g12_merge_result_missing_head_ancestry_is_refused(verified_scenario):
    """merge_result_sha is a real, known commit descended from the current
    base — but never actually incorporates the PR head."""
    context = _context(
        "PASS",
        base_sha=verified_scenario["base_sha"],
        head_sha=verified_scenario["head_sha"],
        merge_result_sha=verified_scenario["base_sha"],  # base masquerading as the merge result
    )
    with pytest.raises(MergeResultUnverified) as exc:
        adjudicate(context, verified_scenario["repo_path"])
    assert exc.value.code == "GIT_MERGE_RESULT_UNVERIFIED"
    assert "PR head" in str(exc.value)


def test_g13_repeated_adjudication_is_deterministic(verified_scenario):
    context = _context("PASS", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    r1 = adjudicate(context, verified_scenario["repo_path"])
    r2 = adjudicate(context, verified_scenario["repo_path"])
    assert r1 == r2


def test_g13b_repeated_cli_invocation_identical_stdout(verified_scenario, tmp_path, capsys):
    context = _context("PASS", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    context_file = tmp_path / "context.json"
    context_file.write_text(json.dumps(context))

    main(["git-gate", str(context_file), "--repo", verified_scenario["repo_path"]])
    out1 = capsys.readouterr().out
    main(["git-gate", str(context_file), "--repo", verified_scenario["repo_path"]])
    out2 = capsys.readouterr().out
    assert out1 == out2


# ------------------------------------------------------------- required extras

def test_missing_context_field_is_unverified(verified_scenario):
    context = _context("PASS", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    del context["repository"]
    with pytest.raises(MergeResultUnverified):
        adjudicate(context, verified_scenario["repo_path"])


def test_unresolvable_base_ref_is_unverified(verified_scenario):
    context = _context(
        "PASS",
        base_sha=verified_scenario["base_sha"],
        head_sha=verified_scenario["head_sha"],
        merge_result_sha=verified_scenario["merge_result_sha"],
        base_ref="does-not-exist",
    )
    with pytest.raises(MergeResultUnverified):
        adjudicate(context, verified_scenario["repo_path"])


def test_no_continue_on_error_bypass_in_cli_exit_code(verified_scenario, tmp_path):
    """A blocking conclusion must always translate to a non-zero process
    exit — the property that makes it usable as a required-check gate."""
    context = _context("FAIL", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    context_file = tmp_path / "context.json"
    context_file.write_text(json.dumps(context))

    exit_code = main(["git-gate", str(context_file), "--repo", verified_scenario["repo_path"]])
    assert exit_code != 0


# ============================================================= CLI-level tests

def test_git_gate_cli_pass(verified_scenario, tmp_path):
    context = _context("PASS", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    context_file = tmp_path / "context.json"
    context_file.write_text(json.dumps(context))

    result, passed = git_gate_cli(str(context_file), verified_scenario["repo_path"])
    assert passed is True
    assert result["status"] == "PASS"
    assert result["current_base_sha"] == verified_scenario["base_sha"]


def test_git_gate_cli_fail_nonzero_exit(verified_scenario, tmp_path, capsys):
    context = _context("FAIL", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    context_file = tmp_path / "context.json"
    context_file.write_text(json.dumps(context))

    code = main(["git-gate", str(context_file), "--repo", verified_scenario["repo_path"]])
    assert code != 0
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "GIT_FAIL"


def test_git_gate_cli_missing_context_file_is_io_error(verified_scenario, capsys):
    code = main(["git-gate", "/nonexistent/context.json", "--repo", verified_scenario["repo_path"]])
    assert code != 0
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_IO_ERROR"


def test_git_gate_cli_invalid_json_context(tmp_path, verified_scenario, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    code = main(["git-gate", str(bad), "--repo", verified_scenario["repo_path"]])
    assert code != 0
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_INVALID_JSON"


def test_git_gate_module_invocation_end_to_end(verified_scenario, tmp_path):
    context = _context("PASS", **{k: verified_scenario[k] for k in ("base_sha", "head_sha", "merge_result_sha")})
    context_file = tmp_path / "context.json"
    context_file.write_text(json.dumps(context))

    repo_root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "git-gate", str(context_file), "--repo", verified_scenario["repo_path"]],
        cwd=repo_root, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS"
