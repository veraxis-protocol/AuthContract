# State of the art: what already exists around AuthContract

Scan date: 2026-08-23. Method: two-direction search (upstream source→runtime and
downstream runtime→source) across GitHub, GitLab, and primary project/spec
pages, independently re-run for AC-024 against an Engineering Lead research
seed (`SOTA-RESEARCH-LEDGER v0.1`) that is explicitly **not** treated as
authority here.

**This document is not a competitor table and does not claim AuthContract is
unique, first, or without equivalent.** It maps what capabilities already
exist in the open ecosystem, where AuthContract's target architecture
overlaps them, what to reuse instead of rebuilding, and exactly where the
current AuthContract MVP-alpha stands versus its target architecture.

Corpus and method limits: this is a point-in-time scan (2026-08-23) of
public GitHub/GitLab repositories and primary spec pages reachable through
web search and repository fetches in one research session. It is not
exhaustive, not a legal survey, and not a substitute for evaluating any
specific comparator yourself before depending on it. A negative finding
below means **"not found in the inspected ref/corpus,"** never "does not
exist." See [§9](#9-search-method-screened-candidates-and-limitations) for
the full screening/exclusion log summary and [§10](#10-how-to-update-this-sota)
for how to re-run or extend this scan.

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
| Ambiguity / unresolved state | The system can say "the source doesn't settle this" instead of guessing | Obligation-First (defeasibility framing), FLINT (partial), decide.fyi (`UNKNOWN`/review verdicts) |
| Professional/authority disposition | A domain expert or institution stands behind the rule, with standing/lifecycle | Catala (domain-expert review intent), Obligation-First (Authority→Instrument schema) — none observed to bind this to a specific software artifact's digest |
| Canonical artifact identity | The exact governed object has a content-hashed identity | Dekimu-style content-hashed manifests **not located** (see [§9](#9-search-method-screened-candidates-and-limitations)); decide.fyi (`rulebook.hash`); Loom (content-hash-linked requirements) |
| PR/CI merge-result gate | The check ran against the *actual* merge result, not just the isolated branch head | Conftest + required checks (commodity infrastructure); no comparator observed re-resolving live base-ref ancestry the way AuthContract's `git-gate` does |
| Runtime fact/action admissibility | A caller's claim is checked against independently-established context, not trusted at face value | Microsoft Agent Governance Toolkit, Permit0, Veridex, OpenEAGO, Permguard, AP2 (mandate-scoped) |
| Reconstructable evidence | A third party can recompute the verdict from raw inputs and compare | decide.fyi, in-toto, Veridex `EvidenceBundle`, Microsoft AGT audit log, AP2 signed Mandates |

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
- **[Catala](https://github.com/CatalaLang/catala)** — a DSL for deriving faithful-by-construction code from legislative text, annotated line-by-line against the law it implements, with formal default-logic semantics and a partially certified compiler.
- **[Blawx](https://github.com/Lexpedite/blawx)** — a web-based, Blockly-fronted Rules-as-Code environment over s(CASP)/Prolog; explicitly experimental/educational, MIT-licensed.
- **[L4 / Natural L4](https://github.com/smucclaw/l4-ide)** (SMU Centre for Computational Law) — a functional DSL for legal rules and contracts, with an IDE, REST/MCP decision-service exposure, and natural-language generation back out of the formal model.
- **[Logical English](https://github.com/LogicalContracts/LogicalEnglish)** — a controlled natural language that compiles to Prolog/s(CASP), used to model finance and insurance regulation text.
- **[OpenFisca](https://github.com/openfisca/openfisca-core)** — the most widely adopted open tax/benefit rules-as-code engine, with dozens of country packages (e.g. [openfisca-france](https://github.com/openfisca/openfisca-france)) turning legislation into a computable, testable model.
- **[Accord Project](https://github.com/accordproject)** (Cicero, Ergo) — Linux Foundation smart-legal-contract stack binding natural-language templates to executable clause logic.
- **[Obligation-First](https://obligationfirst.org/)** ([examples on GitHub](https://github.com/snapsynapse/obligation-first)) — an open upper schema (`Authority → Instrument → Term → Obligation`) for representing normative content across jurisdictions, explicitly *not* a rules engine — it references Catala/Blawx/OpenFisca as where the executable encoding would live.
- **LegalRuleML / Akoma Ntoso** — OASIS LegalDocML standards for legal-rule and legal-document markup. These are **standards, not implementations**; do not infer runtime behavior from the spec text alone.

**If you need to represent a rule's relationship to its source text, look at
this list before building something bespoke.**

### Compliance / control → policy bridge

- **[OSCAL Compass Compliance-to-Policy (C2P)](https://github.com/oscal-compass/compliance-to-policy)** (Python and [Go](https://github.com/oscal-compass/compliance-to-policy-go) implementations) — converts OSCAL Component Definitions into native policy-engine configuration (Kyverno, Open Cluster Management, Auditree) and converts results back into OSCAL Assessment Results, GitOps-native.
- **[Compliance Trestle](https://github.com/oscal-compass/compliance-trestle)** — CI-friendly tooling for authoring/validating OSCAL compliance artifacts in Git.
- **[ComplianceAsCode/content](https://github.com/ComplianceAsCode/content)** (formerly SCAP Security Guide) — machine-enforceable security-control content across many OS/product targets.
- **[FINOS Common Cloud Controls](https://github.com/finos/common-cloud-controls)**, extending in 2025–2026 to **CC4AI ("Common Controls for AI")** — machine-readable, technology-neutral controls for financial-services cloud and AI deployments, backed by 20+ major financial institutions and cloud providers.
- **[FINOS Open RegTech SIG](https://github.com/finos/open-regtech-sig)** — an active effort to "issue regulation as code alongside the prose," directly on-topic for AuthContract's upstream half; newly found in this scan, not in the Lead's seed list.

**Boundary observed across this whole tier:** these systems map controls to
policy IDs/engine configuration. None inspected here proves that the
generated policy is *semantically equivalent* to the authoritative prose —
that mapping is still author-asserted.

### Requirements/code traceability + CI

- **[Loom](https://github.com/jsuppe/loom)** — captures requirements from natural-language conversation, links them to code via content hashing, flags `GRAPH-DRIFT` when code diverges from its linked requirement, and produces a single CI health-score gate. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[Conftest](https://github.com/open-policy-agent/conftest)** — runs Rego assertions against structured config in CI/PR, a commodity building block many of the above systems could sit behind.
- **[fiberplane/drift](https://github.com/fiberplane/drift)** — binds markdown specs to code via tree-sitter + git and fails CI on drift; narrower than Loom (docs, not institutional rules) but the same drift-detection shape.
- GitHub/GitLab required-status-checks, branch protection, and merge-result gating are **commodity delivery infrastructure**. AuthContract's differentiation cannot be "having a merge gate" — every serious CI system has one. What AuthContract's `git-gate` specifically does — re-resolving the *current* base ref live and requiring `git merge-base --is-ancestor` proof that the evaluated SHA actually contains both the current base and the PR head — was not observed as a built-in behavior of Conftest, GitHub required checks, or GitLab merge trains by themselves; see [§5](#5-composite-substitution-attacks).

### Policy / authorization engines

- **[Open Policy Agent (OPA)](https://github.com/open-policy-agent/opa)** — general-purpose policy engine; rules/data are supplied by the caller.
- **[Cedar](https://github.com/cedar-policy/cedar)** — authorization policy language with schema validation and automated formal-analysis tooling.
- **[OpenFGA](https://github.com/openfga/openfga)** — Zanzibar-style relationship-based authorization.
- **[Permify](https://github.com/Permify/permify)** — another Zanzibar-inspired fine-grained authorization engine, discovered in this scan (not in the Lead's list); now part of FusionAuth.

All four are downstream infrastructure: they evaluate policy that something
else must supply and warrant. None of them establishes where the policy
came from.

### Agent runtime governance / consequential action control planes

This is the fastest-moving tier in the whole landscape (most of it shipped
in the last 12 months) and the one most likely to be stale by the time you
read this:

- **[Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)** — deterministic interception of agent tool calls, YAML/OPA/Cedar policy, zero-trust identity (SPIFFE/DID/mTLS), Merkle-chained tamper-evident audit log, multi-language SDKs, explicit `GovernanceDenied` records. High materiality.
- **[Permit0](https://github.com/permit0-ai/permit0)** — pre-execution, deterministic action-authorization layer for agents; every allow/block/escalate decision is replayable and signed; Apache-2.0, Rust.
- **[Veridex / agentic-payments](https://github.com/veridex-protocol)** (`@veridex/agentic-payments`, `agents-treasury`) — session-key-scoped autonomous agent payments with an 8-rule `PolicyEngine`, signed `EvidenceBundle`, multi-chain support. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[OpenEAGO](https://github.com/finos-labs/open-eago)** (FINOS Labs) — enterprise agent governance/orchestration overlay with jurisdiction enforcement, HITL, and real-time compliance checks against GDPR/DORA/EU AI Act/SR 11-7/BCBS 239/PCI-DSS/MiFID-II/EMIR. High materiality.
- **[Permguard](https://github.com/permguard/permguard)** — Git-versioned, distributed authorization engine spanning traditional systems and AI agents.
- **[kyndryl-open-source/aiagent-portable-authorization](https://github.com/kyndryl-open-source)** — reference implementation of policy-embedded credential authorization for AI agents (arXiv:2605.11487): signed credentials with machine-evaluable constraints, verified at runtime, producing signed audit decisions.
- **[Google Agent Payments Protocol (AP2)](https://github.com/google-agentic-commerce/AP2)** — **not in the Lead's seed list; found in this scan.** An industry-scale open standard (60+ launch partners including Mastercard, PayPal, Coinbase, American Express) representing every agent purchase as three signed **Mandates** (Intent, Cart, Payment), each a W3C Verifiable Credential. This is arguably the single most material downstream comparator this scan found for "mandate" vocabulary — see [§4](#4-high-materiality-deep-dives).
- **[alibaba/open-agent-auth](https://github.com/alibaba/open-agent-auth)** — **not in the Lead's seed list; found in this scan.** Enterprise framework implementing the IETF draft "Agent Operation Authorization," binding user identity to agent operations via OAuth2/OIDC/WIMSE/W3C VC with semantic audit trails.
- Other agent-governance projects screened but not deep-dived: `Runestone-Labs/gatekeeper`, `aporthq/aport-spec` (Open Agent Passport), `opena2a-standards/agent-authorization-protocol`, `better-auth/agent-auth`, `auth-agent/auth-agent` — see the [screening log](#9-search-method-screened-candidates-and-limitations).

**Boundary observed across this whole tier:** every one of these systems
governs an action against a *supplied* policy/mandate. None inspected here
was observed linking that policy back to an authoritative external source
with a citation, an unresolved-state marker, or institutional standing —
see the direct textual evidence in [§4](#4-high-materiality-deep-dives) for
Veridex and OpenEAGO specifically.

### Evidence, replay, attestation

- **[in-toto](https://github.com/in-toto/in-toto)** — signed layouts, authorized functionaries, signed link metadata, and continuous verification of a software supply chain.
- **[decide.fyi](https://github.com/decidefyi/decide)** — versioned, hashed rulebooks; deterministic verdicts; Ed25519-signed attestation bundles; replay that compares verdict/evidence/record hashes against the original run; explicit non-binding vs. production-binding modes. High materiality — see [§4](#4-high-materiality-deep-dives).
- **Sigstore** and the **[DSSE](https://github.com/secure-systems-lab/dsse)** envelope spec — the signing-envelope/attestation-format layer that in-toto and Sigstore's `cosign` both build on. Infrastructure precedent for tamper-evident evidence, not authority semantics.

---

## 3. Comparison matrix

Cell values follow the AuthContract Evidence and Claim Register: **YES**
(directly evidenced in the inspected ref), **PARTIAL** (evidenced but
narrower/different), **NO-EVIDENCE-FOUND** (searched the exact ref/corpus
and did not find it — never read as "does not exist"), **NOT-EVALUATED**
(insufficient inspection), **N/A** (out of scope), **STANDARD** (this is a
specification, not an implementation — do not infer runtime behavior).

Axes: **A** source citation/anchor · **B** structured rule representation ·
**C** unresolved/ambiguity preservation · **D** expert/professional review ·
**E** issuer/authority/standing/lifecycle · **F** canonical artifact
identity/digest · **G** projection/transpilation/conformance · **H** PR/CI
gate bound to actual merge result · **I** runtime fact provenance/freshness
· **J** closed action universe/unknown handling · **K** pre-execution
enforcement · **L** independently recomputable evidence · **M**
correction/supersession continuity · **N** current-vs-target honesty.

| System | Class | A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TNO Calculemus/FLINT | Upstream | YES | YES | PARTIAL | PARTIAL | NOT-EVAL | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Catala | Upstream | YES | YES | YES | PARTIAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Blawx | Upstream | YES | YES | PARTIAL | NOT-EVAL | NO-EV | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | YES |
| L4 / Natural L4 | Upstream | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Logical English | Upstream | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| OpenFisca | Upstream | PARTIAL | YES | NOT-EVAL | PARTIAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| Accord Project (Cicero/Ergo) | Upstream/Adjacent | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | YES | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Obligation-First | Upstream | YES | YES | PARTIAL | PARTIAL | YES | NOT-EVAL | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES |
| Regulation-as-code (`dekimuhq`) | **UNCONFIRMED** | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV | NO-EV |
| LegalRuleML / Akoma Ntoso | STANDARD | STANDARD | STANDARD | STANDARD | N/A | STANDARD | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| OSCAL Compass C2P | Upstream/Bridge | N/A | YES | NOT-EVAL | NOT-EVAL | NOT-EVAL | YES | YES | PARTIAL | NO-EV | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| Compliance Trestle | Upstream/Infra | N/A | YES | N/A | NOT-EVAL | NOT-EVAL | YES | N/A | PARTIAL | N/A | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| ComplianceAsCode/content | Upstream/Bridge | PARTIAL | YES | N/A | NOT-EVAL | NOT-EVAL | YES | YES | PARTIAL | N/A | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| FINOS Common Cloud Controls / CC4AI | Upstream standard | YES | YES | NOT-EVAL | YES | NOT-EVAL | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Loom | Adjacent/Upstream | N/A | YES | PARTIAL | N/A | NO-EV | YES | N/A | YES (health-gate) | N/A | N/A | N/A | NOT-EVAL | YES | NOT-EVAL |
| Conftest | Infrastructure | N/A | YES | N/A | N/A | N/A | N/A | N/A | PARTIAL | N/A | N/A | N/A | N/A | N/A | N/A |
| OPA | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| Cedar | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | YES (formal) | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| OpenFGA | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| Microsoft Agent Governance Toolkit | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | YES (Merkle audit) | NOT-EVAL | YES |
| Permit0 | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | YES (signed, replayable) | NOT-EVAL | NOT-EVAL |
| Veridex agentic-payments | Downstream/Runtime | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | YES (mandate version) | N/A | NO-EV | PARTIAL | YES | YES | YES (EvidenceBundle) | YES | NOT-EVAL |
| OpenEAGO | Downstream/Control-plane | NO-EV | YES | NO-EV | NOT-EVAL | PARTIAL | NOT-EVAL | N/A | NO-EV | NOT-EVAL | YES | YES | PARTIAL (blockchain audit) | NOT-EVAL | NOT-EVAL |
| Permguard | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | YES (Git-versioned policy) | N/A | NO-EV | NOT-EVAL | YES | YES | NOT-EVAL | YES | NOT-EVAL |
| kyndryl aiagent-portable-authorization | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | YES (signed decisions) | NOT-EVAL | NOT-EVAL |
| Google AP2 | Downstream/Runtime | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | YES (Mandate = VC) | N/A | NO-EV | YES (signed by wallet) | YES | YES | YES (signed Mandates) | PARTIAL | NOT-EVAL |
| alibaba/open-agent-auth | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | YES (OIDC identity) | NOT-EVAL | N/A | NO-EV | PARTIAL | YES | YES | YES (audit trails) | NOT-EVAL | PARTIAL (public beta labeled) |
| in-toto | Infrastructure | N/A | N/A | N/A | N/A | YES (functionaries) | YES (link metadata) | N/A | N/A | N/A | N/A | N/A | YES | YES | N/A |
| decide.fyi | Downstream/Decision-evidence | NO-EV | YES | YES (`UNKNOWN`) | NO-EV | NOT-EVAL | YES (`rulebook.hash`) | N/A | NO-EV | PARTIAL | YES | YES | YES (replay) | YES (snapshots) | NOT-EVAL |
| Sigstore / DSSE | Infrastructure | N/A | N/A | N/A | N/A | PARTIAL (signer identity) | N/A | N/A | N/A | N/A | N/A | N/A | YES | N/A | N/A |

Standards (LegalRuleML/Akoma Ntoso) and pure infrastructure rows
(GitHub/GitLab required checks, Conftest, OPA/Cedar/OpenFGA, Sigstore/DSSE)
are included because AuthContract's target architecture is explicitly meant
to sit *on top of* several of them, not replace them.

---

## 4. High-materiality deep dives

These ten systems (nine confirmed to exist plus one the Lead's ledger cited
that this scan could not locate) were inspected at two or more primary
files/spec surfaces, not README alone.

### TNO Calculemus/FLINT

**Strongest overlap:** exactly the upstream half of AuthContract's target
chain — Choppr decomposes source text, the FLINT Ontology gives a formal
semantics for the resulting norm frames, and Calculemus provides an
execution/reasoning loop over them, all while staying traceable to the
source sentence.
**Strongest capability where it's ahead:** a decade-plus of applied
methodology for turning real legislative/policy text into structured norm
models — far more mature than AuthContract's current MVP-alpha, which has
no automated source→rule step at all yet.
**Boundary:** no PR/CI semantic gate bound to an actual Git merge result,
and no runtime fact-admissibility/verifier-context binding, were found in
the inspected GitLab material.
**Observed absence vs. search absence:** search absence — the inspected
surfaces (Choppr README/FAQ, Flint Ontology repo, Calculemus Calculator
repo) are focused on the modeling stage; they may simply be out of scope
for delivery/runtime concerns rather than lacking them.
**Composition risk:** high — see S1 in [§5](#5-composite-substitution-attacks).

### Catala

**Strongest overlap:** line-by-line source-to-code faithfulness with formal
default-logic semantics — the most rigorous "code matches law" mechanism
found in this entire scan.
**Strongest capability where it's ahead:** a partially certified compiler
and a body of published formal-methods work; nothing in AuthContract's
current implementation approaches this level of formal assurance.
**Boundary:** Catala's own materials describe legislative-text derivation,
not a generic external-source PR-drift gate, institutional standing, or a
runtime agent-action/evidence chain.
**Observed absence vs. search absence:** search absence for the PR-gate and
runtime-evidence pieces specifically — Catala's own scope is narrower by
design (it targets socio-fiscal legislative computation), so this is not
a criticism of the project, just a boundary.

### `dekimuhq/regulation-as-code` — **could not be located; correction to the Lead's ledger**

The Engineering Lead's seed ledger described this as "VERY HIGH
MATERIALITY," citing a versioned `SourceManifest`, typed facts, a
content-hashed IR, and signed reproducible evaluation receipts — a
combination that, if it existed as described, would be the single closest
comparator to AuthContract's full chain found anywhere in this scan.

**This scan could not find this repository.** Search attempts, exact terms
used: `"dekimuhq regulation-as-code github"`, `""dekimu" regulation-as-code
OR SourceManifest github"`, `"github.com dekimuhq"`,
`""regulation-as-code" "SourceManifest" github repository"`. All four
returned no matching repository, user, or organization under this name.
GitHub's own topic pages for `regulation` and `compliance-as-code` do not
surface it either.

Per this document's own evidence rule, this is reported as
**NO-EVIDENCE-FOUND in the inspected corpus**, not as proof the project
never existed (it could be private, renamed, deleted, or the name/owner in
the seed ledger could be inaccurate). It is flagged prominently because the
Lead's ledger treated it as a load-bearing, very-high-materiality
comparator, and that specific claim cannot currently be independently
verified. Any future scan should re-attempt this search and, if the
Engineering Lead has direct knowledge of the repository's real location,
that should be supplied directly rather than re-derived from web search.

### OSCAL Compass Compliance-to-Policy (C2P)

**Strongest overlap:** the closest thing in this scan to an operational
"compliance prose → executable policy → back to compliance evidence" GitOps
pipeline, with both Python and Go implementations and multiple supported
policy-engine backends (Kyverno, Open Cluster Management, Auditree).
**Strongest capability where it's ahead:** production GitOps integration
maturity (Tekton pipelines, Agile Authoring Pipelines) that AuthContract's
MVP-alpha does not have.
**Boundary:** C2P maps OSCAL Component Definitions to policy IDs and plugin
configuration. Nothing inspected proves the generated policy is
semantically equivalent to the authoritative control text — that mapping
is still author-asserted, exactly as the Lead's ledger flagged.
**Observed absence vs. search absence:** partially observed — the README
and architecture docs describe ID/mapping-based bridging explicitly, which
is a positive description of *how* it works, not merely an absence.

### Loom

**Strongest overlap:** requirement↔code content-hash linking, `GRAPH-DRIFT`
detection, and a single CI health-score gate — structurally close to what a
"has the implementation drifted from what it's supposed to satisfy" check
needs, and the closest developer-traceability analog found to AuthContract's
own Git merge-result admissibility idea (drift detection instead of
merge-result binding).
**Strongest capability where it's ahead:** empirically tuned drift
detection (reported 100% recall / 12% false-positive rate in its own
materials) and small-model task decomposition — engineering maturity
AuthContract's MVP-alpha does not have.
**Boundary:** Loom's linked "requirements" are project requirements
captured from conversation, not institutionally warranted external norms;
no source-citation, authority-standing, or consequential-action-evidence
chain was found.
**Note on method:** an initial web search for `jsuppe/loom` failed to
surface the repository at all (it returned an unrelated `sfw/loom`
project); only a direct fetch of the exact URL found it. This is logged
explicitly in [§9](#9-search-method-screened-candidates-and-limitations) as
a search-tool gap, not an object gap — the same category of failure that
caused the prior landscape scan to miss Veridex, now observed again at
smaller scale and caught by cross-checking rather than trusting one search.

### Microsoft Agent Governance Toolkit

**Strongest overlap:** deterministic pre-execution interception of agent
tool calls against YAML/OPA/Cedar policy, with a Merkle-chained
tamper-evident audit log and an explicit `GovernanceDenied` record shape —
directly adjacent to AuthContract's runtime fact/action admissibility half.
**Strongest capability where it's ahead:** production-grade multi-language
SDKs, zero-trust identity (SPIFFE/DID/mTLS) integration, and coverage
claims against the OWASP Agentic Top 10 — well beyond AuthContract's
one-specimen MVP-alpha scope.
**Boundary:** policy is supplied by the operator; no source→policy semantic
warrant (why this YAML/OPA/Cedar policy is what the governing regulation or
contract actually requires) was found in the inspected README, CHARTER.md,
or policy-engine README.
**Observed absence vs. search absence:** search absence — the toolkit's own
scope statement is about runtime enforcement, not source derivation, so
this is a boundary by design, not a flaw.

### Permit0

**Strongest overlap:** the phrase-level pitch — "the action authorization
layer — pre-execution, deterministic, policies included" — is close to
AuthContract's own runtime half, and Permit0's "every block, allow, and
escalation is replayable, signed, and grounded in an owned policy" directly
overlaps AuthContract's evidence-recomputation goal.
**Strongest capability where it's ahead:** production packaging (action
taxonomy, ready-made integration packs for Claude Code/OpenClaw/Outlook/
Gmail) that AuthContract does not attempt.
**Boundary:** "grounded in an owned policy" means author-owned/configured,
not institutionally sourced; no source-citation or authority-standing
mechanism was found.

### Veridex / agentic-payments

**Strongest overlap:** a versioned mandate object, an 8-rule `PolicyEngine`
producing allow/deny/escalate verdicts, and a signed `EvidenceBundle` with
multiple storage backends — the closest single system in this scan to
AuthContract's runtime decision + receipt half.
**Strongest capability where it's ahead:** real multi-chain payment
execution (EVM, Solana, Aptos, Sui, Starknet, Stacks), ERC-8004 on-chain
identity, and eight production evidence-storage backends — capabilities
entirely outside AuthContract's scope.
**Boundary — directly observed, not just search-absent:** a direct fetch of
the repository content states plainly that policy rules "appear
author-defined based on autonomous-agent safety practices rather than
regulatory mandates" and that "human spending limits originate entirely
from the wallet creator's configuration, not external governance sources."
This is read directly off the primary source, not inferred from its
absence. This independently confirms and sharpens the Lead's ledger's own
finding.
**Composition risk:** tested directly as S6 — see [§5](#5-composite-substitution-attacks); **REFUTED**.

### OpenEAGO

**Strongest overlap:** an explicit "normative governance layer" description
— jurisdiction enforcement, risk scoring, HITL gates, and audit anchoring
sitting on top of A2A/MCP agent traffic, plus real-time compliance checks
against a long list of named financial regulations (GDPR, DORA, EU AI Act,
SR 11-7, BCBS 239, PCI-DSS, MiFID-II, EMIR).
**Strongest capability where it's ahead:** breadth of named regulatory
frameworks addressed and FINOS-backed cross-institution collaboration —
AuthContract currently has zero regulatory-framework-specific coverage.
**Boundary — directly observed, not just search-absent:** a direct fetch of
`docs/overview/overview.md` finds audit described as "immutable audit
trails spanning multiple regulatory frameworks for examination by FCA,
MAS, and FinCEN," which is *recording* compliance, not *tracing* a policy's
provenance back to a specific clause of a specific regulation. The document
provides no mechanism for that trace, and does not address ambiguous or
conflicting regulatory interpretation.
**Composition risk:** tested directly as S6 — see [§5](#5-composite-substitution-attacks); **REFUTED**.

### decide.fyi

**Strongest overlap:** the closest system in this scan to AuthContract's
rule→runtime→evidence half specifically — a versioned, hashed rulebook
(`rulebook.hash`), deterministic verdicts, `input_hash`, Ed25519-signed
attestation bundles, replay that compares hashes against the original run
rather than logs/screenshots, and an explicit non-binding vs.
production-binding distinction.
**Strongest capability where it's ahead:** a live, production decision API
(refund/cancel/trial/return policy decisions) with daily automated
monitoring — a GitHub Action hashes vendor policy pages every 24 hours and
opens an issue if a source page changes — a concrete, working instance of
exactly the kind of source-drift detection AuthContract's target
architecture describes only conceptually.
**Boundary:** rulebooks are supplied/curated by decide.fyi's operators;
no PR/CI semantic gate bound to a Git merge result, and no per-fact
verifier-established-context binding (distinguishing a claim's value from
who asserted it and how fresh it is) beyond deterministic hash-based
replay, were found in the inspected docs.
**Composition risk:** tested directly as S7 — see [§5](#5-composite-substitution-attacks); **STRONGLY SUPPORTED — NOT ESTABLISHED**.

---

## 5. Composite-substitution attacks

The question is not "does any one repository already do everything
AuthContract targets" — it's whether a *stack* of existing open systems
already collapses AuthContract's differentiation claim. Each hypothesis
below was tested against this scan's actual primary-source findings, not
assumed.

**S1 — TNO Calculemus/FLINT + Git/CI + OPA/Cedar + in-toto reproduces the
full AuthContract architecture.**
Verdict: **STRONGLY SUPPORTED — NOT ESTABLISHED.** Positive evidence: each
individual layer is real and mature (FLINT for source→structured
interpretation, OPA/Cedar for runtime policy evaluation, in-toto for
signed supply-chain evidence). Missing transition: no evidence any of these
four systems have been integrated with each other for this purpose, and
specifically no evidence of (a) a PR/CI gate bound to the live-resolved
Git merge-result composition the way `git-gate` does, or (b) runtime fact
checks bound to verifier-established context rather than the policy
engine's caller-supplied input. What to reuse: FLINT's source-decomposition
methodology is directly relevant to AuthContract's still-unimplemented
source→rule step.

**S2 — Catala/L4 + Conftest/GitHub required checks + a runtime policy
engine + in-toto reproduces it.**
Verdict: **STRONGLY SUPPORTED — NOT ESTABLISHED.** Same shape as S1: strong
individual pieces (Catala/L4 for B/D/G, Conftest/required-checks for a
commodity PR gate, a runtime engine for J/K, in-toto for L), no evidence of
integration, and specifically no evidence any composed system re-resolves
live merge-base ancestry rather than trusting the isolated PR head.

**S3 — OSCAL + C2P + OPA/Cedar + GitHub + evidence/attestation reproduces
it for enterprise controls.**
Verdict: **STRONGLY SUPPORTED — NOT ESTABLISHED**, and the *closest* of the
upstream compositions specifically for enterprise-control (not general
statutory) domains — C2P's GitOps pipeline integration is real and
operational today. Missing transition: semantic-equivalence proof between
control prose and generated policy remains author-asserted, exactly as in
S1/S2.

**S4 — Obligation-First + an executable encoding (Catala/Blawx/OpenFisca) +
a runtime governor + in-toto reproduces it.**
Verdict: **OPEN.** Obligation-First is explicitly designed to be composed
this way (it references executable encodings as a downstream layer it
deliberately does not implement), so the composition is architecturally
plausible. But no evidence was found of anyone having actually built this
specific stack end to end — this is a design compatibility observation, not
an observed working system.

**S5 — `dekimuhq` Regulation-as-Code + Microsoft AGT/Permit0/OpenEAGO +
in-toto/receipt systems reproduces it.**
Verdict: **NOT EVALUATED.** The first component's existence could not be
confirmed in this scan (see the [`dekimuhq` deep dive](#dekimuhqregulation-as-code--could-not-be-located-correction-to-the-leads-ledger)
above) — this hypothesis cannot be assessed until that repository is
located or the seed ledger's citation is corrected. Independent of that gap,
the second-stage components (Microsoft AGT, Permit0, OpenEAGO) were each
directly inspected and none independently supplies source-to-rule semantic
warrant, so even a best-case resolution of the first component would still
leave that specific transition unestablished.

**S6 — Veridex or OpenEAGO already carries enough mandate/contract
provenance that AuthContract is redundant upstream.**
Verdict: **REFUTED**, with direct primary-source evidence (not search
absence). Veridex's own repository content states its policy rules are
author-defined and spending limits come from wallet-creator configuration,
not external governance sources. OpenEAGO's own architecture overview
describes audit as recording compliance activity, not tracing a policy
back to its regulatory origin, and provides no ambiguity/conflict-resolution
mechanism. Both are read directly off primary sources fetched during this
scan.

**S7 — decide.fyi's rulebook/trusted-adapter/replay model already collapses
the rule→runtime→evidence portion sufficiently that AuthContract only adds
source interpretation.**
Verdict: **STRONGLY SUPPORTED — NOT ESTABLISHED.** This is the strongest
runtime/evidence comparator this scan found — hashed rulebooks,
deterministic verdicts, signed replay, and even automated source-drift
monitoring for its own policy inputs are all directly evidenced. What
remains missing: (a) no PR/CI gate bound to an actual Git merge result, and
(b) no per-fact verifier-established-context binding distinguishing a
claim's value from who asserted it and how fresh it is, beyond
deterministic hash-based replay of the whole input. If a future AuthContract
architecture revision wants to narrow scope, decide.fyi's rulebook/replay
model is the closest existing pattern to study or build on top of, rather
than reinvent.

**Net read across S1–S7:** no tested composition was found to fully
reproduce AuthContract's target chain, and two hypotheses that could have
collapsed the runtime half specifically (S6) were **refuted with direct
evidence** rather than merely unconfirmed. But every individual link in the
chain has at least one, and usually several, mature open precedents. The
honest claim is a **composite/seam** claim, not an ingredient claim — see
[§6](#6-what-authcontract-should-reuse) and [§8](#8-current-implementation-boundary).

---

## 6. What AuthContract should reuse

Rebuilding any of the following inside AuthContract would be wasted effort
given the state of this landscape:

- **Source decomposition and structured interpretation** — study TNO
  Calculemus/FLINT and Catala's approach before designing AuthContract's
  still-unimplemented source→rule step.
- **PR/CI drift detection UX** — Loom's content-hash-linked
  requirement/drift model and fiberplane/drift's spec-binding approach are
  worth studying for the developer-facing side of a semantic gate.
- **Compliance-control-to-policy mapping plumbing** — OSCAL Compass C2P
  already solves the "control ID → policy engine config" problem; don't
  re-derive it for regulated-industry use cases.
- **Policy evaluation itself** — OPA, Cedar, and OpenFGA are mature,
  independently formally-analyzed (Cedar) engines; AuthContract's runtime
  layer should sit on top of one of these rather than reinvent a policy
  language.
- **Signed evidence/attestation envelopes** — DSSE and in-toto's link
  metadata format are a reasonable target for AuthContract's own receipt
  serialization instead of a bespoke signature envelope.
- **Rulebook/replay UX patterns** — decide.fyi's hash-then-replay model is
  the closest existing pattern to AuthContract's own "recompute the receipt
  from raw inputs and compare" goal.

## 7. What AuthContract is trying to connect

None of the systems above were found integrating *all* of: source citation,
unresolved-state preservation, professional/authority standing, canonical
artifact digest, a PR/CI gate bound to the actual merge result, runtime
fact/action admissibility checked against verifier-established context, and
a reconstructable evidence receipt — in one continuous, non-relocatable
chain. AuthContract's target architecture is that seam, not any one
ingredient in it. This is explicitly a **product/architecture target**, not
a claim about the current MVP-alpha (see [§8](#8-current-implementation-boundary)).

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
(TNO/FLINT, Catala, L4, OpenFisca, etc.) is currently more mature at that
specific task than AuthContract, because AuthContract has not attempted it
yet.

This matches [`docs/DEVELOPER-LANGUAGE.md`](DEVELOPER-LANGUAGE.md)'s
implementation-status discipline and the root [`README.md`](../README.md)'s
own "Current status" section — this document does not relax or contradict
either.

---

## 9. Search method, screened candidates, and limitations

**Method:** two-direction search (Direction A: source/statute/regulation/
contract/control → interpretation → executable rule → authority → CI/merge
→ runtime → evidence; Direction B: agent action/payment/authorization/
mandate/policy/audit/evidence → governing object → provenance/source/
authority basis), plus adjacency terms (rules as code, legislation as code,
policy as code, compliance as code, requirements traceability, semantic
drift, agent governance, GitOps controls, continuous compliance, warrant,
mandate, obligation) across GitHub, GitLab, and primary project/spec pages,
run independently against the Engineering Lead's seed ledger rather than
reusing its conclusions.

**Corpus size:** at least 54 distinct candidate projects/specifications
screened by title/README/project page; at least 29 inspected beyond search
snippets using primary README/spec/code/docs; 30 systems represented in the
comparison matrix above (including one explicitly flagged as unconfirmed);
10 systems inspected at two or more primary surfaces (README plus at least
one more file, doc, or spec page).

**Material corrections to the Engineering Lead's seed ledger:**

1. `dekimuhq/regulation-as-code`, cited as "VERY HIGH MATERIALITY," could
   not be located under that name after four distinct search attempts
   (exact terms logged in [§4](#4-high-materiality-deep-dives)). Reported
   as NO-EVIDENCE-FOUND, not nonexistence.
2. `Loom` at `jsuppe/loom` **is real** and matches the Lead's description
   closely, but a naive web search for it failed to surface the repository
   at all (returning an unrelated `sfw/loom` project instead); only a
   direct URL fetch found it. This is logged as a search-tool gap, the same
   category of failure that caused the prior scan to miss Veridex.
3. `arcadeai-labs/safe-hands` and `smartpolicy-protocol/smartpolicy`,
   listed in the seed ledger as "mandatory validation targets," could not
   be located under those names. Reported as NO-EVIDENCE-FOUND.

**Newly discovered comparators not in the seed ledger:** Google's
**[Agent Payments Protocol (AP2)](https://github.com/google-agentic-commerce/AP2)**
(industry-scale mandate/Verifiable-Credential standard, arguably the most
material single new finding of this scan), **[alibaba/open-agent-auth](https://github.com/alibaba/open-agent-auth)**
(IETF-draft-based agent operation authorization), **[FINOS Open RegTech SIG](https://github.com/finos/open-regtech-sig)**,
**[fiberplane/drift](https://github.com/fiberplane/drift)**, and
**[Permify](https://github.com/Permify/permify)**.

**Additional candidates screened lightly (title/README only) and excluded
as not materially closer than the systems above:** `sfw/loom` (unrelated
"AI harness" project, name collision only), `opena2a-standards/agent-authorization-protocol`,
`better-auth/agent-auth` and `agent-auth-protocol`, `auth-agent/auth-agent`,
`swedishembedded/open-agent-api`, `the-open-agent/openagent`,
`eclipse-tractusx/ssi-authority-schema-registry`, `snyk/driftctl`,
`qq3g7bad/shtracer`, `yesilzeytin/JanusTrace`, the `spec-sync` GitHub Action,
the SpecKit `CI Guard` extension, `oasdiff`, `finos/compliant-financial-infrastructure`,
`bitrefill/awesome-agentic-payments` (a curated list, useful as a further
discovery seed rather than a comparator itself), `ArcadeAI/arcade-mcp`,
`Runestone-Labs/gatekeeper`, `aporthq/aport-spec` (Open Agent Passport),
`agentrust-io/awesome-ai-governance`. None of these were found to be
materially closer to AuthContract's full target chain than the systems
already deep-dived above; all are one-line-screened rather than fully
inspected, so treat their exclusion as provisional, not final.

**Limitations:** this is a single-session, point-in-time (2026-08-23) web
and repository scan. It did not clone or execute any comparator's code; all
findings come from README/doc/spec text and file listings as fetched. Some
repositories described in secondary sources (blog posts, press releases)
could not be independently confirmed at their primary source and are
labeled `NOT-EVALUATED` rather than assumed. GitHub/GitLab search-engine
coverage gaps (see the Loom finding above) mean this document's absence
claims are bounded by what web search and direct fetches actually surfaced
in one session, not by systematic repository enumeration.

## 10. How to update this SOTA

1. Re-run the two-direction search in [§9](#9-search-method-screened-candidates-and-limitations)
   with the current date, including the adjacency terms listed there.
2. Re-verify every `NO-EVIDENCE-FOUND` row in [§3](#3-comparison-matrix) —
   a negative finding here is a search-corpus statement, not a permanent
   fact, and is the most likely part of this document to have changed.
3. Directly fetch (don't just search) any repository this document cites,
   since search-engine coverage gaps caused at least one real, matching
   repository (`jsuppe/loom`) to be missed in this scan.
4. Re-run the S1–S7 composite-substitution attacks in
   [§5](#5-composite-substitution-attacks) — this is the fastest-moving
   part of the landscape (most of Tier E shipped in the 12 months before
   this scan).
5. Update the scan date at the top of this document and add a dated note
   here summarizing what changed, rather than silently overwriting prior
   findings.
