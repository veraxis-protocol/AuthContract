#!/usr/bin/env python3
"""Exercise install/import/tests/CLI with outbound Python sockets blocked."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts/no_network"


def run(label: str, command: list[str]) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(GUARD) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if result.returncode != 0:
        raise SystemExit(f"FAIL {label}: exit {result.returncode}")
    print(f"PASS {label}: no outbound Python socket used")


def main() -> int:
    run(
        "offline editable install",
        [sys.executable, "-m", "pip", "install", "--no-index", "--no-deps", "--no-build-isolation", "-e", "."],
    )
    run("package import", [sys.executable, "-c", "import authcontract"])
    run("test suite", [sys.executable, "-m", "pytest", "-q"])
    run("CLI", [sys.executable, "-m", "authcontract", "verify", "fixtures/valid.json"])
    print("PASS no-network guard: install/import/tests/CLI completed without outbound Python sockets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

