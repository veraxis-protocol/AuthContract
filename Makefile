.PHONY: test falsify no-network sbom ci

PYTHON ?= python3

test:
	$(PYTHON) -m pytest -q

falsify:
	$(PYTHON) scripts/falsify.py

no-network:
	$(PYTHON) scripts/verify_no_network.py

sbom:
	$(PYTHON) scripts/generate_sbom.py --output build/authcontract.cdx.json

ci: test falsify no-network sbom

