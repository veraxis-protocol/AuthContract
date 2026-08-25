# SDLC v1.2 producer status

Baseline: `ce783851897b8ddbbe92fae2b098b8bee8e88f57`.

This matrix uses the canonical public-release gate definitions in owner-authorized
`CURRENT-SDLC.md` v1.2. It reports literal producer evidence, does not accept its own
claims, and is **NOT SELF-ADJUDICATED**.

| Gate | Canonical gate | Disposition | Literal evidence / limitation |
|---|---|---|---|
| E | Human Repository Usability | PASS | The README first screen states purpose and maturity and provides copy/paste clean-clone, install, meaningful valid/refusal CLI, expected output, integration, and boundary paths. `make ci` exercises the documented implementation. |
| F | Agent Usability | PASS | `AGENTS.md` gives real install, verification, falsification, CLI, evidence-reading, and boundary instructions without inventing interfaces. |
| G | Adoption Readiness | NOT ESTABLISHED | The README provides a truthful first-run and integration surface, but no adoption/conversion result is established; no star prompt or repository CTA is treated as adoption proof. |
| H | Supply-Chain & Release Integrity | PASS | Consequential Actions are immutable-SHA pinned; PR dependency review, advisory scanning, and SBOM generation run in CI. No package/release artifact is published, so artifact digest, provenance, and attestation are not applicable to the current source-only state and are not claimed. |
| I | Security & Vulnerability Management | NOT ESTABLISHED | `SECURITY.md` states supported scope, triage expectations, scanner limits, and that a verified private disclosure route is not established. Dependency review and `pip-audit` provide bounded dependency evidence; a scanner result is not represented as an audit. |
| J | API & Versioning Integrity | PASS | `VERSIONING.md` declares the pre-1.0 Python API/import, CLI, exit, reason-code, artifact, receipt, and compatibility surfaces. |
| K | Machine-Readable Discovery & Licensing | NOT ESTABLISHED | `pyproject.toml` provides truthful package metadata, but the repository grants no license and declares no SPDX license identity. No grant is invented. |
| L | Public Falsification Completeness | PASS | `make falsify` publicly exercises one valid decision and three meaningful refusal/tamper paths: unclassified action, stale fact, and receipt mismatch (4/4). |
| M | Agent Interaction Observability | NOT ESTABLISHED | `docs/AGENT-OBSERVABILITY.md` truthfully documents GitHub-attributable versus dark local activity and the no-hidden-telemetry/no-network boundary. No approved ingestion pipeline, hosted gateway, or MCP observability implementation is established. |

## Independent Adjudication

Independent Adjudication remains pending for the designated independent reviewer and owner.
GitHub CI success is evidence, not acceptance. **CI GREEN IS NOT ACCEPTANCE.**
