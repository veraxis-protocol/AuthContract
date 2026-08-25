#!/usr/bin/env python3
"""Public falsification harness for AuthContract.

Run it:

    python3 falsify.py

Anyone can run this against a clean clone with no credentials, no services and
no network. It exists so an outsider can try to *break* the claims rather than
only reproduce the happy path.

Each case declares the disposition AuthContract is expected to reach. The
harness runs the real CLI — the same commands a developer would type — and
compares what actually happened against that expectation. **A case fails if the
observed disposition differs from the expected one in either direction:** a
refusal that was supposed to pass fails, and a pass that was supposed to refuse
fails just as loudly. The second direction is the one that matters. A system
that fails closed is only trustworthy if you can watch it refuse.

Exit code is 0 only if every case matched. Any mismatch exits 1.

What this establishes: that the documented dispositions are the observed ones
for this bounded public set, on your machine, at this commit. What it does not
establish: production readiness, security certification, absence of defects, or
behaviour beyond these committed specimens. See docs/RELEASE-READINESS.md.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
FIXTURES = REPO_ROOT / "fixtures"

SPECIMEN = FIXTURES / "banking_payment_specimen.json"
ACTION_VALID = FIXTURES / "actions" / "send_payment_valid.json"
ACTION_UNDECLARED = FIXTURES / "actions" / "send_payment_unknown_action_type.json"
FACTS_VALID = FIXTURES / "runtime" / "facts_valid.json"
FACTS_STALE = FIXTURES / "runtime" / "facts_stale.json"
RECEIPT_VALID = FIXTURES / "runtime" / "receipt_valid.json"


def run_cli(args: list[str]) -> tuple[int, dict]:
    """Invoke the installed CLI and parse its single-line JSON stdout."""
    completed = subprocess.run(
        [sys.executable, "-m", "authcontract.cli", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    stdout = completed.stdout.strip()
    if not stdout:
        return completed.returncode, {
            "status": "<no JSON on stdout>",
            "stderr": completed.stderr.strip()[:400],
        }
    try:
        return completed.returncode, json.loads(stdout)
    except json.JSONDecodeError:
        return completed.returncode, {"status": "<unparseable stdout>", "raw": stdout[:400]}


def tampered_receipt_path(tmpdir: Path) -> Path:
    """A receipt with one bound value altered, and nothing else touched.

    The point is not that the file is malformed — it is well-formed. The point
    is that a bound digest no longer agrees with what the raw inputs recompute
    to, which is precisely what receipt verification is for.
    """
    receipt = json.loads(RECEIPT_VALID.read_text())
    receipt["contract_digest"] = "sha256:" + "0" * 64
    path = tmpdir / "receipt_tampered.json"
    path.write_text(json.dumps(receipt))
    return path


def build_cases(tmpdir: Path) -> list[dict]:
    return [
        {
            "name": "valid specimen is allowed",
            "why": "the whole implemented chain must reach ALLOW on a compliant request",
            "args": [
                "run-specimen", str(SPECIMEN), str(ACTION_VALID), str(FACTS_VALID),
                "--execution-result", "SIMULATED_SUCCESS",
            ],
            "expect_status": "PASS",
            "expect_reason": "OK",
            "expect_exit": 0,
            "expect_receipt": True,
        },
        {
            "name": "undeclared action is refused",
            "why": "an action the rule never granted authority for must not be improvised into a permission",
            "args": [
                "run-specimen", str(SPECIMEN), str(ACTION_UNDECLARED), str(FACTS_VALID),
                "--execution-result", "SIMULATED_SUCCESS",
            ],
            "expect_status": "REFUSED",
            "expect_reason": "RUN_UNCLASSIFIED_ACTION",
            "expect_exit": 1,
            "expect_receipt": False,
        },
        {
            "name": "stale runtime fact is refused",
            "why": "evidence that existed but is too old must not be treated as current permission",
            "args": [
                "run-specimen", str(SPECIMEN), str(ACTION_VALID), str(FACTS_STALE),
                "--execution-result", "SIMULATED_SUCCESS",
            ],
            "expect_status": "REFUSED",
            "expect_reason": "RUN_FACT_STALE",
            "expect_exit": 1,
            "expect_receipt": False,
        },
        {
            "name": "untampered receipt verifies",
            "why": "verification must accept a receipt whose bindings genuinely recompute",
            "args": [
                "verify-receipt", str(RECEIPT_VALID), str(SPECIMEN),
                str(ACTION_VALID), str(FACTS_VALID),
            ],
            "expect_status": "PASS",
            "expect_reason": "OK",
            "expect_exit": 0,
            "expect_receipt": None,
        },
        {
            "name": "tampered receipt binding is detected",
            "why": "a receipt is only evidence if altering a bound value is caught by recomputation",
            "args": [
                "verify-receipt", str(tampered_receipt_path(tmpdir)), str(SPECIMEN),
                str(ACTION_VALID), str(FACTS_VALID),
            ],
            "expect_status": "REFUSED",
            "expect_reason": "VEIP_RECEIPT_MISMATCH",
            "expect_exit": 1,
            "expect_receipt": None,
        },
    ]


def check(case: dict) -> tuple[bool, list[str]]:
    exit_code, payload = run_cli(case["args"])
    status = payload.get("status")
    reason = payload.get("reason_code")

    problems = []
    if status != case["expect_status"]:
        problems.append(f"status: expected {case['expect_status']!r}, observed {status!r}")
    if reason != case["expect_reason"]:
        problems.append(f"reason_code: expected {case['expect_reason']!r}, observed {reason!r}")
    if exit_code != case["expect_exit"]:
        problems.append(f"exit code: expected {case['expect_exit']}, observed {exit_code}")
    if case["expect_receipt"] is not None:
        has_receipt = isinstance(payload.get("receipt"), dict)
        if has_receipt != case["expect_receipt"]:
            expected = "a receipt" if case["expect_receipt"] else "no receipt"
            observed = "a receipt" if has_receipt else "no receipt"
            problems.append(f"receipt: expected {expected}, observed {observed}")

    print(f"  observed: status={status} reason_code={reason} exit={exit_code}")
    return not problems, problems


def main() -> int:
    print("AuthContract public falsification harness")
    print(f"repository: {REPO_ROOT}")
    print("Each case below states what SHOULD happen. A mismatch in either")
    print("direction — an unexpected refusal or an unexpected pass — fails.\n")

    with tempfile.TemporaryDirectory() as tmp:
        cases = build_cases(Path(tmp))
        failures = []
        for index, case in enumerate(cases, start=1):
            print(f"[{index}/{len(cases)}] {case['name']}")
            print(f"  expects: {case['expect_status']} / {case['expect_reason']} / exit {case['expect_exit']}")
            print(f"  why:     {case['why']}")
            ok, problems = check(case)
            if ok:
                print("  result:   MATCH\n")
            else:
                failures.append((case["name"], problems))
                print("  result:   MISMATCH")
                for problem in problems:
                    print(f"            - {problem}")
                print()

    print("-" * 68)
    if failures:
        print(f"FALSIFIED: {len(failures)} of {len(cases)} cases did not match expectation.")
        for name, problems in failures:
            print(f"  {name}")
            for problem in problems:
                print(f"    - {problem}")
        print("\nThis is a real result, not a harness bug to be worked around.")
        return 1

    print(f"All {len(cases)} cases matched their expected disposition.")
    print("This establishes the documented dispositions for this bounded public")
    print("set at this commit. It is not an audit and not proof of correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
