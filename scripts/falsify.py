#!/usr/bin/env python3
"""Run the bounded public AuthContract falsification cases."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_case(name: str, args: list[str], exit_code: int, status: str, reason: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "authcontract", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{name}: stdout was not JSON: {result.stdout!r}") from exc
    actual = (result.returncode, payload.get("status"), payload.get("reason_code"))
    expected = (exit_code, status, reason)
    if actual != expected:
        raise AssertionError(f"{name}: expected {expected!r}, got {actual!r}; stderr={result.stderr!r}")
    print(f"PASS {name}: exit={exit_code} status={status} reason_code={reason}")


def main() -> int:
    artifact = "fixtures/banking_payment_specimen.json"
    valid_action = "fixtures/actions/send_payment_valid.json"
    valid_facts = "fixtures/runtime/facts_valid.json"

    run_case(
        "valid decision",
        ["run-specimen", artifact, valid_action, valid_facts, "--execution-result", "SIMULATED_SUCCESS"],
        0,
        "PASS",
        "OK",
    )
    run_case(
        "unclassified-action refusal",
        [
            "run-specimen",
            artifact,
            "fixtures/actions/send_payment_unknown_action_type.json",
            valid_facts,
            "--execution-result",
            "SIMULATED_SUCCESS",
        ],
        1,
        "REFUSED",
        "RUN_UNCLASSIFIED_ACTION",
    )
    run_case(
        "stale-fact refusal",
        [
            "run-specimen",
            artifact,
            valid_action,
            "fixtures/runtime/facts_stale.json",
            "--execution-result",
            "SIMULATED_SUCCESS",
        ],
        1,
        "REFUSED",
        "RUN_FACT_STALE",
    )

    receipt = json.loads((ROOT / "fixtures/runtime/receipt_valid.json").read_text())
    receipt["decision"] = "REFUSE"
    with tempfile.TemporaryDirectory(prefix="authcontract-falsify-") as temp_dir:
        tampered = Path(temp_dir) / "receipt-tampered.json"
        tampered.write_text(json.dumps(receipt), encoding="utf-8")
        run_case(
            "receipt-tamper refusal",
            ["verify-receipt", str(tampered), artifact, valid_action, valid_facts],
            1,
            "REFUSED",
            "VEIP_RECEIPT_MISMATCH",
        )

    print("PASS bounded falsification harness: 4/4 expected outcomes observed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

