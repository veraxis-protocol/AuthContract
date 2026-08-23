"""AC-016 CLI conformance: `authcontract project <fixture>` and
`authcontract check-action <fixture> <action-json>`.

Mirrors tests/test_cli.py's style. Does not modify test_cli.py or its
fixtures — `authcontract verify <fixture>` is asserted unbroken here too.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from authcontract.cli import check_action_cli, main, project_fixture, verify_fixture

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
ACTIONS = FIXTURES / "actions"

SPECIMEN = FIXTURES / "banking_payment_specimen.json"


# ------------------------------------------------------------------ project

def test_project_valid_specimen_passes():
    result, passed = project_fixture(str(SPECIMEN))
    assert passed is True
    assert result["status"] == "PASS"
    assert result["reason_code"] == "OK"
    assert result["contract_digest"].startswith("sha256:")
    assert result["projection_digest"].startswith("sha256:")
    assert result["activation_state"] == "ACTIVE"
    assert "domain" in result


def test_project_is_deterministic_repeated_call():
    r1, _ = project_fixture(str(SPECIMEN))
    r2, _ = project_fixture(str(SPECIMEN))
    assert r1 == r2


def test_project_cli_repeated_invocation_identical_stdout(capsys):
    main(["project", str(SPECIMEN)])
    out1 = capsys.readouterr().out
    main(["project", str(SPECIMEN)])
    out2 = capsys.readouterr().out
    assert out1 == out2


def test_project_contract_mutation_changes_digests():
    r1, _ = project_fixture(str(SPECIMEN))
    r2, _ = project_fixture(str(FIXTURES / "banking_payment_specimen_contract_mutated.json"))
    assert r1["contract_digest"] != r2["contract_digest"]
    assert r1["projection_digest"] != r2["projection_digest"]


def test_project_admission_only_mutation_does_not_change_digests():
    r1, _ = project_fixture(str(SPECIMEN))
    r2, _ = project_fixture(str(FIXTURES / "banking_payment_specimen_admission_mutated.json"))
    assert r1["contract_digest"] == r2["contract_digest"]
    assert r1["projection_digest"] == r2["projection_digest"]


def test_project_on_pre_ac016_fixture_is_domain_escape():
    """AC-015's `valid.json` has no projection_domain — must refuse, not
    silently pass through a projection with no domain."""
    result, passed = project_fixture(str(FIXTURES / "valid.json"))
    assert passed is False
    assert result["reason_code"] == "RUN_DOMAIN_ESCAPE"


def test_project_overlapping_specimen_is_a_distinct_active_contract():
    """`banking_payment_specimen_overlapping.json` is a second, independently
    ACTIVE contract that also declares `send_payment` — the fixture used by
    test_projection.py's CONTRACT_SCOPE_CONFLICT coverage. Asserted here so
    the committed file itself is exercised via the CLI path, not just an
    in-memory equivalent."""
    r1, passed1 = project_fixture(str(SPECIMEN))
    r2, passed2 = project_fixture(str(FIXTURES / "banking_payment_specimen_overlapping.json"))
    assert passed1 and passed2
    assert r1["contract_digest"] != r2["contract_digest"]
    assert r1["activation_state"] == r2["activation_state"] == "ACTIVE"
    assert "send_payment" in r2["domain"]["actions"]


def test_project_missing_file_is_io_error(capsys):
    code = main(["project", str(FIXTURES / "does_not_exist.json")])
    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_IO_ERROR"


def test_project_module_invocation_end_to_end():
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "project", str(SPECIMEN)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS"


# -------------------------------------------------------------- check-action

CHECK_ACTION_MATRIX = [
    ("send_payment_valid.json", "PASS", "OK", 0),
    ("send_payment_unknown_action_type.json", "REFUSED", "RUN_UNCLASSIFIED_ACTION", 1),
    ("send_payment_unknown_parameter.json", "REFUSED", "RUN_DOMAIN_ESCAPE", 1),
    ("send_payment_missing_required_parameter.json", "REFUSED", "RUN_DOMAIN_ESCAPE", 1),
    ("send_payment_lossy_value.json", "REFUSED", "RUN_DOMAIN_ESCAPE", 1),
    ("send_payment_out_of_enum_value.json", "REFUSED", "RUN_DOMAIN_ESCAPE", 1),
]


@pytest.mark.parametrize("action_file,status,reason_code,exit_code", CHECK_ACTION_MATRIX)
def test_check_action_matrix_via_function(action_file, status, reason_code, exit_code):
    result, passed = check_action_cli(str(SPECIMEN), str(ACTIONS / action_file))
    assert result["status"] == status
    assert result["reason_code"] == reason_code
    assert passed == (exit_code == 0)


@pytest.mark.parametrize("action_file,status,reason_code,exit_code", CHECK_ACTION_MATRIX)
def test_check_action_matrix_via_main_exit_code(action_file, status, reason_code, exit_code, capsys):
    code = main(["check-action", str(SPECIMEN), str(ACTIONS / action_file)])
    assert code == exit_code
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == status
    assert result["reason_code"] == reason_code


def test_check_action_repeated_call_is_deterministic():
    r1, _ = check_action_cli(str(SPECIMEN), str(ACTIONS / "send_payment_valid.json"))
    r2, _ = check_action_cli(str(SPECIMEN), str(ACTIONS / "send_payment_valid.json"))
    assert r1 == r2


def test_check_action_against_suspended_fixture_is_refused():
    """AC-017 F1 correction: this test previously asserted PASS here, on the
    theory that check_action only type-checks the action and activation
    enforcement was select_matching_projection's job alone. Independent
    review established that reasoning as a false-green path — the public
    check-action CLI must never return PASS for a SUSPENDED/REVOKED
    contract, since nothing else in the single-fixture CLI path enforces
    activation. check_action itself now refuses unless activation_state ==
    "ACTIVE"; see test_projection.py's F1 coverage for the Python-level
    matrix (ACTIVE/SUSPENDED/REVOKED/unknown)."""
    result, passed = check_action_cli(
        str(FIXTURES / "banking_payment_specimen_suspended.json"),
        str(ACTIONS / "send_payment_valid.json"),
    )
    assert passed is False
    assert result["status"] == "REFUSED"
    assert result["reason_code"] == "RUN_INACTIVE_CONTRACT"


def test_check_action_missing_action_file_is_io_error(capsys):
    code = main(["check-action", str(SPECIMEN), str(ACTIONS / "does_not_exist.json")])
    assert code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_IO_ERROR"


def test_check_action_module_invocation_end_to_end():
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "check-action",
         str(SPECIMEN), str(ACTIONS / "send_payment_valid.json")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS"
    assert result["action_type"] == "send_payment"


def test_check_action_module_invocation_nonzero_on_refusal():
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "check-action",
         str(SPECIMEN), str(ACTIONS / "send_payment_unknown_action_type.json")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert proc.returncode != 0
    result = json.loads(proc.stdout)
    assert result["status"] == "REFUSED"


# ------------------------------------------------- `verify` remains unbroken

def test_verify_still_works_unmodified():
    result, passed = verify_fixture(str(FIXTURES / "valid.json"))
    assert passed is True
    assert result["status"] == "PASS"


def test_verify_cli_still_works_unmodified(capsys):
    code = main(["verify", str(FIXTURES / "valid.json")])
    assert code == 0
