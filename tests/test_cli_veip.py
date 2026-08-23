"""AC-019 / C-08, amended by AC-020 — CLI conformance: `authcontract
run-specimen` and `authcontract verify-receipt`. Mirrors the style of
test_cli_projection.py and test_git_gate.py."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from authcontract.cli import main, run_specimen_cli, verify_receipt_cli

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
RUNTIME = FIXTURES / "runtime"

ARTIFACT = FIXTURES / "banking_payment_specimen.json"
SUSPENDED_ARTIFACT = FIXTURES / "banking_payment_specimen_suspended.json"
DUPLICATE_REQUIRED_FACT_ARTIFACT = FIXTURES / "banking_payment_specimen_duplicate_required_fact.json"
BAD_CORROBORATION_REQUIRED_ARTIFACT = FIXTURES / "banking_payment_specimen_bad_corroboration_required.json"
ACTION = FIXTURES / "actions" / "send_payment_valid.json"
UNKNOWN_ACTION = FIXTURES / "actions" / "send_payment_unknown_action_type.json"
DOMAIN_ESCAPE_ACTION = FIXTURES / "actions" / "send_payment_unknown_parameter.json"
FACTS_VALID = RUNTIME / "facts_valid.json"
RECEIPT_VALID = RUNTIME / "receipt_valid.json"


# --------------------------------------------------------------- run-specimen

def test_run_specimen_cli_positive():
    result, passed = run_specimen_cli(str(ARTIFACT), str(ACTION), str(FACTS_VALID), "SIMULATED_SUCCESS")
    assert passed is True
    assert result["status"] == "PASS"
    assert result["decision"] == "ALLOW"
    assert result["receipt"]["decision"] == "ALLOW"


def test_run_specimen_cli_matches_committed_golden_receipt():
    result, passed = run_specimen_cli(str(ARTIFACT), str(ACTION), str(FACTS_VALID), "SIMULATED_SUCCESS")
    assert passed is True
    golden = json.loads(RECEIPT_VALID.read_text())
    assert result["receipt"] == golden


@pytest.mark.parametrize("negative_facts,expected_reason", [
    ("facts_missing_required.json", "VEIP_FACT_BUNDLE_INCOMPLETE"),
    ("facts_self_asserted_prohibited.json", "RUN_FACT_SELF_ASSERTED"),
    ("facts_stale.json", "RUN_FACT_STALE"),
    ("facts_lossy_representation.json", "RUN_FACT_REPRESENTATION"),
    ("facts_future_timestamp.json", "RUN_FACT_FUTURE_TIMESTAMP"),
    ("facts_naive_timestamp.json", "RUN_FACT_TIME_UNVERIFIABLE"),
    # AC-020 D1-D4, D9, D11 at the CLI level.
    ("facts_verified_asserter_mismatch.json", "RUN_FACT_EVIDENCE_MISMATCH"),
    ("facts_verified_value_mismatch.json", "RUN_FACT_EVIDENCE_MISMATCH"),
    ("facts_verified_time_stale_claimed_fresh.json", "RUN_FACT_EVIDENCE_MISMATCH"),
    ("facts_verified_fact_id_mismatch.json", "RUN_FACT_IDENTITY_MISMATCH"),
    ("facts_duplicate_fact_id.json", "VEIP_MALFORMED_INPUT"),
    ("facts_unknown_bundle_field.json", "VEIP_MALFORMED_INPUT"),
    ("facts_unknown_fact_field.json", "VEIP_MALFORMED_INPUT"),
    ("facts_unknown_evidence_field.json", "VEIP_MALFORMED_INPUT"),
])
def test_run_specimen_cli_negative_fact_paths(negative_facts, expected_reason):
    result, passed = run_specimen_cli(
        str(ARTIFACT), str(ACTION), str(RUNTIME / negative_facts), "NOT_EXECUTED"
    )
    assert passed is False
    assert result["status"] == "REFUSED"
    assert result["reason_code"] == expected_reason
    assert "receipt" not in result


def test_run_specimen_cli_inactive_projection():
    result, passed = run_specimen_cli(str(SUSPENDED_ARTIFACT), str(ACTION), str(FACTS_VALID), "NOT_EXECUTED")
    assert passed is False
    assert result["reason_code"] == "RUN_INACTIVE_CONTRACT"


def test_run_specimen_cli_unknown_action():
    result, passed = run_specimen_cli(str(ARTIFACT), str(UNKNOWN_ACTION), str(FACTS_VALID), "NOT_EXECUTED")
    assert passed is False
    assert result["reason_code"] == "RUN_UNCLASSIFIED_ACTION"


def test_run_specimen_cli_domain_escape():
    result, passed = run_specimen_cli(str(ARTIFACT), str(DOMAIN_ESCAPE_ACTION), str(FACTS_VALID), "NOT_EXECUTED")
    assert passed is False
    assert result["reason_code"] == "RUN_DOMAIN_ESCAPE"


def test_run_specimen_cli_duplicate_required_facts_declaration():
    """AC-020 D10, at the CLI level."""
    result, passed = run_specimen_cli(
        str(DUPLICATE_REQUIRED_FACT_ARTIFACT), str(ACTION), str(FACTS_VALID), "NOT_EXECUTED"
    )
    assert passed is False
    assert result["reason_code"] == "VEIP_MALFORMED_INPUT"


def test_run_specimen_cli_non_boolean_corroboration_required():
    """AC-020 D12, at the CLI level."""
    result, passed = run_specimen_cli(
        str(BAD_CORROBORATION_REQUIRED_ARTIFACT), str(ACTION), str(FACTS_VALID), "NOT_EXECUTED"
    )
    assert passed is False
    assert result["reason_code"] == "VEIP_MALFORMED_INPUT"


def test_run_specimen_cli_exit_code_via_main(capsys):
    code = main(["run-specimen", str(ARTIFACT), str(ACTION), str(FACTS_VALID), "--execution-result", "SIMULATED_SUCCESS"])
    assert code == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PASS"


def test_run_specimen_cli_nonzero_exit_on_refusal(capsys):
    code = main(["run-specimen", str(SUSPENDED_ARTIFACT), str(ACTION), str(FACTS_VALID), "--execution-result", "NOT_EXECUTED"])
    assert code != 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "REFUSED"


def test_run_specimen_cli_invalid_execution_result_rejected_by_argparse():
    with pytest.raises(SystemExit):
        main(["run-specimen", str(ARTIFACT), str(ACTION), str(FACTS_VALID), "--execution-result", "REAL_PAYMENT"])


def test_run_specimen_repeated_invocation_identical_stdout(capsys):
    main(["run-specimen", str(ARTIFACT), str(ACTION), str(FACTS_VALID), "--execution-result", "SIMULATED_SUCCESS"])
    out1 = capsys.readouterr().out
    main(["run-specimen", str(ARTIFACT), str(ACTION), str(FACTS_VALID), "--execution-result", "SIMULATED_SUCCESS"])
    out2 = capsys.readouterr().out
    assert out1 == out2


def test_run_specimen_module_invocation_end_to_end():
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "run-specimen", str(ARTIFACT), str(ACTION), str(FACTS_VALID),
         "--execution-result", "SIMULATED_SUCCESS"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["decision"] == "ALLOW"


# --------------------------------------------------------------- verify-receipt

def test_verify_receipt_cli_positive():
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(FACTS_VALID))
    assert passed is True
    assert result["status"] == "PASS"


def test_verify_receipt_cli_exit_code_via_main(capsys):
    code = main(["verify-receipt", str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(FACTS_VALID)])
    assert code == 0


def test_verify_receipt_cli_missing_receipt_file(capsys):
    code = main(["verify-receipt", str(RUNTIME / "does_not_exist.json"), str(ARTIFACT), str(ACTION), str(FACTS_VALID)])
    assert code != 0
    result = json.loads(capsys.readouterr().out)
    assert result["reason_code"] == "AC_IO_ERROR"


# ------------------------------------------------- B8 mutation matrix (CLI)

@pytest.fixture
def tampered_receipt_factory(tmp_path):
    golden = json.loads(RECEIPT_VALID.read_text())

    def _make(**overrides):
        receipt = dict(golden)
        receipt.update(overrides)
        path = tmp_path / "tampered_receipt.json"
        path.write_text(json.dumps(receipt))
        return path

    return _make


@pytest.mark.parametrize("field,bad_value", [
    ("contract_digest", "sha256:" + "0" * 64),
    ("activation_id", "act:tampered:v1"),
    ("projection_digest", "sha256:" + "1" * 64),
    ("runtime_fact_set_digest", "sha256:" + "2" * 64),
    ("exact_action_digest", "sha256:" + "3" * 64),
    ("admission_digest", "sha256:" + "5" * 64),
    ("decision", "DENY"),
    ("execution_result", "NOT_EXECUTED"),
    ("decision_time", "2099-01-01T00:00:00+00:00"),
    ("receipt_digest", "sha256:" + "4" * 64),
])
def test_cli_b8_mutation_matrix(tampered_receipt_factory, field, bad_value):
    """Tests 1-7 of B8 (each bound field, extended with AC-020's
    admission_digest/decision_time) plus receipt_digest itself, at the CLI
    level, via `authcontract verify-receipt`."""
    receipt_path = tampered_receipt_factory(**{field: bad_value})
    result, passed = verify_receipt_cli(str(receipt_path), str(ARTIFACT), str(ACTION), str(FACTS_VALID))
    assert passed is False
    assert result["reason_code"] == "VEIP_RECEIPT_MISMATCH"


def test_cli_b8_missing_receipt_field(tmp_path):
    """B8 test 11."""
    golden = json.loads(RECEIPT_VALID.read_text())
    del golden["decision"]
    path = tmp_path / "missing_field.json"
    path.write_text(json.dumps(golden))
    result, passed = verify_receipt_cli(str(path), str(ARTIFACT), str(ACTION), str(FACTS_VALID))
    assert passed is False
    assert result["reason_code"] == "VEIP_RECEIPT_MALFORMED"


def test_cli_b8_unknown_receipt_field(tmp_path):
    """B8 test 12: fail closed, no silent drop."""
    golden = json.loads(RECEIPT_VALID.read_text())
    golden["not_a_real_field"] = "sneaky"
    path = tmp_path / "unknown_field.json"
    path.write_text(json.dumps(golden))
    result, passed = verify_receipt_cli(str(path), str(ARTIFACT), str(ACTION), str(FACTS_VALID))
    assert passed is False
    assert result["reason_code"] == "VEIP_RECEIPT_MALFORMED"


def test_cli_b8_admitted_fact_value_changed_receipt_unchanged(tmp_path):
    """B8 test 8."""
    facts = json.loads(FACTS_VALID.read_text())
    facts["facts"][0]["raw_value"] = False
    facts["facts"][0]["evidence"]["value"] = False
    facts_path = tmp_path / "mutated_facts.json"
    facts_path.write_text(json.dumps(facts))
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(facts_path))
    assert passed is False


def test_cli_b8_action_parameter_changed_receipt_unchanged(tmp_path):
    """B8 test 9."""
    action = json.loads(ACTION.read_text())
    action["parameters"]["amount"] = "1.23"
    action_path = tmp_path / "mutated_action.json"
    action_path.write_text(json.dumps(action))
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(action_path), str(FACTS_VALID))
    assert passed is False


def test_cli_b8_artifact_activation_changed_receipt_unchanged():
    """B8 test 10."""
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(SUSPENDED_ARTIFACT), str(ACTION), str(FACTS_VALID))
    assert passed is False


def test_cli_b8_repeated_verification_is_deterministic():
    """B8 test 13, at the CLI-function level."""
    r1, p1 = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(FACTS_VALID))
    r2, p2 = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(FACTS_VALID))
    assert p1 is True and p2 is True
    assert r1 == r2


# --------------------------------------------------- AC-020 D5-D8 (CLI level)

def test_cli_d5_verified_asserted_by_changed_receipt_unchanged_refuses(tmp_path):
    facts = json.loads(FACTS_VALID.read_text())
    facts["facts"][0]["asserted_by"] = "TREASURY_APPROVAL_SERVICE_V2"
    facts["facts"][0]["evidence"]["asserted_by"] = "TREASURY_APPROVAL_SERVICE_V2"
    facts_path = tmp_path / "mutated_facts.json"
    facts_path.write_text(json.dumps(facts))
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(facts_path))
    assert passed is False
    assert result["reason_code"] == "VEIP_RECEIPT_MISMATCH"


def test_cli_d6_verified_asserted_at_changed_receipt_unchanged_refuses(tmp_path):
    facts = json.loads(FACTS_VALID.read_text())
    facts["facts"][0]["asserted_at"] = "2026-08-23T00:06:00+00:00"
    facts["facts"][0]["evidence"]["asserted_at"] = "2026-08-23T00:06:00+00:00"
    facts_path = tmp_path / "mutated_facts.json"
    facts_path.write_text(json.dumps(facts))
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(facts_path))
    assert passed is False
    assert result["reason_code"] == "VEIP_RECEIPT_MISMATCH"


def test_cli_d7_decision_time_changed_receipt_unchanged_refuses(tmp_path):
    facts = json.loads(FACTS_VALID.read_text())
    facts["now"] = "2026-08-23T00:11:00+00:00"
    facts_path = tmp_path / "mutated_facts.json"
    facts_path.write_text(json.dumps(facts))
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(facts_path))
    assert passed is False
    assert result["reason_code"] == "VEIP_RECEIPT_MISMATCH"


def test_cli_d8_admission_mutation_receipt_unchanged_refuses(tmp_path):
    artifact = json.loads(ARTIFACT.read_text())
    artifact["admission"]["approvals"] = [{"approval_id": "approval:xyz", "approver": "ops-lead"}]
    artifact_path = tmp_path / "mutated_artifact.json"
    artifact_path.write_text(json.dumps(artifact))
    result, passed = verify_receipt_cli(str(RECEIPT_VALID), str(artifact_path), str(ACTION), str(FACTS_VALID))
    assert passed is False
    assert result["reason_code"] == "VEIP_RECEIPT_MISMATCH"


def test_verify_receipt_repeated_cli_invocation_identical_stdout(capsys):
    main(["verify-receipt", str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(FACTS_VALID)])
    out1 = capsys.readouterr().out
    main(["verify-receipt", str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(FACTS_VALID)])
    out2 = capsys.readouterr().out
    assert out1 == out2


def test_verify_receipt_module_invocation_end_to_end():
    proc = subprocess.run(
        [sys.executable, "-m", "authcontract", "verify-receipt", str(RECEIPT_VALID), str(ARTIFACT), str(ACTION), str(FACTS_VALID)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS"


def test_verify_receipt_module_invocation_nonzero_on_tamper():
    golden = json.loads(RECEIPT_VALID.read_text())
    golden["decision"] = "DENY"
    tmp = ROOT / "fixtures" / "runtime" / "_tmp_tampered_for_subprocess_test.json"
    tmp.write_text(json.dumps(golden))
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "authcontract", "verify-receipt", str(tmp), str(ARTIFACT), str(ACTION), str(FACTS_VALID)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        assert proc.returncode != 0
        result = json.loads(proc.stdout)
        assert result["status"] == "REFUSED"
    finally:
        tmp.unlink(missing_ok=True)


# ----------------------------------------------- existing commands unbroken

def test_verify_command_still_works():
    code = main(["verify", str(FIXTURES / "valid.json")])
    assert code == 0


def test_project_command_still_works():
    code = main(["project", str(ARTIFACT)])
    assert code == 0


def test_check_action_command_still_works():
    code = main(["check-action", str(ARTIFACT), str(ACTION)])
    assert code == 0
