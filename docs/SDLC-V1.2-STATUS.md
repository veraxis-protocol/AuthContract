# SDLC v1.2 disposition

Baseline: `ce783851897b8ddbbe92fae2b098b8bee8e88f57`.

This producer record reports literal repository evidence. It does not accept its
own claims and is **NOT SELF-ADJUDICATED**. The governing `CURRENT-SDLC.md` v1.2
text was not present in this repository at the baseline, so gate names are not
reconstructed from memory; the IDs and evidence disposition are recorded
without inventing missing normative text.

| Gate | Disposition | Literal evidence / limitation |
|---|---|---|
| E | PASS | Clean source install and full test suite are exercised by `make test` and `make no-network`. |
| F | PASS | `make falsify` checks valid PASS plus unclassified-action, stale-fact, and receipt-tamper refusals. |
| G | PASS | `SECURITY.md` defines supported scope, private reporting, and bounded triage. |
| H | PASS | Dependency review and vulnerability scanning are defined in `.github/workflows/security.yml`; `make sbom` generates a bounded SBOM. |
| I | PASS | `VERSIONING.md` identifies provisional CLI, Python, reason-code, artifact, and receipt contracts. |
| J | PASS | `README.md`, `AGENTS.md`, and `CONTRIBUTING.md` state the source-only, pre-1.0, no-license contribution boundary. |
| K | N/A | No distributable release is authorized; no release attestation is claimed. |
| L | NOT ESTABLISHED | Independent verification and adjudication have not occurred for this producer branch. |
| M | PASS | `docs/AGENT-OBSERVABILITY.md` distinguishes GitHub attribution from dark local work, defines trailers, and documents the no-network check. Remote gateway/MCP surfaces remain not implemented. |

These dispositions must be checked against the authoritative `CURRENT-SDLC.md`
v1.2 by an independent verifier before adjudication.

