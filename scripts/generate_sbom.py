#!/usr/bin/env python3
"""Generate a deterministic, bounded CycloneDX SBOM from installed metadata."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path


def component(name: str) -> dict[str, object]:
    distribution = importlib.metadata.distribution(name)
    canonical = distribution.metadata["Name"] or name
    version = distribution.version
    return {
        "type": "library",
        "bom-ref": f"pkg:pypi/{canonical.lower()}@{version}",
        "name": canonical,
        "version": version,
        "purl": f"pkg:pypi/{canonical.lower()}@{version}",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    components = sorted([component("authcontract"), component("rfc8785")], key=lambda item: str(item["name"]))
    serial_material = json.dumps(components, sort_keys=True, separators=(",", ":")).encode()
    serial = hashlib.sha256(serial_material).hexdigest()
    document = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{serial[:8]}-{serial[8:12]}-{serial[12:16]}-{serial[16:20]}-{serial[20:32]}",
        "version": 1,
        "metadata": {"component": next(item for item in components if item["name"] == "authcontract")},
        "components": components,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.output} with {len(components)} components")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

