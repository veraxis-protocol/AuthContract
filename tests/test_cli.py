"""`authcontract verify <fixture>` — AC-015 CLI conformance.

Covers exit codes, JSON result shape, deterministic repeated output, and the
required fixture matrix (PASS, sibling digest mismatch, self-referential
digest-scope violation, malformed/unsupported structure, cross-object
substitution).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from authcontract.cli import main, verify_fixture

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

REQUIRED_KEYS = {"status", "reason_code", "fixture"}

FIXTURE_MATRIX = [
    # (fixture filename, expected status, expected reason_code, expected exit code)
    ("valid.json", "PASS", "OK", 0),
    ("sibling_digest_mismatch.json", "REFUSED", "AC_DIGEST", 1),
    ("self_referential.json", "REFUSED", "AC_DIGEST_SCOPE", 1),
    ("malformed.json", "REFUSED", "AC_INVALID_STRUCTURE", 1),
    ("cross_object_substitution.json", "REFUSED", "AC_DIGEST", 1),
]


# --------------------------------------------------------------- fixture matrix

@pytest.mark.parametrize("name,status,reason_code,exit_code", FIXTURE_MATRIX)
def test_fixture_matrix_via_verify_fixture(name, status, reason_code, exit_code):
    result, passed = verify_fixture(str(FIXTURES / name))
    assert result["status"] == status
    assert result["reason_code"] == reason_code
    assert result["fixture"] == name
    assert passed == (exit_code == 0)


@pytest.mark.parametrize("name,status,reason_code,exit_code", FIXTURE_MATRIX)
def test_fixture_matrix_via_main_exit_code(name, status, reason_code, exit_code, capsys):
    code = main(["verify", str(FIXTURES / name)])
    assert code == exit_code

    out = capsys.readouterr().out.strip()
    result = json.loads(out)
    assert result["status"] == status
    assert result["reason_code"] == reason_code
    assert result["fixture"] == name


def test_valid_fixture_reports_contract_digest():
    result, passed = verify_fixture(str(FIXTURES / "valid.json"))
    assert passed is True
    assert result["contract_digest"].startswith("sha256:")


def test_refused_result_has_no_contract_digest_key():
    result, passed = verify_fixture(str(FIXTURES / "malformed.json"))
    assert passed is False
    assert "contract_digest" not in result


# ------------------------------------------------------------------ result shape

@pytest.mark.parametrize("name,_status,_reason_code,_exit_code", FIXTURE_MATRIX)
def test_result_has_required_keys(name, _status, _reason_code, _exit_code):
    result, _passed = verify_fixture(str(FIXTURES / name))
    assert REQUIRED_KEYS <= result.keys()


def test_result_excludes_timestamps_and_random_ids():
    """D: the deterministic result must not carry timestamps/random IDs."""
    for name, *_ in FIXTURE_MATRIX:
        result, _passed = verify_fixture(str(FIXTURES / name))
        forbidden = {"timestamp", "id", "run_id", "nonce", "generated_at"}
        assert forbidden.isdisjoint(result.keys())


# ------------------------------------------------------------- determinism

@pytest.mark.parametrize("name,_status,_reason_code,_exit_code", FIXTURE_MATRIX)
def test_repeated_verification_is_deterministic(name, _status, _reason_code, _exit_code):
    first, _ = verify_fixture(str(FIXTURES / name))
    second, _ = verify_fixture(str(FIXTURES / name))
    assert first == second


def test_repeated_cli_invocation_produces_identical_stdout(capsys):
    main(["verify", str(FIXTURES / "valid.json")])
    first = capsys.readouterr().out
    main(["verify", str(FIXTURES / "valid.json")])
    second = capsys.readouterr().out
    assert first == second


# --------------------------------------------------------- error/edge handling

def test_missing_file_is_refused_not_crashed(capsys):
    code = main(["verify", str(FIXTURES / "does_not_exist.json")])
    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "REFUSED"
    assert result["reason_code"] == "AC_IO_ERROR"


def test_invalid_json_syntax_is_refused_not_crashed(tmp_path, capsys):
    bad = tmp_path / "not_json.json"
    bad.write_text("{not valid json")
    code = main(["verify", str(bad)])
    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "REFUSED"
    assert result["reason_code"] == "AC_INVALID_JSON"


def test_top_level_list_is_rejected(tmp_path, capsys):
    bad = tmp_path / "list_root.json"
    bad.write_text("[]")
    code = main(["verify", str(bad)])
    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_INVALID_STRUCTURE"


def test_missing_contract_object_is_rejected(tmp_path, capsys):
    bad = tmp_path / "no_contract.json"
    bad.write_text(json.dumps({"admission": {"contract_digest": "sha256:aa"}}))
    code = main(["verify", str(bad)])
    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_INVALID_STRUCTURE"


def test_non_object_sibling_is_rejected(tmp_path, capsys):
    bad = tmp_path / "bad_sibling.json"
    bad.write_text(json.dumps({"contract": {"identity": {"contract_id": "x"}}, "proof": "not-an-object"}))
    code = main(["verify", str(bad)])
    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_INVALID_STRUCTURE"


# --------------------------------------------------- python -m module invocation

def test_module_invocation_matches_verify_fixture():
    """`python -m authcontract verify <fixture>` end-to-end, per requirement A."""
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "verify", str(FIXTURES / "valid.json")],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS"
    assert result["reason_code"] == "OK"


def test_module_invocation_nonzero_exit_on_refusal():
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "verify", str(FIXTURES / "self_referential.json")],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "REFUSED"
