# State of the art: what already exists around AuthContract

Scan date: 2026-08-23 (amended 2026-08-23, AC-024A). Method: two-direction
search (upstream source→runtime and downstream runtime→source) across
GitHub, GitLab, and primary project/spec pages, independently re-run
against an Engineering Lead research seed that is explicitly **not**
treated as authority here — and, for this revision, re-audited against
Claude's own AC-024 output after independent review (ADJ-AC-024) found
real evidence-integrity defects in it. Those defects and their repairs are
listed in [§0](#0-amendment-notice-ac-024a).

**This document is not a competitor table and does not claim AuthContract
is unique, first, or without equivalent.** It maps what capabilities
already exist in the open ecosystem, where AuthContract's target
architecture overlaps them, what to reuse instead of rebuilding, and
exactly where the current AuthContract MVP-alpha stands versus its target
architecture.

Corpus and method limits: this is a point-in-time scan (2026-08-23) of
public GitHub/GitLab repositories and primary spec pages reachable through
web search, direct repository fetch, and (for some systems) the GitHub
commit API in one research session, extended over two amendment rounds. It
is not exhaustive, not a legal survey, and not a substitute for evaluating
any specific comparator yourself before depending on it. A negative
finding below means **"not found in the inspected ref/corpus,"** never
"does not exist" — see [§0](#0-amendment-notice-ac-024a) for a concrete
case where that distinction mattered.

---

## 0. Amendment notice (AC-024A)

The original AC-024 candidate was returned for amendment by independent
review (ADJ-AC-024) for real evidence-integrity defects, not stylistic
ones. This revision fixes them directly rather than defending the prior
version:

1. **Four repositories AC-024 called unavailable are real and are now
   directly inspected.** AC-024 searched for `dekimuhq/regulation-as-code`,
   `mhatzl/mantra`, `arcadeai-labs/safe-hands`, and
   `smartpolicy-protocol/smartpolicy` and, finding no search-engine hits,
   reported them as not locatable. All four exist and were directly
   fetched at their exact URLs for this revision — this was a **search-tool
   coverage gap in AC-024's method, not an absence of the projects**. The
   AC-024 return record's own §9 already flagged one instance of this
   pattern (`jsuppe/loom`); it turns out the pattern was broader than that
   one instance. The corrected rule this revision follows throughout: an
   exact, named repository may be reported unlocatable only after a
   **direct URL fetch** fails, never after a zero-result search alone.
2. **`dekimuhq/regulation-as-code` is a materially close comparator to
   AuthContract's canonical-digest/receipt mechanics** — closer than
   anything else found in this entire scan — and is now deep-dived at six
   spec files plus the GDPR profile, with an exact commit SHA. S5, left
   `NOT EVALUATED` in AC-024 because this repository appeared unlocatable,
   is now executed. See [§4](#4-high-materiality-deep-dives).
3. **Several A–N matrix cells in AC-024 scored a neighboring capability as
   if it satisfied the literal axis** (e.g., a signature or audit log
   counted as "independently recomputable evidence," Git versioning
   counted as "canonical artifact digest," OIDC identity counted as
   "institutional standing"). Every YES/PARTIAL cell has been re-audited
   against the literal axis text; several are downgraded in
   [§3](#3-comparison-matrix), with the specific rule that triggered each
   change noted inline.
4. **S6's "REFUTED" verdict relied on a sentence attributed to Veridex's
   README as if it were a direct quote** ("policy rules appear
   author-defined based on autonomous-agent safety practices rather than
   regulatory mandates"). Re-checking the actual primary source: Veridex's
   README does say limits are human-configured ("Human sets limits → Agent
   gets session key → Makes autonomous payments") — that part is a direct,
   literal fact. It does **not** contain the words "regulatory mandates"
   or "external governance sources" anywhere; the absence of that
   vocabulary is a **search/inspection-scope finding**, not something the
   README itself asserts. S6 is corrected in [§5](#5-composite-substitution-attacks)
   to keep those two evidence classes separate rather than blending them
   into one "REFUTED" conclusion.
5. **A compact, reproducible source-evidence appendix** (exact commit SHA
   or equivalent, files inspected, evidence class, status) is added in
   [§9](#9-source-evidence-appendix) for every deep-dive and matrix system
   where that identity was obtainable.
6. **The complete ≥50-candidate screening/exclusion ledger is deposited in
   full in the AC-024A Drive return record**, not summarized here or
   pointed at with "see this document" — this document's own
   [§10](#10-search-method-and-limitations) carries a condensed version
   for developer readability, and says so explicitly.
7. **Status/maturity language is audited throughout.** Microsoft Agent
   Governance Toolkit's own README says **Public Preview**; this document
   says that, not "production-grade." The general rule applied everywhere
   below: documented support is not reproduced behavior; reproduced
   behavior is not production deployment maturity; a signature or identity
   credential is not institutional authority; public repository existence
   is not adoption.

None of these corrections required rewriting the document's overall
shape. The two most consequential findings — dekimuhq's closeness on the
canonical-digest/receipt side, and the correction of what Veridex's README
actually says versus what this document previously implied it said — are
carried through into the [S1–S7 re-run](#5-composite-substitution-attacks)
and the [final claim](#8-current-implementation-boundary).

---

## 1. Landscape in one table

AuthContract's target architecture (not all implemented yet — see [§8](#8-current-implementation-boundary))
is a chain:

```
source → interpretation/unresolved-state → professional/authority disposition
  → canonical governed artifact (.ac, digested) → PR/CI merge-result gate
  → runtime fact/action admissibility → reconstructable evidence
```

No single system inspected in this corpus directly evidences the complete
chain end to end. Substantial open precedent exists for most *individual*
links:

| Layer | What it needs to prove | Mature open precedent found |
|---|---|---|
| Source → structured interpretation | The rule is derived from a citable, quoted normative source | TNO Calculemus/FLINT, Catala, Blawx, L4, Logical English, OpenFisca, Obligation-First |
| Ambiguity / unresolved state | The system can say "the source doesn't settle this" instead of guessing | Obligation-First (defeasibility framing, PARTIAL). **No system inspected was confirmed to distinguish source-interpretation ambiguity from runtime evidence-missing/UNKNOWN** — see the corrected C-axis notes in [§3](#3-comparison-matrix). |
| Professional/authority disposition | A domain expert or institution stands behind the rule, with standing/lifecycle | Catala (domain-expert review intent), Obligation-First (Authority→Instrument schema, PARTIAL) — none observed to bind this to a specific software artifact's digest; identity/OIDC/authorized-functionary mechanisms in the runtime tier are **not** institutional standing (corrected per ADJ-AC-024 R3) |
| Canonical artifact identity | The exact governed object has a content-hashed identity | **dekimuhq/regulation-as-code's `manifestHash`** (RFC 8785 canonical JSON → SHA-256, deterministic) and decide.fyi's `rulebook.hash` are the two clean matches; most others use a version field or Git history, which is not the same thing (corrected per ADJ-AC-024 R3) |
| PR/CI merge-result gate | The check ran against the *actual* merge result, not just the isolated branch head | Conftest + required checks (commodity infrastructure); no comparator observed re-resolving live base-ref ancestry the way AuthContract's `git-gate` does |
| Runtime fact/action admissibility | A caller's claim is checked against independently-established context, not trusted at face value | Microsoft Agent Governance Toolkit (Public Preview), Permit0, Veridex, OpenEAGO, Permguard, Safe Hands, SmartPolicy, AP2 (mandate-scoped) |
| Reconstructable evidence | A third party can recompute the verdict from raw inputs and compare | **dekimuhq/regulation-as-code's receipt-verification contract** (`manifestMatches` / `reproducible` / `signatureValid`, computed independently from the manifest, facts, and corpus) is the clearest match found; in-toto's link/layout verification is the other clean match. Most agent-governance systems' "audit trail"/"signed decision" mechanisms are evidence *of a decision having been logged*, not independently *recomputable* verdicts, and are scored PARTIAL, not YES (corrected per ADJ-AC-024 R3) |

The rest of this document backs every cell above with a primary-source
citation, and is explicit about which of these are AuthContract's own
**target** claims rather than what the current reference implementation does.

---

## 2. What already exists, by capability layer

### Computational law / Rules-as-Code (source → structured, reviewable rule)

This is a real, active research and engineering field. AuthContract must not
claim novelty for "linking a rule to its source text" or "expert-reviewable
executable law" — these are established territory:

- **[TNO Calculemus/FLINT](https://gitlab.com/normativesystems)** (part of the TNO Rules Governance Stack) — a methodology and toolset (Choppr source decomposer, FLINT Ontology, Calculemus Calculator) for turning normative source text into structured norm frames (actions, duties, actors, facts) that stay traceable to the source sentence.
- **[Catala](https://github.com/CatalaLang/catala)** — a DSL for deriving faithful-by-construction code from legislative text, annotated line-by-line against the law it implements, with a formal default-logic semantics and a partially certified compiler.
- **[Blawx](https://github.com/Lexpedite/blawx)** — a web-based, Blockly-fronted Rules-as-Code environment over s(CASP)/Prolog; explicitly experimental/educational, MIT-licensed.
- **[L4 / Natural L4](https://github.com/smucclaw/l4-ide)** (SMU Centre for Computational Law) — a functional DSL for legal rules and contracts, with an IDE, REST/MCP decision-service exposure, and natural-language generation back out of the formal model.
- **[Logical English](https://github.com/LogicalContracts/LogicalEnglish)** — a controlled natural language that compiles to Prolog/s(CASP), used to model finance and insurance regulation text.
- **[OpenFisca](https://github.com/openfisca/openfisca-core)** — the most widely adopted open tax/benefit rules-as-code engine, with dozens of country packages (e.g. [openfisca-france](https://github.com/openfisca/openfisca-france)) turning legislation into a computable, testable model.
- **[Accord Project](https://github.com/accordproject)** (Cicero, Ergo) — Linux Foundation smart-legal-contract stack binding natural-language templates to executable clause logic.
- **[Obligation-First](https://obligationfirst.org/)** ([examples on GitHub](https://github.com/snapsynapse/obligation-first)) — an open upper schema (`Authority → Instrument → Term → Obligation`) for representing normative content across jurisdictions, explicitly *not* a rules engine — it references Catala/Blawx/OpenFisca as where the executable encoding would live.
- **[Mantra](https://github.com/mhatzl/mantra)** — **recovered in AC-024A** (AC-024 reported it unlocatable via search; a direct fetch finds it real). A Rust-focused requirements-traceability tool: maps requirements to implementation/test code, tracks six sync states (Failed/Verified/Skipped/Unverified/Deprecated/Excluded). Does not reference external regulation or a formal standards body, and its README documents no Git-merge-result-bound PR gate — it is a project-requirements tool in the same family as Loom, not a source-of-normative-authority tool.
- **[FINOS Open RegTech SIG](https://github.com/finos/open-regtech-sig)** — an active effort to "issue regulation as code alongside the prose," directly on-topic for AuthContract's upstream half.
- LegalRuleML / Akoma Ntoso — OASIS LegalDocML standards for legal-rule and legal-document markup. These are **standards, not implementations**; do not infer runtime behavior from the spec text alone.

**If you need to represent a rule's relationship to its source text, look at
this list before building something bespoke.**

### Compliance / control → policy bridge, and the closest single comparator found

- **[`dekimuhq/regulation-as-code`](https://github.com/dekimuhq/regulation-as-code)** — **the single most materially close comparator to AuthContract's own canonical-digest-and-receipt mechanics found in this entire scan.** Deep-dived in [§4](#4-high-materiality-deep-dives); do not treat the one-line mention here as the full picture.
- **[OSCAL Compass Compliance-to-Policy (C2P)](https://github.com/oscal-compass/compliance-to-policy)** (Python and [Go](https://github.com/oscal-compass/compliance-to-policy-go) implementations) — converts OSCAL Component Definitions into native policy-engine configuration (Kyverno, Open Cluster Management, Auditree) and converts results back into OSCAL Assessment Results, GitOps-native.
- **[Compliance Trestle](https://github.com/oscal-compass/compliance-trestle)** — CI-friendly tooling for authoring/validating OSCAL compliance artifacts in Git.
- **[ComplianceAsCode/content](https://github.com/ComplianceAsCode/content)** (formerly SCAP Security Guide) — machine-enforceable security-control content across many OS/product targets.
- **[FINOS Common Cloud Controls](https://github.com/finos/common-cloud-controls)**, extending in 2025–2026 to **CC4AI ("Common Controls for AI")** — machine-readable, technology-neutral controls for financial-services cloud and AI deployments, backed by 20+ major financial institutions and cloud providers.

**Boundary observed across this whole tier, dekimuhq included:** these
systems map controls/obligations to policy IDs, evidence families, or
engine configuration. None inspected here proves the mapping is
*semantically faithful* to the authoritative prose — the encoding is
always author-asserted, whether the author is a compliance engineer
writing an OSCAL mapping or a regulation-as-code author writing a
`SourceManifest`.

### Requirements/code traceability + CI

- **[Loom](https://github.com/jsuppe/loom)** — captures requirements from natural-language conversation, links them to code via content hashing, flags `GRAPH-DRIFT` when code diverges from its linked requirement, and produces a single CI health-score gate. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[Mantra](https://github.com/mhatzl/mantra)** — see above; the same family as Loom, narrower (Rust-focused, no drift-detection CI gate documented).
- **[Conftest](https://github.com/open-policy-agent/conftest)** — runs Rego assertions against structured config in CI/PR, a commodity building block many of the above systems could sit behind.
- **[fiberplane/drift](https://github.com/fiberplane/drift)** — binds markdown specs to code via tree-sitter + git and fails CI on drift; narrower than Loom (docs, not institutional rules) but the same drift-detection shape.
- GitHub/GitLab required-status-checks, branch protection, and merge-result gating are **commodity delivery infrastructure**. AuthContract's differentiation cannot be "having a merge gate" — every serious CI system has one. What AuthContract's `git-gate` specifically does — re-resolving the *current* base ref live and requiring `git merge-base --is-ancestor` proof that the evaluated SHA actually contains both the current base and the PR head — was not observed as a built-in behavior of Conftest, GitHub required checks, GitLab merge trains, or Loom's/Mantra's own CI health gates by themselves; see [§5](#5-composite-substitution-attacks).

### Policy / authorization engines

- **[Open Policy Agent (OPA)](https://github.com/open-policy-agent/opa)** — general-purpose policy engine; rules/data are supplied by the caller.
- **[Cedar](https://github.com/cedar-policy/cedar)** — authorization policy language with schema validation and automated formal-analysis tooling. Per the Evidence and Claim Register: Cedar's own formal verification is about Cedar policies themselves, not about any translator or projection *into* Cedar from another representation — it is not itself evidence of projection/transpilation conformance for a system that compiles down to it.
- **[OpenFGA](https://github.com/openfga/openfga)** — Zanzibar-style relationship-based authorization.
- **[Permify](https://github.com/Permify/permify)** — another Zanzibar-inspired fine-grained authorization engine, now part of FusionAuth.

All four are downstream infrastructure: they evaluate policy that something
else must supply and warrant. None of them establishes where the policy
came from.

### Agent runtime governance / consequential action control planes

This is the fastest-moving tier in the whole landscape (most of it shipped
in the last 12 months) and the one most likely to be stale by the time you
read this:

- **[Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)** — the README's own status label is **"Public Preview"** ("production-quality public preview releases. May have breaking changes before GA") — this document preserves that label rather than upgrading it. Deterministic interception of agent tool calls, YAML/OPA/Cedar policy, zero-trust identity (SPIFFE/DID/mTLS), Merkle-chained tamper-evident audit log, multi-language SDKs, explicit `GovernanceDenied` records. The README maps its controls to OWASP Agentic AI Top 10, NIST AI RMF, EU AI Act, and SOC 2 as *compliance mappings* — it explicitly does not claim to enforce policies *derived from* those frameworks; users author their own YAML policies. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[Permit0](https://github.com/permit0-ai/permit0)** — pre-execution, deterministic action-authorization layer for agents; every allow/block/escalate decision is described by the project as "replayable and signed"; Apache-2.0, Rust. No explicit maturity/status label was found in the inspected README.
- **[Veridex / agentic-payments](https://github.com/veridex-protocol)** (`@veridex/agentic-payments`, `agents-treasury`) — session-key-scoped autonomous agent payments with an 8-rule `PolicyEngine`, signed `EvidenceBundle`, multi-chain support. High materiality — see [§4](#4-high-materiality-deep-dives) for the corrected quote-level analysis of what its README actually says versus what this document infers.
- **[OpenEAGO](https://github.com/finos-labs/open-eago)** (FINOS Labs) — enterprise agent governance/orchestration overlay with jurisdiction enforcement, HITL, and real-time compliance checks against GDPR/DORA/EU AI Act/SR 11-7/BCBS 239/PCI-DSS/MiFID-II/EMIR. No explicit maturity/status label was found in the inspected `overview.md`. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[Permguard](https://github.com/permguard/permguard)** — Git-versioned, distributed authorization engine spanning traditional systems and AI agents.
- **[Safe Hands](https://github.com/arcadeai-labs/safe-hands)** — **recovered in AC-024A** (AC-024 reported it unlocatable via search; a direct fetch finds it real). Implements Asimov's Three Laws of Robotics as Cedar authorization policy, governing a real physical robotic arm over MCP before commands reach actuators. Reports blocking all 46 forbidden commands across 11,728 red-team test cases with zero false-permits in its own benchmark description. Its "law" concept is a fictional/design framing, not institutional or regulatory authority, and no source-citation mechanism was found.
- **[SmartPolicy](https://github.com/smartpolicy-protocol/smartpolicy)** — **recovered in AC-024A** (AC-024 reported it unlocatable via search; a direct fetch finds it real). An on-chain (Ethereum Sepolia) policy registry decoupling authorization rules from enforcement, with off-chain EIP-712 signed grants via an MCP server. The project's own materials describe the contracts as tested (54 Foundry tests passing) but **not independently audited** and internal pending maturity — status preserved here rather than upgraded.
- **[kyndryl-open-source/aiagent-portable-authorization](https://github.com/kyndryl-open-source)** — reference implementation of policy-embedded credential authorization for AI agents (arXiv:2605.11487): signed credentials with machine-evaluable constraints, verified at runtime, producing signed audit decisions.
- **[Google Agent Payments Protocol (AP2)](https://github.com/google-agentic-commerce/AP2)** — an industry-scale open standard (60+ launch partners including Mastercard, PayPal, Coinbase, American Express) representing every agent purchase as three signed **Mandates** (Intent, Cart, Payment), each a W3C Verifiable Credential.
- **[alibaba/open-agent-auth](https://github.com/alibaba/open-agent-auth)** — enterprise framework implementing the IETF draft "Agent Operation Authorization," binding user identity to agent operations via OAuth2/OIDC/WIMSE/W3C VC with semantic audit trails; the project's own materials describe it as **public beta**.
- Other agent-governance projects screened but not deep-dived: `Runestone-Labs/gatekeeper`, `aporthq/aport-spec` (Open Agent Passport), `opena2a-standards/agent-authorization-protocol`, `better-auth/agent-auth`, `auth-agent/auth-agent` — full detail in the AC-024A Drive return's screening ledger.

**Boundary observed across this whole tier:** every one of these systems
governs an action against a *supplied* policy/mandate. What none of them
was directly confirmed to do is bind that policy back to an authoritative
external source with a citation, an unresolved-state marker, or genuine
institutional standing (as distinct from an identity/authentication
credential) — see the corrected, quote-level evidence for Veridex and
OpenEAGO specifically in [§4](#4-high-materiality-deep-dives) and the
evidence-class discipline applied in [§5](#5-composite-substitution-attacks).

### Evidence, replay, attestation

- **[in-toto](https://github.com/in-toto/in-toto)** — signed layouts, authorized functionaries, signed link metadata, and continuous verification of a software supply chain. (Note: "authorized functionaries" is an identity/authorization mechanism, not institutional standing in the sense AuthContract's target E axis means — corrected per ADJ-AC-024 R3; see [§3](#3-comparison-matrix).)
- **[decide.fyi](https://github.com/decidefyi/decide)** — versioned, hashed rulebooks (`rulebook.hash`); deterministic verdicts; `input_hash`; Ed25519-signed attestation bundles; replay that compares verdict/evidence/record hashes against the original run; explicit non-binding vs. production-binding modes. High materiality — see [§4](#4-high-materiality-deep-dives).
- **Sigstore** and the **[DSSE](https://github.com/secure-systems-lab/dsse)** envelope spec — the signing-envelope/attestation-format layer that in-toto and Sigstore's `cosign` both build on. Infrastructure precedent for tamper-evident evidence, not authority semantics.

---

## 3. Comparison matrix

Cell values follow the AuthContract Evidence and Claim Register: **YES**
(directly evidenced in the inspected ref, matching the *literal* axis
definition — not a neighboring capability), **PARTIAL** (evidenced but
narrower/different, or a neighboring capability that does not fully
satisfy the axis), **NO-EVIDENCE-FOUND** (searched/inspected the exact
ref/corpus and did not find it — never read as "does not exist"),
**NOT-EVALUATED** (insufficient inspection), **N/A** (out of scope),
**STANDARD** (this is a specification, not an implementation — do not
infer runtime behavior).

Axes: **A** source citation/anchor · **B** structured rule representation ·
**C** unresolved/ambiguity preservation (source-interpretation uncertainty,
not runtime evidence-missing/UNKNOWN) · **D** expert/professional review ·
**E** issuer/authority/standing/lifecycle (not identity/authentication
alone) · **F** canonical artifact identity/digest (a content hash, not a
version field or Git commit alone) · **G** projection/transpilation with a
conformance result (not a destination language's own formal analysis) ·
**H** PR/CI gate bound to the actual merge result (not a generic CI/health
gate) · **I** runtime fact provenance/freshness · **J** closed action
universe/unknown handling · **K** pre-execution enforcement · **L**
independently recomputable evidence/replay *from raw inputs* (not a
signature, Merkle log, or audit record alone) · **M**
correction/supersession continuity · **N** current-vs-target honesty.

**Cells changed from the AC-024 candidate are marked with a dagger (†) and
the rule that changed them.**

| System | Class | A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TNO Calculemus/FLINT | Upstream | YES | YES | PARTIAL | PARTIAL | NOT-EVAL | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Catala | Upstream | YES | YES | PARTIAL† (default logic resolves via defaults, doesn't necessarily flag-as-unresolved) | PARTIAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Blawx | Upstream | YES | YES | PARTIAL | NOT-EVAL | NO-EV | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | YES |
| L4 / Natural L4 | Upstream | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Logical English | Upstream | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| OpenFisca | Upstream | PARTIAL | YES | NOT-EVAL | PARTIAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| Accord Project (Cicero/Ergo) | Upstream/Adjacent | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Obligation-First | Upstream | YES | YES | PARTIAL | PARTIAL | PARTIAL† (ontological authority concept, not verified lifecycle/revocation mechanics) | NOT-EVAL | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES |
| **`dekimuhq/regulation-as-code`** † (recovered, deep-dived) | Upstream/Bridge | PARTIAL† (`citationUrl` present but optional) | YES | **NO-EV** † (five-state model is explicitly deterministic with no unresolved/ambiguous concept — an observed absence, not just unsearched) | NO-EV | NO-EV | **YES** (`manifestHash`, RFC 8785 canonical JSON → SHA-256) | N/A | NO-EV | N/A | YES (typed facts, closed compile-time checks) | N/A | **YES** (receipt independently verifies `manifestMatches`/`reproducible`/`signatureValid` from raw manifest+facts+corpus) | NOT-EVAL | YES (spec is explicitly versioned/frozen at v1) |
| Mantra † (recovered) | Adjacent/Upstream | NO-EV | YES | NOT-EVAL | N/A | NO-EV | NOT-EVAL | N/A | NO-EV | N/A | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| LegalRuleML / Akoma Ntoso | STANDARD | STANDARD | STANDARD | STANDARD | N/A | STANDARD | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| OSCAL Compass C2P | Upstream/Bridge | N/A | YES | NOT-EVAL | NOT-EVAL | NOT-EVAL | PARTIAL† (UUID/version, not confirmed content digest) | YES | PARTIAL | NO-EV | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| Compliance Trestle | Upstream/Infra | N/A | YES | N/A | NOT-EVAL | NOT-EVAL | PARTIAL† (same F correction as C2P) | N/A | PARTIAL | N/A | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| ComplianceAsCode/content | Upstream/Bridge | PARTIAL | YES | N/A | NOT-EVAL | NOT-EVAL | PARTIAL† | YES | PARTIAL | N/A | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| FINOS Common Cloud Controls / CC4AI | Upstream standard | YES | YES | NOT-EVAL | YES | NOT-EVAL | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Loom | Adjacent/Upstream | N/A | YES | PARTIAL | N/A | NO-EV | PARTIAL† (content-hashed requirement, not an institutionally-governed artifact) | N/A | **NO-EV**† (health-score CI gate is generic, not source-relative merge-result binding) | N/A | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| Conftest | Infrastructure | N/A | YES | N/A | N/A | N/A | N/A | N/A | PARTIAL | N/A | N/A | N/A | N/A | N/A | N/A |
| OPA | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| Cedar | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | **NO-EV**† (formal analysis is of Cedar's own policies, not a translator into Cedar) | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| OpenFGA | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| Microsoft Agent Governance Toolkit | Downstream (**Public Preview**†) | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL† (identity/RBAC, not institutional standing) | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | **PARTIAL**† (Merkle-chained audit log is tamper-evident, not confirmed independently recomputable from raw inputs) | NOT-EVAL | YES |
| Permit0 | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL† | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | **PARTIAL**† (project calls decisions "replayable and signed"; mechanism not independently confirmed) | NOT-EVAL | NOT-EVAL |
| Veridex agentic-payments | Downstream/Runtime | NO-EV† (searched; the literal phrase "regulatory mandates" does not appear — see [§4](#4-high-materiality-deep-dives)) | YES | NOT-EVAL | NO-EV | PARTIAL† | PARTIAL† (mandate version field, not confirmed content digest) | N/A | NO-EV | PARTIAL | YES | YES | **PARTIAL**† (`EvidenceBundle` hash/signature verification, not confirmed independent recomputation from raw inputs) | YES (mandate versioning) | NOT-EVAL |
| OpenEAGO | Downstream/Control-plane | NO-EV | YES | NO-EV | NOT-EVAL | PARTIAL† | NOT-EVAL | N/A | NO-EV | NOT-EVAL | YES | YES | **PARTIAL**† (blockchain audit trail records activity; not confirmed as independently recomputable verdicts) | NOT-EVAL | NOT-EVAL |
| Permguard | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | PARTIAL† (Git-versioned policy, not a confirmed content digest distinct from Git's own object hash) | N/A | NO-EV | NOT-EVAL | YES | YES | NOT-EVAL | YES | NOT-EVAL |
| Safe Hands † (recovered) | Downstream/Runtime (physical) | NO-EV | YES (Cedar policy) | N/A | N/A | NO-EV | NOT-EVAL | N/A | NO-EV | NOT-EVAL | YES (46 forbidden commands blocked, 11,728-case benchmark) | YES | PARTIAL (audit log of law/decision per action) | NOT-EVAL | NOT-EVAL |
| SmartPolicy † (recovered) | Downstream (**not independently audited**†) | NO-EV | YES | N/A | N/A | PARTIAL (on-chain registry owner, not institutional standing) | PARTIAL (immutable on-chain record, not a canonical-artifact digest scheme like dekimuhq's) | N/A | NO-EV | NOT-EVAL | NOT-EVAL | YES | PARTIAL (EIP-712 signed grants) | NOT-EVAL | NOT-EVAL |
| kyndryl aiagent-portable-authorization | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | PARTIAL† (signed decisions; recomputability from raw inputs not confirmed) | NOT-EVAL | NOT-EVAL |
| Google AP2 | Downstream/Runtime | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | PARTIAL† (VC = signed credential; content-digest scheme not confirmed) | N/A | NO-EV | YES (signed by wallet) | YES | YES | PARTIAL† (signed Mandates; independent recomputation contract not confirmed) | PARTIAL | NOT-EVAL |
| alibaba/open-agent-auth | Downstream (**public beta**) | NO-EV | YES | NOT-EVAL | NO-EV | **NO-EV**† (OIDC identity is not institutional standing — ADJ-AC-024's own example) | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | PARTIAL (audit trails; recomputability not confirmed) | NOT-EVAL | PARTIAL (labels itself public beta) |
| in-toto | Infrastructure | N/A | N/A | N/A | N/A | **NO-EV**† (authorized functionaries are an identity mechanism, not institutional standing) | YES (link metadata content hash) | N/A | N/A | N/A | N/A | N/A | YES (layout/materials/products verification is genuinely independently recomputable) | YES | N/A |
| decide.fyi | Downstream/Decision-evidence | NO-EV | YES | **NO-EV**† (`UNKNOWN`/review states are runtime input-completeness, not confirmed source-interpretation ambiguity) | NO-EV | NOT-EVAL | YES (`rulebook.hash`) | N/A | NO-EV | PARTIAL | YES | YES | **PARTIAL**† (hash-compare replay confirmed; not confirmed to recompute from raw un-hashed inputs each time versus re-hashing stored inputs) | YES (snapshots) | NOT-EVAL |
| Sigstore / DSSE | Infrastructure | N/A | N/A | N/A | N/A | PARTIAL (signer identity) | N/A | N/A | N/A | N/A | N/A | N/A | YES | N/A | N/A |

Standards (LegalRuleML/Akoma Ntoso) and pure infrastructure rows
(GitHub/GitLab required checks, Conftest, OPA/Cedar/OpenFGA, Sigstore/DSSE)
are included because AuthContract's target architecture is explicitly meant
to sit *on top of* several of them, not replace them.

**This document does not claim every cell above is independently verified
from primary source with equal rigor.** Cells backed by a direct file
fetch and quote are the ones marked YES/NO-EV with an explicit citation in
[§4](#4-high-materiality-deep-dives) or [§9](#9-source-evidence-appendix);
the remaining cells (mostly `TNO/Catala/L4`-family upstream systems, scored
during the original AC-024 pass) rest on the depth of inspection recorded
for that system in [§9](#9-source-evidence-appendix) and should be treated
accordingly — several are `NOT-EVAL` for exactly this reason.

---

## 4. High-materiality deep dives

### `dekimuhq/regulation-as-code` — the closest comparator found in this entire scan

**This repository is real, public, and was reported unlocatable by AC-024
due to a search-tool coverage gap, not because it doesn't exist.** Six
spec files plus the GDPR profile were fetched directly for this revision
(commit `11ba12bfd6851800ab11a2c925b99ad09ba90d98`, branch `main`,
inspected 2026-08-23):

- **`spec/grammar.md`** — an authored `SourceManifest` bundles a typed
  `FactSchema` (boolean/number/enum facts) with `Obligation`s, each pairing
  an `appliesWhen` `Condition` (boolean algebra over facts) with a
  `requires` `Requirement` (quantifiers over an evidence corpus:
  `exists`/`fresh`/`count`/`all`/`any`/`dependsOn`). Each obligation names
  a `regulation` and has an *optional* `citationUrl` field pointing to the
  authoritative legal source.
- **`spec/compilation.md`** — compilation is a deterministic, fail-closed,
  eight-error-code static-check pipeline (`schema-invalid`,
  `duplicate-id`, `unknown-fact`, `fact-type-mismatch`, `unknown-family`,
  `unknown-dependency`, `dependency-cycle`, `nested-dependson-invalid`).
  On success it emits a `CompiledManifest` carrying a `manifestHash`:
  **the SHA-256, over RFC-8785-derived canonical JSON, of a five-field
  intermediate representation** — this is materially the same digest
  discipline AuthContract's own `digest.py` uses for `.ac` artifacts
  (RFC 8785 JCS + SHA-256), independently arrived at.
- **`spec/evidence.md`** — the evidence corpus is an open, extensible
  family registry of `CorpusReceipt` records (five fields: `family`,
  `claimId`, `issuedAt`, `active`, optional `eventType`), matched by exact
  string equality, with `active` supporting revocation-style semantics.
- **`spec/receipt.md`** — an `EvaluationReceipt` binds four content hashes
  (`manifestHash`, `factsHash`, `corpusDigest`, `reportHash`) under an
  Ed25519 signature over exactly `{kind, alg, input, reportHash}`.
  **Independent verifiers need only the public spec, the three raw inputs
  (manifest, facts, corpus), and a trust-anchor key resolver, and produce
  three independent booleans: `manifestMatches`, `reproducible`,
  `signatureValid`.** This is the clearest, most literal match to
  AuthContract's own target "recompute the receipt from raw inputs and
  compare" behavior found anywhere in this scan — closer than
  Microsoft AGT's, Permit0's, Veridex's, or OpenEAGO's audit/evidence
  mechanisms, none of which document an equivalent independent-recomputation
  contract at this level of rigor.
- **`spec/evaluation.md`** — obligations resolve to exactly one of five
  states (`satisfied`, `at-risk`, `expired`, `missing`, `not-applicable`).
  **The specification explicitly states there is no "unresolved,"
  "undetermined," or "ambiguous" evaluation state** — this is a directly
  observed *absence*, not merely an unsearched one, and it is the paradigm
  case ADJ-AC-024's R3 warned about: a closed, deterministic runtime status
  model is not the same thing as preserved source-interpretation
  ambiguity. dekimuhq's `missing` state means "no satisfying evidence was
  found," not "the regulation itself is unclear here."
- **`profiles/gdpr/v1.md`** — a reference profile (v1.2.0) encoding eight
  GDPR obligations (Arts. 5, 6, 13, 15–22, 17, 35, 36) against named
  evidence families, explicitly framed as "reference material, not legal
  advice."

**What this means for AuthContract's claim:** dekimuhq/regulation-as-code
independently demonstrates that a source-labeled, content-hash-addressed,
independently-verifiable-receipt compliance framework is not a novel
combination — someone has already built exactly this shape of system, with
a digest discipline extremely close to AuthContract's own. What it does
**not** do, on the evidence actually inspected: bind that manifest to a Git
PR's merge-result composition; enforce anything against a live agent
action (its domain is compliance-obligation-satisfaction over a
"workspace," not agent tool-call gating); establish institutional
authority/standing for the `SourceManifest`'s author (the spec is silent on
who is authorized to author a manifest, versus merely how the manifest is
structured); or verify that the obligation's encoding is *semantically
faithful* to the cited regulation (`citationUrl` is optional and, even
when present, is a pointer for a human reader, not a machine-checked
fidelity proof). See [S5](#5-composite-substitution-attacks) for the full
composite-substitution analysis this comparator now requires.

### Veridex / agentic-payments — corrected quote-level analysis

AC-024 attributed to Veridex's README a sentence about policy rules being
"author-defined based on autonomous-agent safety practices rather than
regulatory mandates," presented as if quoting the repository. **Re-fetching
the actual README directly finds no such sentence, and specifically no
occurrence of the phrases "regulatory mandates" or "external governance
sources" anywhere in it.**

What the README *does* literally say, quoted directly: **"Human sets
limits → Agent gets session key → Makes autonomous payments"**, and **"Give
your agent a wallet with human-set spending limits."** Session
configuration is `dailyLimitUSD`, `perTransactionLimitUSD`, `expiryHours`,
`allowedChains`. No maturity/status label (beta, production, experimental)
was found in the inspected README; test coverage ("372 passing") and an
MIT license are stated.

Corrected classification: **it is a direct, primary-source (E4) fact that
Veridex's spending limits are configured by the human wallet creator.** It
is a **separate, search/inspection-scope (E8) finding** that no mention of
external regulatory or governance sourcing was found in the inspected
README — this absence finding does not itself appear as an assertion
anywhere in Veridex's own text, and should not be presented as though it
does. Both facts point the same direction (Veridex's policy provenance is
author/operator-configured, not source-derived), but they are different
evidence classes and are kept separate here per the Evidence and Claim
Register, per ADJ-AC-024's correction.

### OpenEAGO — corrected quote-level analysis

Direct re-fetch of `docs/overview/overview.md` finds the literal sentence:
**"Immutable audit trails spanning multiple regulatory frameworks for
examination by FCA, MAS, and FinCEN"** and **"Audit Continuity: Blockchain
trails provide immutable records across all interactions."** Both are E4
direct facts about audit *recording* across named regulators. **The
document was inspected for, and did not contain, any passage tracing a
specific policy back to a specific regulatory clause** — this is an E8
inspection-scope finding about what the document does not contain, kept
explicitly separate from the E4 facts about what it does say. No explicit
project maturity/status label (alpha, beta, RFC, stable) was found in the
inspected document.

### Microsoft Agent Governance Toolkit

**Status, preserved as stated by the project:** the README's own words are
"production-quality public preview releases. May have breaking changes
before GA" — this document calls it **Public Preview**, not
production-grade, per ADJ-AC-024's explicit correction.

**Strongest overlap:** deterministic pre-execution interception of agent
tool calls against YAML/OPA/Cedar policy, with a Merkle-chained
tamper-evident audit log and an explicit `GovernanceDenied` record shape.
**Policy provenance, directly quoted:** the toolkit maps its controls to
OWASP Agentic AI Top 10, NIST AI RMF, EU AI Act, and SOC 2 as *compliance
mappings*, and states plainly that policy enforcement is
application-defined — users write their own YAML policies; the toolkit
"does not cite institutional authority for the actual policies it
enforces." This is a direct, quoted E4 fact, not an inference.
**L-axis correction:** the Merkle-chained audit log is tamper-*evident*
(you can detect if it was altered); this scan did not confirm it is
independently *recomputable* from raw inputs the way dekimuhq's receipt
contract is — scored PARTIAL, not YES.

### decide.fyi

**Strongest overlap:** the closest system in this scan (alongside
dekimuhq) to AuthContract's rule→runtime→evidence half — a versioned,
hashed rulebook (`rulebook.hash`), deterministic verdicts, `input_hash`,
Ed25519-signed attestation bundles, and replay that compares hashes
against the original run.
**C-axis correction:** decide.fyi's `UNKNOWN`/review-required verdict
states were scored YES for ambiguity-preservation in AC-024. On the R3
re-audit, this is the exact pattern the amendment warns against: decide.fyi's
domain is refund/cancel/trial/return *decisions*, and `UNKNOWN` in that
context reads as "the input data needed to decide is missing or unclear,"
not "the underlying policy text is ambiguous." No passage was found
distinguishing "the vendor's refund policy is itself ambiguous" from "we
don't have enough information about this specific case" — scored
NO-EVIDENCE-FOUND, not YES.
**L-axis note:** decide.fyi's own materials describe replay as comparing
hashes against the original run; whether replay recomputes from the raw,
un-hashed rulebook/input each time or re-derives from already-stored
hashes was not confirmed at the code level in this scan — scored PARTIAL.
**Capability that remains uniquely strong here:** a live, production
decision API with a GitHub Action that hashes vendor policy pages daily
and opens an issue on change — a working instance of exactly the kind of
source-drift detection AuthContract's target architecture describes only
conceptually.

---

## 5. Composite-substitution attacks (re-run after evidence corrections)

**S1 — TNO Calculemus/FLINT + Git/CI + OPA/Cedar + in-toto reproduces the
full AuthContract architecture.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED.** Positive evidence:
FLINT gives source→structured interpretation (A/B); OPA/Cedar give runtime
policy evaluation (J/K); in-toto gives signed, independently verifiable
supply-chain evidence (L, corrected — in-toto's own verification is a
genuine match, unlike most agent-governance audit logs). Missing
transition: no evidence these four have been integrated for this purpose,
and specifically no evidence of a PR/CI gate re-resolving live merge-base
ancestry, or of runtime facts checked against verifier-established context
rather than caller-supplied policy input. What to reuse: FLINT's
source-decomposition methodology.

**S2 — Catala/L4 + Conftest/GitHub required checks + a runtime policy
engine + in-toto reproduces it.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED.** Same shape as S1.
Missing transition unchanged.

**S3 — OSCAL + C2P + OPA/Cedar + GitHub + evidence/attestation reproduces
it for enterprise controls.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED**, closest of the
upstream compositions for enterprise-control domains specifically. C2P's F
axis is corrected to PARTIAL (UUID/version, not a confirmed content
digest) — this slightly weakens, not strengthens, this composition's claim
to canonical artifact identity relative to the AC-024 version.

**S4 — Obligation-First + an executable encoding (Catala/Blawx/OpenFisca) +
a runtime governor + in-toto reproduces it.**
Disposition: **OPEN.** Unchanged — architecturally plausible, no evidence
of anyone having built it end to end.

**S5 — Regulation-as-Code (`dekimuhq`) + Microsoft AGT / Permit0 / OpenEAGO
+ in-toto / receipt systems can reproduce the AuthContract composite.**
**Disposition: STRONGLY SUPPORTED — NOT ESTABLISHED.** This attack is now
executed in full, not left `NOT EVALUATED`.

Positive evidence, by transition:
- **(a) author/profile supplies the machine meaning** — YES, directly
  evidenced. dekimuhq's `SourceManifest` grammar is exactly this: an
  author writes typed facts, conditions, and requirements.
- **(b) semantic fidelity to authoritative source** — **NOT ESTABLISHED.**
  `citationUrl` is optional, points to a URL for human reference, and
  nothing in `grammar.md`, `compilation.md`, or `evaluation.md` checks
  that the encoded obligation actually matches what the cited regulation
  says. This is the same author-asserted-mapping boundary every upstream
  bridge system in this scan has.
- **(c) institutional authority/standing** — **NO-EVIDENCE-FOUND.** No
  spec file inspected defines who is authorized to publish a
  `SourceManifest`, any lifecycle/revocation concept for the manifest's
  own authority (as opposed to the evidence corpus's `active` field, which
  is about individual receipts, not the manifest's authorial standing), or
  any equivalent of AuthContract's target professional-disposition
  concept.
- **(d) final Git source-relative merge-result admissibility** —
  **NO-EVIDENCE-FOUND.** No PR/CI integration was found in the inspected
  spec files; dekimuhq's own scope is compilation and evaluation, not
  delivery. Combining it with Microsoft AGT/Permit0/OpenEAGO does not
  close this gap either — none of those three were found to re-resolve
  live Git merge-base ancestry the way `git-gate` does; they gate agent
  *tool calls*, not GitHub PR merges.
- **(e) runtime fact/action enforcement** — **PARTIAL, via composition
  only.** dekimuhq itself does not enforce anything at agent-action time
  (its `requires` quantifiers run over a stored evidence corpus, not a
  live tool call). Microsoft AGT/Permit0/OpenEAGO do enforce at agent
  tool-call time. No evidence was found of anyone actually wiring
  dekimuhq's obligation-satisfaction output into one of these three
  systems' policy input.
- **(f) independently recomputable evidence** — **YES, and this is the
  strongest single transition in the whole S1–S5 set.** dekimuhq's receipt
  contract (`manifestMatches`/`reproducible`/`signatureValid`, computed
  from raw manifest+facts+corpus) is a genuine, literal match to
  AuthContract's target evidence behavior, on its own — no composition
  needed for this specific transition.

**Net verdict:** this is the closest any tested composition comes to
AuthContract's full target chain, specifically because dekimuhq closes
transition (f) outright and partially closes (a). But (b), (c), and (d)
remain open, and (d) in particular — the Git PR/merge-result-bound gate —
was not found to exist anywhere in this composition, including inside
dekimuhq itself. **This does not collapse AuthContract's differentiation
claim, but it is the single strongest evidence in this scan that the
"evidence half" of that claim already has close, independently-arrived-at
open precedent**, and any future AuthContract architecture work on the
receipt/evidence side should study dekimuhq's receipt contract directly
rather than design one from scratch.

**S6 — Veridex or OpenEAGO already carries enough mandate/contract
provenance that AuthContract is redundant upstream.**
**Disposition: STRONGLY SUPPORTED — NOT ESTABLISHED.** (Corrected from
AC-024's "REFUTED" — see [§0](#0-amendment-notice-ac-024a) and [§4](#4-high-materiality-deep-dives)
for the full quote-level correction.)

Evidence, separated by class per the Evidence and Claim Register:
- **E4 direct primary-source facts:** Veridex's README literally states
  spending limits are human-configured at session creation. OpenEAGO's
  `overview.md` literally describes audit trails as spanning multiple
  regulatory frameworks for regulator examination.
- **E8 search/inspection-scope findings:** neither document was found, in
  the files inspected, to contain the phrase "regulatory mandate,"
  "external governance source," or any mechanism tracing a specific policy
  clause back to a specific regulatory provision.
- **What would need to be true for REFUTED to be the correct disposition:**
  a literal statement, in either project's primary source, affirmatively
  describing its policy/mandate content as user/operator-configured *and
  explicitly disclaiming* any source-derivation mechanism — i.e., the
  project would need to say what it is *not*, not merely omit saying what
  it is. Neither project's inspected material does this.
- **Correct disposition:** the E4 facts (human/operator-configured policy)
  combined with the E8 absence (no source-derivation mechanism found)
  together support "these two systems, as inspected, do not appear to
  carry AuthContract's upstream source-warrant half" — which is
  STRONGLY SUPPORTED — NOT ESTABLISHED, not REFUTED. REFUTED would require
  a positive, literal contradiction of AuthContract's claim, which was not
  found.

**S7 — decide.fyi's rulebook/trusted-adapter/replay model already collapses
the rule→runtime→evidence portion sufficiently that AuthContract only adds
source interpretation.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED.** Unchanged in
overall disposition, but the supporting evidence is corrected: decide.fyi's
`UNKNOWN` state is no longer counted as source-ambiguity preservation (see
[§4](#4-high-materiality-deep-dives)), and its replay mechanism is scored
PARTIAL rather than YES pending code-level confirmation of what exactly is
recomputed. What remains true and strong: hashed rulebooks, deterministic
verdicts, signed attestation, and automated daily source-drift monitoring
of decide.fyi's own policy inputs are all directly evidenced. Missing: no
PR/CI gate bound to a Git merge result; no per-fact verifier-established-
context binding distinguishing a claim's value from who asserted it.

**Net read across S1–S7 after correction:** the single biggest change from
AC-024 is that **S5 is now evaluated and is the strongest attack in the
set** — dekimuhq closes the independently-recomputable-evidence transition
outright — and **S6 is downgraded from REFUTED to STRONGLY SUPPORTED — NOT
ESTABLISHED** because the prior REFUTED verdict rested on treating a
search-absence finding as if it were a literal repository statement. No
tested composition, including the corrected S5, was found to close the
institutional-authority-standing (c) or Git-merge-result-binding (d)
transitions. The honest claim remains a **composite/seam** claim, not an
ingredient claim, and this revision's evidence makes that seam narrower and
better-evidenced than AC-024 did, not wider.

---

## 6. What AuthContract should reuse

- **The receipt/evidence contract specifically** — study
  `dekimuhq/regulation-as-code`'s `spec/receipt.md` directly. Its
  independent-recomputation contract (`manifestMatches`/`reproducible`/
  `signatureValid` from raw manifest+facts+corpus) is closer to
  AuthContract's own target receipt behavior than anything else found in
  this scan, and is already specified in enough detail to study line by
  line rather than redesign from scratch.
- **Source decomposition and structured interpretation** — TNO
  Calculemus/FLINT and Catala's approach, before designing AuthContract's
  still-unimplemented source→rule step.
- **PR/CI drift detection UX** — Loom's and Mantra's content-hash-linked
  requirement/drift model, and fiberplane/drift's spec-binding approach.
- **Compliance-control-to-policy mapping plumbing** — OSCAL Compass C2P.
- **Policy evaluation itself** — OPA, Cedar, OpenFGA.
- **Signed evidence/attestation envelopes** — DSSE and in-toto's link
  metadata format.
- **Rulebook/replay UX patterns** — decide.fyi's hash-then-replay model.

## 7. What AuthContract is trying to connect

None of the systems above, including the corrected S5 composition, were
found integrating *all* of: source citation, unresolved-state preservation,
professional/authority standing, canonical artifact digest, a PR/CI gate
bound to the actual merge result, runtime fact/action admissibility checked
against verifier-established context, and a reconstructable evidence
receipt — in one continuous, non-relocatable chain. AuthContract's target
architecture is that seam, not any one ingredient in it, and — per this
amendment's own findings — not even the two closest ingredients found
(dekimuhq's receipt contract and decide.fyi's replay model) close the
institutional-standing or Git-merge-result-binding transitions. This is
explicitly a **product/architecture target**, not a claim about the
current MVP-alpha (see [§8](#8-current-implementation-boundary)).

---

## 8. Current implementation boundary

What the current AuthContract MVP-alpha reference implementation actually
does, as of this scan:

- verifies canonical artifact identity and bindings (RFC 8785 JCS + SHA-256
  digest);
- projects a rule into its declared runtime action domain and checks
  actions against it;
- checks a PR's actual Git test-merge composition (re-resolving the live
  base ref and requiring ancestry proof), not merely the isolated PR head;
- runs a bounded runtime fact/action decision path with verifier-established
  assertion-context binding, and issues a receipt on PASS, independently
  recomputable from the raw artifact/action/fact inputs;
- all of the above for **one synthetic banking specimen**.

What it does **not** do: **broad automated natural-language source→rule
semantic verification is target behavior and is not implemented end to
end.** There is no current mechanism that reads a statute, regulation, or
contract and automatically derives or checks a rule against it — every
system in [§2](#2-what-already-exists-by-capability-layer) and
[§4](#4-high-materiality-deep-dives) that does anything in that space
(TNO/FLINT, Catala, L4, OpenFisca, dekimuhq, etc.) is currently more mature
at that specific task than AuthContract, because AuthContract has not
attempted it yet.

This matches [`docs/DEVELOPER-LANGUAGE.md`](DEVELOPER-LANGUAGE.md)'s
implementation-status discipline and the root [`README.md`](../README.md)'s
own "Current status" section — this document does not relax or contradict
either.

---

## 9. Source-evidence appendix

Compact, reproducible identity for every deep-dive and matrix system where
an immutable reference was obtainable in this scan. "SHA (via API)" means
obtained from GitHub's commit-list web page or JSON API in this session;
these were not independently re-verified with a local `git clone` and
should be treated as reported-and-cited evidence, not cryptographically
re-derived by this scan itself.

| Project | Canonical URL | Inspected | Branch/ref | Commit SHA | Files inspected | Status (if evidenced) | Evidence class |
|---|---|---|---|---|---|---|---|
| `dekimuhq/regulation-as-code` | github.com/dekimuhq/regulation-as-code | 2026-08-23 | main | `11ba12bfd6851800ab11a2c925b99ad09ba90d98` | README.md, spec/grammar.md, spec/compilation.md, spec/evidence.md, spec/receipt.md, spec/evaluation.md, profiles/gdpr/v1.md | not stated in inspected material | E4 |
| Microsoft Agent Governance Toolkit | github.com/microsoft/agent-governance-toolkit | 2026-08-23 | main | `b5705588883fac48b88cbe6fd0bd7d48c798453e` (via API) | README.md | **Public Preview** (project's own words) | E4 |
| Veridex agentic-payments | github.com/veridex-protocol | 2026-08-23 | main | `329a200afa6748c7965a6fc896b24eb6c8c25c5a` (via API, `agentic-payments` repo) | org listing, agentic-payments README, agents-treasury README | not stated in inspected material | E4 |
| OpenEAGO | github.com/finos-labs/open-eago | 2026-08-23 | main | `f03627fce810a8e0ba423147fe29a854b5fcd3b2` (via API) | README.md, docs/overview/overview.md, ROADMAP.md | not stated in inspected material | E4 |
| decide.fyi | github.com/decidefyi/decide | 2026-08-23 | main | `21ff7def1899ea75a5f02408c221fec538dc4517` (via API) | README.md, decide.fyi/resources/docs | production-binding vs. non-binding modes distinguished in-product | E4 |
| Loom | github.com/jsuppe/loom | 2026-08-23 | main | `104ac0b4e2ea8cca72db9f829a61d8b6fd66ddfc` | README.md (direct fetch after initial search miss) | active (commits within days of scan) | E4 |
| Catala | github.com/CatalaLang/catala | 2026-08-23 | master | `08832f46b26f5d3936c7b6ac156540cd90e7d500` | README.md, doc/formalization/README.md | active | E4 |
| OSCAL Compass C2P | github.com/oscal-compass/compliance-to-policy | 2026-08-23 | main | `6ec821d4c253baf85e5b4d171ee9f9fb7affc1e0` | README.md, architecture docs | active | E4 |
| Google AP2 | github.com/google-agentic-commerce/AP2 | 2026-08-23 | main | `e1ea56db72a6385bce3e5c1112b3a56ce60acb43` | README.md, src/ap2/types/mandate.py | v0.2.0 (stated in repo) | E4 |
| Permit0 | github.com/permit0-ai/permit0 | 2026-08-23 | main | `c5e8f7db3d119591d70a3a7d64d195f6d4432127` | README.md | not stated in inspected material | E4 |
| Mantra | github.com/mhatzl/mantra | 2026-08-23 | main | `f295cb88b9cc5126759b65f19e446af633783271` | README.md (direct fetch after initial search miss) | active (Rust-focused; other-language support "planned") | E4 |
| Safe Hands | github.com/arcadeai-labs/safe-hands | 2026-08-23 | main | `52088c179d78e414db1a49e98e4853eaec9a7648` | README.md (direct fetch after initial search miss) | active | E4 |
| SmartPolicy | github.com/smartpolicy-protocol/smartpolicy | 2026-08-23 | main | `534f4e382756a9e54733766a24cf447741ffd5eb` | README.md (direct fetch after initial search miss) | contracts tested, **not independently audited**, "internal pending maturity" (project's own words) | E4 |
| TNO Calculemus/FLINT | gitlab.com/normativesystems | 2026-08-23 | (GitLab; no commit SHA captured this pass) | — | Choppr / Flint Ontology / Calculemus Calculator repo pages | not stated | E4 |
| in-toto | github.com/in-toto/in-toto | 2026-08-23 | (not re-captured this pass; unchanged from AC-024) | — | README.md | active, CNCF-graduated project | E4 |
| Obligation-First | obligationfirst.org / github.com/snapsynapse/obligation-first | 2026-08-23 | (schema site, not a single repo ref) | — | schema page, GitHub examples | v0.4.1 | E4 |

Systems not in this table (Blawx, L4, Logical English, OpenFisca, Accord
Project, LegalRuleML/Akoma Ntoso, Compliance Trestle, ComplianceAsCode,
FINOS CCC/CC4AI, Conftest, OPA, Cedar, OpenFGA, Permify, Permguard, kyndryl
aiagent-portable-authorization, alibaba/open-agent-auth, Sigstore/DSSE,
fiberplane/drift, FINOS Open RegTech SIG) were inspected in the original
AC-024 pass or this amendment via README/project-page fetch without a
captured commit SHA; their matrix classification stands on that
inspection depth, recorded per-system in [§2](#2-what-already-exists-by-capability-layer),
and is not claimed to carry the same immutable-reference rigor as the rows
above.

---

## 10. Search method and limitations

**Method:** two-direction search plus adjacency terms (rules as code,
legislation as code, policy as code, compliance as code, requirements
traceability, semantic drift, agent governance, GitOps controls,
continuous compliance, warrant, mandate, obligation) across GitHub,
GitLab, and primary project/spec pages, run independently against the
Engineering Lead's seed ledger, amended once after independent review
(ADJ-AC-024) found direct-fetch verification gaps in the first pass.

**Corpus size:** at least 54 distinct candidate projects/specifications
screened; at least 33 inspected beyond search snippets using primary
README/spec/code/docs (up from 29+ in AC-024, after the four mandatory
recoveries); 33 systems represented in the comparison matrix.

**The complete screening/exclusion ledger — every one of the 54+ screened
candidates, with URL, discovery query/class, included/excluded/near-miss
disposition, reason, and inspection depth — is deposited in full in the
AC-024A Drive return record, per that work order's explicit instruction
not to substitute a summary or a "see docs/SOTA.md" pointer for it.** This
section gives the material corrections and additions only.

**Material correction from AC-024 (the central finding of this
amendment):** four repositories AC-024 reported as unlocatable —
`dekimuhq/regulation-as-code`, `mhatzl/mantra`, `arcadeai-labs/safe-hands`,
`smartpolicy-protocol/smartpolicy` — are real and were found immediately
by directly fetching their exact URLs. AC-024's method relied on search
engine results to conclude unavailability; that method has a real,
repeated coverage gap (this is now confirmed at four repositories, not
one). This amendment's method going forward: **an exact, named repository
may be reported unlocatable only after a direct URL fetch attempt fails**,
and the exact fetch attempt and its result must be recorded (see
[§9](#9-source-evidence-appendix)).

**Newly discovered comparators not in the Engineering Lead's original seed
ledger** (carried forward from AC-024, unchanged): Google's Agent Payments
Protocol (AP2), `alibaba/open-agent-auth`, FINOS Open RegTech SIG,
`fiberplane/drift`, Permify.

**Limitations:** this is a two-session (AC-024, then AC-024A), point-in-time
(2026-08-23) web and repository scan. It did not clone or execute any
comparator's code; findings come from README/doc/spec text and file
listings as fetched via web search, direct URL fetch, or the GitHub commit
API. Several commit SHAs in [§9](#9-source-evidence-appendix) were obtained
via API/webpage fetch rather than independently re-derived by cloning and
hashing locally, and are reported as such rather than presented as
cryptographically self-verified by this scan. GitHub/GitLab search-engine
coverage gaps (now confirmed at four repositories) mean this document's
remaining `NO-EVIDENCE-FOUND` rows are bounded by what direct fetch could
reach in two sessions, not by systematic repository enumeration — a future
pass should continue applying the direct-fetch-first rule to every
remaining `NO-EVIDENCE-FOUND` cell, not just the four repositories named in
AC-024A.

## 11. How to update this SOTA

1. Re-run the two-direction search in [§10](#10-search-method-and-limitations)
   with the current date, including the adjacency terms listed there.
2. **Before concluding any exact, named repository is unavailable, fetch
   its URL directly.** Do not rely on a zero-result search alone — this
   amendment exists because that rule was not followed the first time.
3. Re-verify every `NO-EVIDENCE-FOUND` row in [§3](#3-comparison-matrix) —
   a negative finding here is a search-corpus statement, not a permanent
   fact.
4. Re-run the S1–S7 composite-substitution attacks in
   [§5](#5-composite-substitution-attacks) — this is the fastest-moving
   part of the landscape.
5. When citing what a primary source "says," quote it directly and check
   the quote against the actual fetched text before publishing — this
   amendment exists partly because a paraphrase was previously presented
   as a quotation.
6. Update the scan date at the top of this document and add a dated note
   here summarizing what changed, rather than silently overwriting prior
   findings.
