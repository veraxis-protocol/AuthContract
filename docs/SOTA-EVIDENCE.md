# SOTA evidence record: full research substrate

> **This is the evidence appendix, not the developer-facing landscape doc.**
> For the 90-second orientation, quadrant, capability map, and
> build/reuse/avoid guidance, start at [`docs/SOTA.md`](SOTA.md) instead.
> Everything below is the same full audit trail moved out of the primary
> reading path by AC-027 (developer-centric SOTA rearchitecture) — nothing
> was shortened, reworded for tone, or reclassified in that move; only its
> location and this heading/banner changed. AC-024 through AC-024D content
> and dispositions are otherwise byte-identical to the pre-AC-027 document.

Scan date: 2026-08-23 (amended 2026-08-23, AC-024A; narrow evidence closure
2026-08-23, AC-024B; final narrow evidence-class literalness closure
2026-08-23, AC-024C). Method: two-direction search (upstream source→runtime
and downstream runtime→source) across GitHub, GitLab, and primary
project/spec pages, independently re-run against an Engineering Lead
research seed that is explicitly **not** treated as authority here, and
re-audited three times after independent review found real
evidence-integrity defects in earlier passes. Those defects and their
repairs are listed in [§0](#0-amendment-notices).

**This document is not a competitor table and does not claim AuthContract
is unique, first, or without equivalent.** It maps what capabilities
already exist in the open ecosystem, where AuthContract's target
architecture overlaps them, what to reuse instead of rebuilding, and
exactly where the current AuthContract MVP-alpha stands versus its target
architecture.

**Corpus accounting (exact, reconciled in AC-024B):** 56 distinct
candidates screened; 33 inspected beyond search snippets using primary
README/spec/code/docs; 33 systems represented in the comparison matrix in
[§3](#3-comparison-matrix). See [§10](#10-search-method-and-limitations)
for the method and [§11](#11-how-to-update-this-sota) to extend it.

Corpus and method limits: this is a point-in-time scan (2026-08-23) of
public GitHub/GitLab repositories and primary spec pages reachable through
web search, direct repository fetch, and (for some systems) the GitHub
commit API or commit-history web page, across three research sessions. It
is not exhaustive, not a legal survey, and not a substitute for evaluating
any specific comparator yourself before depending on it. A negative
finding below means **"not found in the inspected ref/corpus, and not
established to close that transition,"** never "does not exist" or
"categorically does not close" — see [§0](#0-amendment-notices) for
concrete cases where that distinction mattered and was previously stated
too strongly.

**A note on inspection rigor.** Cells and claims in this document do not
all carry equal evidentiary weight. Where a cell is backed by a direct
file fetch and quote, that is stated and cited in [§4](#4-high-materiality-deep-dives)
or [§9](#9-source-evidence-appendix). Where a cell rests on a shallower
README-level pass, it is scored more conservatively (`PARTIAL`,
`NOT-EVALUATED`, or `NO-EVIDENCE-FOUND` rather than `YES`) and
[§9](#9-source-evidence-appendix) says so per project. This document does
not claim uniform primary-source rigor across every cell — see the
correction in [§0](#0-amendment-notices) item 7.

---

## 0. Amendment notices

### AC-024A (first amendment)

The original AC-024 candidate was returned for amendment because four
repositories it called unavailable — `dekimuhq/regulation-as-code`,
`mhatzl/mantra`, `arcadeai-labs/safe-hands`, `smartpolicy-protocol/
smartpolicy` — are real and were found immediately by directly fetching
their exact URLs (AC-024 had relied on web-search zero-result findings,
which have a real, repeated coverage gap). All four are inspected in this
document. `dekimuhq/regulation-as-code` was deep-dived at six spec files
plus its GDPR profile and is treated as serious bridge/evidence precedent
for AuthContract's canonical-digest-and-receipt mechanics specifically.
S5, left `NOT EVALUATED` in AC-024 because dekimuhq appeared unlocatable,
was executed. A misattributed quotation about Veridex's README was
corrected, and several A–N matrix cells that had scored a neighboring
capability as if it satisfied the literal axis were downgraded.

### AC-024B (this amendment — narrow evidence closure)

Independent review of the AC-024A candidate (ADJ-AC-024A) accepted the
engineering mechanics and the material AC-024A repairs, but returned the
content for a further narrow amendment on six residual defects, all
repaired in this revision:

1. **The A–N matrix still contained neighboring-capability substitutions**
   in specific, named cells: `dekimuhq`'s J (typed facts/obligations
   scored as if they were a mediated *action* universe) and N (spec
   versioning scored as if it were an explicit current-vs-target
   distinction); Google AP2's I (a signed mandate scored as if it were
   runtime *fact* provenance); and Sigstore/DSSE's L (a signing envelope
   scored as if it were independently recomputable *verdict* evidence
   from raw decision inputs). All four are corrected in
   [§3](#3-comparison-matrix), and the M, G, F, and J axes were
   re-audited across every row that used versioning, compilation, content
   hashing, or a benchmarked command list as if it automatically
   satisfied a stricter axis.
2. **The source-evidence appendix omitted many matrix systems**, grouping
   them into one prose sentence instead of giving each an explicit row.
   [§9](#9-source-evidence-appendix) now has one row per matrix/deep-dive
   system, honestly marked "not captured" where no SHA/date/status was
   obtained, rather than omitted.
3. **Two canonical URLs pointed at an organization root instead of the
   exact repository**: Veridex was cited as `github.com/veridex-protocol`
   instead of `github.com/veridex-protocol/agentic-payments`, and Kyndryl
   was cited as `github.com/kyndryl-open-source` instead of
   `github.com/kyndryl-open-source/aiagent-portable-authorization`. Both
   are corrected throughout, with fresh commit SHAs captured directly
   from the exact repository.
4. **Unsupported comparative/maturity language was removed or narrowed**:
   OpenFisca's "most widely adopted" superlative (not established by the
   inspected README) is replaced with a bounded factual description; the
   §1 table's "Mature open precedent found" column header, which implied
   maturity across systems explicitly labeled Public Preview or
   unaudited, is relabeled "Open precedent found in inspected corpus";
   dekimuhq's "closest comparator" framing is now explicitly scoped to
   the canonical-digest/receipt mechanics comparison, not a general
   market ranking.
5. **S6's disposition was directionally inverted.** S6 asks whether
   Veridex or OpenEAGO already carry enough provenance to make
   AuthContract redundant upstream. The evidence found is counterevidence
   to that hypothesis (operator-configured policy, no source-derivation
   mechanism found), not support for it, and a search-absence finding
   cannot REFUTE a hypothesis either. S6's hypothesis disposition is now
   **OPEN**, with a separately labeled counter-finding at STRONGLY
   SUPPORTED — NOT ESTABLISHED. The same directionality check — does the
   disposition attach to the literal stated hypothesis, not to whichever
   evidence paragraph reads strongest — was re-applied to S1–S7.
6. **Claim-ceiling wording overstated search evidence in places.** "This
   does not collapse AuthContract's differentiation claim" is replaced
   with language that S5 does not *establish* collapse/full equivalence
   in the inspected corpus. Sentences saying a comparator "does not
   close" a transition based only on inspection/search absence now say
   "was not found/established to close." The corpus accounting is
   reconciled to the exact number (56 screened), not "54+".

None of these corrections required rewriting the document's overall
shape or reopening the landscape research. They make the same underlying
findings more precisely and honestly stated.

### AC-024C (final narrow amendment — evidence-class literalness closure)

Independent review of the AC-024B candidate (ADJ-AC-024B) accepted the
matrix-semantics and evidence-ledger repairs, but returned the content for
one final, narrow amendment: two named evidence-class misattributions, plus
a full targeted sweep for every project-attributed quotation in the
document, checking that each literally survives inspection of its recorded
primary source rather than being a paraphrase presented as a direct quote.

**The two named load-bearing repairs:**

1. **Microsoft AGT's institutional-authority sentence.** The prior text
   presented "does not cite institutional authority for the actual
   policies it enforces" as a direct, quoted E4 fact from the README at
   commit `b5705588883fac48b88cbe6fd0bd7d48c798453e`. A targeted re-fetch
   of that exact commit found neither "institutional authority" nor "does
   not cite" anywhere in the text. That sentence is this document's own
   analyst inference from genuine E4 facts (policy is user-supplied via
   `policy="policy.yaml"`; `safe_tool` evaluates and logs against that
   supplied policy; the frameworks named are compliance *mappings*, not
   claimed derivation sources) — restated in [§4](#4-high-materiality-deep-dives)
   as an explicitly labeled, evidence-bounded inference, separated from the
   literal E4 quotes that support it.
2. **In-toto's F-axis score.** The prior matrix cell scored F = YES using
   "link metadata content hash" as evidence. Link metadata records hashes
   of a step's *materials and products* (execution evidence), not a
   separate content-hash/digest of the *governing layout itself*, which
   in-toto's own documentation describes as authenticated by functionary
   **signature**. F is rescored NO-EVIDENCE-FOUND in [§3](#3-comparison-matrix)
   and [§2](#2-what-already-exists-by-capability-layer); the L-axis score
   (independently recomputable layout/materials/products verification) is
   unaffected and unchanged, since L concerns replay of recorded steps, not
   identity of the governing layout. No S1/S2 composite-attack narrative
   references in-toto's F score (both reference its L-axis evidence only),
   so no further narrative change was needed there.

**Targeted quote/inference sweep — additional defects found and corrected**
(not individually named in ADJ-AC-024B, but within the sweep's explicit
scope that "every project-attributed quote/direct/literal/E4 statement must
literally survive inspection of its recorded primary source"):

| # | Project / location | Old wording | New wording | Evidence class | Source/ref |
|---|---|---|---|---|---|
| 1 | Microsoft AGT, §4 | "does not cite institutional authority for the actual policies it enforces" presented as direct quoted E4 fact | Separated into genuine E4 direct quotes ("Govern any tool function in two lines"; `safe_tool` evaluation/logging behavior) plus an explicitly labeled analyst inference (institutional-authority conclusion) | E4 (quotes) / analyst inference, E8-bounded (conclusion) | README.md @ `b5705588883fac48b88cbe6fd0bd7d48c798453e`, direct re-fetch this cycle |
| 2 | in-toto, §2 & §3 | F = YES ("link metadata content hash") | F = NO-EVIDENCE-FOUND (link metadata is execution evidence, not layout identity/digest) | E4 (absence of a described layout-digest mechanism, directly observed) | github.com/in-toto/in-toto README, direct fetch this cycle |
| 3 | FINOS Open RegTech SIG, §2 | quoted as "issue regulation as code alongside the prose" | not a quotation; real literal text is "a community of people interested in creating open source solutions for regulatory and compliance issues" | E4 | github.com/finos/open-regtech-sig, direct fetch this cycle |
| 4 | decide.fyi, §4 (M-axis) | quoted as "immutable tenant-scoped snapshot metadata" | real literal text is "immutable tenant-scoped snapshots" (word "metadata" not present); full sentence restored | E4 | github.com/decidefyi/decide README, direct fetch this cycle |
| 5 | Permit0, §2 & §3 (M-axis) | quoted as decisions being "replayable and signed" | not a verbatim compound phrase; real text separately uses "canonical, append-only vocabulary" / "canonical action taxonomy" (verbatim, confirmed) and "signed audit trail" (verbatim) | E4 | github.com/permit0-ai/permit0 README, direct fetch this cycle |
| 6 | FINOS Common Cloud Controls, §2 & §3 & §9 | "extending in 2025–2026 to CC4AI ('Common Controls for AI')"; "backing from 20+ named financial institutions and cloud providers" | both removed as unsupported by the inspected README; replaced with the seven named Steering Committee organizations actually stated (Citi, LSEG, Morgan Stanley, ScottLogic, Red Hat, RBC, BlackRock); row label "/ CC4AI" removed | E8 (not found in inspected README — does not establish falsity of the claim elsewhere, only that this document's citation of it to this source was incorrect) | github.com/finos/common-cloud-controls README, direct fetch this cycle |
| 7 | SmartPolicy, §2 & §9 | quoted as "internal pending maturity"; paraphrased as "not independently audited" | real literal text is "NOT audited; internal until mature — no public repo or registry listings yet" | E4 | github.com/smartpolicy-protocol/smartpolicy README, direct fetch this cycle |

**Quotes checked in this sweep and confirmed already accurate, no change
made:** Veridex's "Human sets limits → Agent gets session key → Makes
autonomous payments" and "Give your agent a wallet with human-set spending
limits" (both re-verified verbatim against the live README this cycle);
OpenEAGO's "Immutable audit trails spanning multiple regulatory frameworks
for examination by FCA, MAS, and FinCEN" and "Audit Continuity: Blockchain
trails provide immutable records across all interactions" (both re-verified
verbatim against `docs/overview/overview.md` this cycle); alibaba/open-agent-auth's
"public beta" label (re-verified verbatim: "Open Agent Auth is in public
beta"); dekimuhq's observed absence of an "unresolved"/"undetermined"/
"ambiguous" evaluation state in `spec/evaluation.md` (previously verified by
direct read in AC-024A, not re-fetched again this cycle).

None of these seven corrections change any hypothesis disposition in
[§5](#5-composite-substitution-attacks) or any previously-accepted AC-024B
repair; all AC-024B repairs (dekimuhq J/N, AP2 I, DSSE/Sigstore L split,
G/J/M re-audit, per-project evidence-appendix rows, exact Veridex/Kyndryl
URLs, S6 hypothesis/counter-finding separation, corpus accounting) are
preserved unchanged.

### AC-024D (final consistency amendment — Microsoft E8 wording)

Independent review (ADJ-AC-024C) found one residual cross-section
inconsistency: the §2 Microsoft Agent Governance Toolkit bullet stated the
README "explicitly does not claim to enforce policies derived from those
frameworks," overstating an inspection absence as an explicit source
statement, inconsistent with §4's own E8-bounded framing of the identical
evidence. §2 now reads: the README maps its controls to the four named
frameworks as compliance mappings and users author their own YAML
policies; in the inspected README, no claim was found that those
frameworks are the derivation source of the enforced policy. No matrix,
S1–S7, claim-ceiling, or corpus change was required or made.

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

| Layer | What it needs to prove | Open precedent found in inspected corpus |
|---|---|---|
| Source → structured interpretation | The rule is derived from a citable, quoted normative source | TNO Calculemus/FLINT, Catala, Blawx, L4, Logical English, OpenFisca, Obligation-First |
| Ambiguity / unresolved state | The system can say "the source doesn't settle this" instead of guessing | Obligation-First (defeasibility framing, PARTIAL). **No system inspected was confirmed to distinguish source-interpretation ambiguity from runtime evidence-missing/UNKNOWN** — see the corrected C-axis notes in [§3](#3-comparison-matrix). |
| Professional/authority disposition | A domain expert or institution stands behind the rule, with standing/lifecycle | Catala (domain-expert review intent), Obligation-First (Authority→Instrument schema, PARTIAL) — none observed to bind this to a specific software artifact's digest; identity/OIDC/authorized-functionary mechanisms in the runtime tier are **not** institutional standing |
| Canonical artifact identity | The exact governed object has a content-hashed identity | `dekimuhq/regulation-as-code`'s `manifestHash` (RFC 8785 canonical JSON → SHA-256) and decide.fyi's `rulebook.hash` are the two clean matches, in the sense that both hash a governed semantic artifact, not merely a software version — most others use a version field or Git history, which is a narrower, PARTIAL match |
| PR/CI merge-result gate | The check ran against the *actual* merge result, not just the isolated branch head | Conftest + required checks (commodity infrastructure); no comparator inspected was observed re-resolving live base-ref ancestry the way AuthContract's `git-gate` does |
| Runtime fact/action admissibility | A caller's claim is checked against independently-established context, not trusted at face value | Microsoft Agent Governance Toolkit (Public Preview), Permit0, Veridex, OpenEAGO, Permguard, Safe Hands, SmartPolicy, AP2 — all narrower than the literal axis on closer inspection; see [§3](#3-comparison-matrix) |
| Reconstructable evidence | A third party can recompute the verdict from raw inputs and compare | `dekimuhq/regulation-as-code`'s receipt-verification contract (`manifestMatches` / `reproducible` / `signatureValid`, computed independently from the manifest, facts, and corpus) is the clearest match found; in-toto's link/layout verification is the other clean match. Most agent-governance systems' "audit trail"/"signed decision" mechanisms are evidence *of a decision having been logged*, not independently *recomputable* verdicts, and are scored PARTIAL, not YES |

The rest of this document backs the claims above with primary-source
citation where obtained — see the per-cell evidence in
[§3](#3-comparison-matrix) and [§9](#9-source-evidence-appendix) for
exactly which claims carry that rigor — and is explicit about which of
these are AuthContract's own **target** claims rather than what the
current reference implementation does.

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
- **[OpenFisca](https://github.com/openfisca/openfisca-core)** — an open tax/benefit rules-as-code engine with dozens of country packages (e.g. [openfisca-france](https://github.com/openfisca/openfisca-france)) turning legislation into a computable, testable model. The inspected README establishes an active, multi-country-package project; it does not itself establish a comparative claim like "most widely adopted" — no primary source in this scan's corpus was found substantiating that comparison, so this document does not make it.
- **[Accord Project](https://github.com/accordproject)** (Cicero, Ergo) — Linux Foundation smart-legal-contract stack binding natural-language templates to executable clause logic.
- **[Obligation-First](https://obligationfirst.org/)** ([examples on GitHub](https://github.com/snapsynapse/obligation-first)) — an open upper schema (`Authority → Instrument → Term → Obligation`) for representing normative content across jurisdictions, explicitly *not* a rules engine — it references Catala/Blawx/OpenFisca as where the executable encoding would live.
- **[Mantra](https://github.com/mhatzl/mantra)** — a Rust-focused requirements-traceability tool: maps requirements to implementation/test code, tracks six sync states (Failed/Verified/Skipped/Unverified/Deprecated/Excluded). Does not reference external regulation or a formal standards body, and its README documents no Git-merge-result-bound PR gate — it is a project-requirements tool in the same family as Loom, not a source-of-normative-authority tool.
- **[FINOS Open RegTech SIG](https://github.com/finos/open-regtech-sig)** — a FINOS special interest group. **Correction from AC-024B:** the phrase "issue regulation as code alongside the prose" was this document's own paraphrase, not a quotation — it does not appear in the repository. The repository's own literal words describe the group as "a community of people interested in creating open source solutions for regulatory and compliance issues." Directly on-topic for AuthContract's upstream half regardless.
- LegalRuleML / Akoma Ntoso — OASIS LegalDocML standards for legal-rule and legal-document markup. These are **standards, not implementations**; do not infer runtime behavior from the spec text alone.

**If you need to represent a rule's relationship to its source text, look at
this list before building something bespoke.**

### Compliance / control → policy bridge, and the closest single comparator found for canonical-digest/receipt mechanics specifically

- **[`dekimuhq/regulation-as-code`](https://github.com/dekimuhq/regulation-as-code)** — of the systems inspected in this scan, the one whose canonical-digest-and-receipt mechanics compare most closely to AuthContract's own `digest.py`/receipt design. This is an analyst comparison scoped specifically to that one mechanic, in this inspected corpus — not a general claim that dekimuhq is the closest comparator to AuthContract overall, and not a market-ranking claim. Deep-dived in [§4](#4-high-materiality-deep-dives).
- **[OSCAL Compass Compliance-to-Policy (C2P)](https://github.com/oscal-compass/compliance-to-policy)** (Python and [Go](https://github.com/oscal-compass/compliance-to-policy-go) implementations) — converts OSCAL Component Definitions into native policy-engine configuration (Kyverno, Open Cluster Management, Auditree) and converts results back into OSCAL Assessment Results, GitOps-native.
- **[Compliance Trestle](https://github.com/oscal-compass/compliance-trestle)** — CI-friendly tooling for authoring/validating OSCAL compliance artifacts in Git.
- **[ComplianceAsCode/content](https://github.com/ComplianceAsCode/content)** (formerly SCAP Security Guide) — machine-enforceable security-control content across many OS/product targets.
- **[FINOS Common Cloud Controls](https://github.com/finos/common-cloud-controls)** — machine-readable, technology-neutral controls for financial-services cloud deployments, with a named Steering Committee of Citi, LSEG, Morgan Stanley, ScottLogic, Red Hat, RBC, and BlackRock. **Correction from AC-024B:** the prior wording ("extending in 2025–2026 to CC4AI ('Common Controls for AI')," and "backing from 20+ named financial institutions and cloud providers") is not supported by this repository's README — a direct re-fetch found no mention of "CC4AI" or "Common Controls for AI" anywhere in it, and no "20+" figure; only the seven Steering Committee organizations named above are stated. Both claims are removed as unsupported by the inspected primary source (E8: not found in the inspected README; this does not establish they are false of the project generally, only that this document's prior citation of them to this source was incorrect).

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
- GitHub/GitLab required-status-checks, branch protection, and merge-result gating are **commodity delivery infrastructure**. AuthContract's differentiation cannot be "having a merge gate" — every serious CI system has one. What AuthContract's `git-gate` specifically does — re-resolving the *current* base ref live and requiring `git merge-base --is-ancestor` proof that the evaluated SHA actually contains both the current base and the PR head — was not found to be a built-in behavior of Conftest, GitHub required checks, GitLab merge trains, or Loom's/Mantra's own CI health gates by themselves; see [§5](#5-composite-substitution-attacks).

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

- **[Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit)** — the README's own status label is **"Public Preview"** ("production-quality public preview releases. May have breaking changes before GA") — this document preserves that label. Deterministic interception of agent tool calls, YAML/OPA/Cedar policy, zero-trust identity (SPIFFE/DID/mTLS), Merkle-chained tamper-evident audit log, multi-language SDKs, explicit `GovernanceDenied` records. **Correction from AC-024C (AC-024D consistency amendment):** the prior wording here ("it explicitly does not claim to enforce policies *derived from* those frameworks") overstated an inspection absence as an explicit source statement, inconsistent with §4's own E8-bounded framing. The README maps its controls to OWASP Agentic AI Top 10, NIST AI RMF, EU AI Act, and SOC 2 as *compliance mappings*; users author their own YAML policies. In the inspected README, no claim was found that those frameworks are the derivation source of the enforced policy. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[Permit0](https://github.com/permit0-ai/permit0)** — pre-execution, deterministic action-authorization layer for agents, publishing what it calls a "canonical, append-only vocabulary" (its "canonical action taxonomy") of what agents do, with a separately-described "signed audit trail" for decisions; Apache-2.0, Rust. **Correction from AC-024B:** the compound phrase "replayable and signed" describing decisions does not appear verbatim in the README — that was this document's own paraphrase, not a quotation. No explicit maturity/status label was found in the inspected README.
- **[Veridex / agentic-payments](https://github.com/veridex-protocol/agentic-payments)** (plus [`agents-treasury`](https://github.com/veridex-protocol)) — session-key-scoped autonomous agent payments with an 8-rule `PolicyEngine`, signed `EvidenceBundle`, multi-chain support. High materiality — see [§4](#4-high-materiality-deep-dives) for the quote-level analysis of what its README actually says.
- **[OpenEAGO](https://github.com/finos-labs/open-eago)** (FINOS Labs) — enterprise agent governance/orchestration overlay with jurisdiction enforcement, HITL, and real-time compliance checks against GDPR/DORA/EU AI Act/SR 11-7/BCBS 239/PCI-DSS/MiFID-II/EMIR. No explicit maturity/status label was found in the inspected `overview.md`. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[Permguard](https://github.com/permguard/permguard)** — Git-versioned, distributed authorization engine spanning traditional systems and AI agents.
- **[Safe Hands](https://github.com/arcadeai-labs/safe-hands)** — implements Asimov's Three Laws of Robotics as Cedar authorization policy, governing a real physical robotic arm over MCP before commands reach actuators. Its own benchmark description reports blocking 46 specific forbidden commands across 11,728 red-team test cases with zero false-permits — a tested-prohibition-coverage result, not by itself evidence of a generally closed/normalized action-space model (see the corrected J axis in [§3](#3-comparison-matrix)). Its "law" concept is a fictional/design framing, not institutional or regulatory authority, and no source-citation mechanism was found.
- **[SmartPolicy](https://github.com/smartpolicy-protocol/smartpolicy)** — an on-chain (Ethereum Sepolia) policy registry decoupling authorization rules from enforcement, with off-chain EIP-712 signed grants via an MCP server. The project's own materials state the contracts are tested (54 Foundry tests passing) and, in its own literal words, "**NOT audited; internal until mature** — no public repo or registry listings yet." **Correction from AC-024B:** the prior wording "not independently audited" and "internal pending maturity" paraphrased this sentence rather than quoting it; the exact literal text is restored above — status preserved here rather than upgraded.
- **[kyndryl-open-source/aiagent-portable-authorization](https://github.com/kyndryl-open-source/aiagent-portable-authorization)** ("PortAuth") — reference implementation of policy-embedded credential authorization for AI agents (arXiv:2605.11487): signed credentials with machine-evaluable constraints, verified at runtime, producing signed audit decisions.
- **[Google Agent Payments Protocol (AP2)](https://github.com/google-agentic-commerce/AP2)** — an open standard representing every agent purchase as three signed **Mandates** (Intent, Cart, Payment), each a W3C Verifiable Credential; the project's own materials name 60+ launch partners including Mastercard, PayPal, Coinbase, and American Express.
- **[alibaba/open-agent-auth](https://github.com/alibaba/open-agent-auth)** — enterprise framework implementing the IETF draft "Agent Operation Authorization," binding user identity to agent operations via OAuth2/OIDC/WIMSE/W3C VC with semantic audit trails; the project's own materials describe it as **public beta**.
- Other agent-governance projects screened but not deep-dived: `Runestone-Labs/gatekeeper`, `aporthq/aport-spec` (Open Agent Passport), `opena2a-standards/agent-authorization-protocol`, `better-auth/agent-auth`, `auth-agent/auth-agent` — full detail in the AC-024B Drive return's screening ledger.

**Boundary observed across this whole tier:** every one of these systems
governs an action against a *supplied* policy/mandate. What none of them
was directly confirmed to do is bind that policy back to an authoritative
external source with a citation, an unresolved-state marker, or genuine
institutional standing (as distinct from an identity/authentication
credential); nor was a genuinely closed, normalized action-universe model
with unknown/overlap handling — as opposed to a bounded set of known tool
types or a tested list of prohibited commands — confirmed in any of them.
See [§3](#3-comparison-matrix) for the corrected per-system J-axis scoring
and [§4](#4-high-materiality-deep-dives) for the quote-level evidence on
Veridex and OpenEAGO specifically.

### Evidence, replay, attestation

- **[in-toto](https://github.com/in-toto/in-toto)** — signed layouts, authorized functionaries, signed link metadata, and continuous verification of a software supply chain. ("Authorized functionaries" is an identity/authorization mechanism, not institutional standing in the sense AuthContract's target E axis means.) **Correction from AC-024B:** the layout itself is directly documented as authenticated by functionary **signature**, not by a separate content-hash/digest of the layout as a governed semantic object; the *link metadata* hashes are records of each step's materials and products (evidence of what a step consumed/produced), not an identity mechanism for the governing layout. F is therefore re-scored NO-EVIDENCE-FOUND (not YES) in [§3](#3-comparison-matrix); the independently-recomputable-replay finding on the L axis is unrelated to this correction and is unchanged.
- **[decide.fyi](https://github.com/decidefyi/decide)** — versioned, hashed rulebooks (`rulebook.hash`); deterministic verdicts; `input_hash`; Ed25519-signed attestation bundles; replay that compares verdict/evidence/record hashes against the original run; explicit non-binding vs. production-binding modes. High materiality — see [§4](#4-high-materiality-deep-dives).
- **[Sigstore](https://github.com/sigstore)** and the **[DSSE](https://github.com/secure-systems-lab/dsse)** envelope spec — signing-envelope/attestation-format infrastructure that in-toto and Sigstore's `cosign` both build on. DSSE's own specification establishes a generic signing envelope for arbitrary data; it authenticates that a named signer signed a given payload. That is a distinct claim from independently recomputing a *decision verdict* from raw inputs (AuthContract's target L axis) — see the corrected, split scoring for Sigstore and DSSE in [§3](#3-comparison-matrix).

---

## 3. Comparison matrix

Cell values follow the AuthContract Evidence and Claim Register: **YES**
(directly evidenced in the inspected ref, matching the *literal* axis
definition — not a neighboring capability), **PARTIAL** (the observed
mechanism directly touches the axis but is narrower or different — never
used for a merely adjacent capability), **NO-EVIDENCE-FOUND**
(searched/inspected the exact ref/corpus and did not find it — never read
as "does not exist" or "categorically does not close" a transition; read
as "not found/established to close, in the inspected corpus"),
**NOT-EVALUATED** (insufficient inspection to score either way), **N/A**
(axis does not apply to this system's scope/domain), **STANDARD** (this is
a specification, not an implementation — do not infer runtime behavior).

Axes: **A** source citation/anchor · **B** structured rule representation ·
**C** unresolved/ambiguity preservation (source-interpretation uncertainty,
not runtime evidence-missing/UNKNOWN) · **D** expert/professional review ·
**E** issuer/authority/standing/lifecycle (not identity/authentication
alone) · **F** canonical *governed semantic artifact* identity/digest (not
a version field, Git commit, or generic software-release identity alone)
· **G** projection/transpilation *with an established conformance/
equivalence result* (compiler or transpiler existence alone is not a
conformance result) · **H** PR/CI gate bound to the actual merge result
(not a generic CI/health gate) · **I** runtime *fact* provenance/
admissibility/type/freshness (a signed mandate or credential authorizing
an *action* is not evidence for this axis unless it also establishes fact
provenance) · **J** closed/normalized mediated *action* universe with
unknown/overlap handling (a set of known tool integrations, or a
benchmarked list of prohibited commands, is not the same as a formally
closed action-space model — and facts/obligations are not actions) · **K**
pre-execution enforcement · **L** independently recomputable evidence/
replay *from raw decision inputs* (a signature, Merkle log, audit record,
or signing envelope alone is not sufficient — it must be shown that a
third party can recompute the verdict itself, not merely verify that a
payload was signed) · **M** correction/supersession/*history continuity*
(a version number or snapshot alone does not establish a
correction/supersession workflow unless the mechanism for handling
change/replacement is evidenced) · **N** the project's own
current-implemented-vs-target/roadmap honesty (spec versioning or a
"frozen at v1" label is not evidence of this — the project must itself
distinguish what is implemented from what is planned).

**Cells changed from the AC-024A candidate in this amendment are marked
with a double-dagger (‡) and the axis rule that changed them; cells
changed in the AC-024A amendment (from AC-024) retain their single-dagger
(†) marking.**

| System | Class | A | B | C | D | E | F | G | H | I | J | K | L | M | N |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TNO Calculemus/FLINT | Upstream | YES | YES | PARTIAL | PARTIAL | NOT-EVAL | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Catala | Upstream | YES | YES | PARTIAL† | PARTIAL | NO-EV | NOT-EVAL | YES (partial compiler certification is a genuine, if partial, conformance result) | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Blawx | Upstream | YES | YES | PARTIAL | NOT-EVAL | NO-EV | NOT-EVAL | PARTIAL‡ (compiles to s(CASP)/Prolog; no conformance/equivalence result found) | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | YES |
| L4 / Natural L4 | Upstream | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | PARTIAL‡ (multiple transpilation targets exist; no independent conformance result found) | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Logical English | Upstream | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | PARTIAL‡ (compiles to Prolog/s(CASP); no conformance result found) | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| OpenFisca | Upstream | PARTIAL | YES | NOT-EVAL | PARTIAL | NO-EV | NOT-EVAL | PARTIAL‡ (testable models; no independent conformance/equivalence proof found) | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | PARTIAL‡ (versioned country packages; correction/supersession workflow not independently confirmed) | NOT-EVAL |
| Accord Project (Cicero/Ergo) | Upstream/Adjacent | YES | YES | NOT-EVAL | NOT-EVAL | NO-EV | NOT-EVAL | PARTIAL‡ (Ergo compiles to JS; no conformance result found) | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Obligation-First | Upstream | YES | YES | PARTIAL | PARTIAL | PARTIAL | NOT-EVAL | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES |
| **`dekimuhq/regulation-as-code`** (deep-dived) | Upstream/Bridge | PARTIAL (`citationUrl` present but optional) | YES | NO-EV (five-state model is explicitly deterministic with no unresolved/ambiguous concept — an observed absence, not just unsearched) | NO-EV | NO-EV | **YES** (`manifestHash`, RFC 8785 canonical JSON → SHA-256, over the governed `SourceManifest` content itself, not a software release) | N/A | NO-EV | N/A | **N/A‡** (J is a mediated agent-*action* universe; dekimuhq's typed facts/obligations/evidence requirements are not actions — this axis does not apply to its scope, and the prior YES conflated facts/obligations with actions) | N/A | **YES** (receipt independently verifies `manifestMatches`/`reproducible`/`signatureValid` from raw manifest+facts+corpus) | NOT-EVAL | **NO-EV‡** (the spec being versioned/"frozen at v1" is not itself evidence the project distinguishes implemented-now from target/roadmap capability; no such distinction was found in the six spec files and profile inspected) |
| Mantra | Adjacent/Upstream | NO-EV | YES | NOT-EVAL | N/A | NO-EV | NOT-EVAL | N/A | NO-EV | N/A | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| LegalRuleML / Akoma Ntoso | STANDARD | STANDARD | STANDARD | STANDARD | N/A | STANDARD | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| OSCAL Compass C2P | Upstream/Bridge | N/A | YES | NOT-EVAL | NOT-EVAL | NOT-EVAL | PARTIAL (UUID/version, not confirmed content digest of a governed artifact) | PARTIAL‡ (maps controls to policy IDs and round-trips results to OSCAL Assessment Results; the mapping's own semantic conformance is not independently confirmed) | PARTIAL | NO-EV | N/A | N/A | NOT-EVAL | PARTIAL‡ (OSCAL objects carry version/last-modified metadata; a full correction/supersession workflow is not independently confirmed) | NOT-EVAL |
| Compliance Trestle | Upstream/Infra | N/A | YES | N/A | NOT-EVAL | NOT-EVAL | PARTIAL | N/A | PARTIAL | N/A | N/A | N/A | NOT-EVAL | PARTIAL‡ | NOT-EVAL |
| ComplianceAsCode/content | Upstream/Bridge | PARTIAL | YES | N/A | NOT-EVAL | NOT-EVAL | PARTIAL | PARTIAL‡ (generates enforcement content from control content; conformance of the generated content to the control text not independently confirmed) | PARTIAL | N/A | N/A | N/A | NOT-EVAL | PARTIAL‡ | NOT-EVAL |
| FINOS Common Cloud Controls (**"/ CC4AI" label removed — unsupported by inspected source, see §2**) | Upstream standard | YES | YES | NOT-EVAL | YES | NOT-EVAL | NOT-EVAL | PARTIAL | NO-EV | NO-EV | N/A | N/A | NOT-EVAL | NOT-EVAL | NOT-EVAL |
| Loom | Adjacent/Upstream | N/A | YES | PARTIAL | N/A | NO-EV | PARTIAL (content-hashed requirement, not an institutionally-governed artifact) | N/A | NO-EV (health-score CI gate is generic, not source-relative merge-result binding) | N/A | N/A | N/A | NOT-EVAL | PARTIAL‡ (content-hash-linked requirements track drift; a full correction/supersession workflow beyond drift-detection is not independently confirmed) | NOT-EVAL |
| Conftest | Infrastructure | N/A | YES | N/A | N/A | N/A | N/A | N/A | PARTIAL | N/A | N/A | N/A | N/A | N/A | N/A |
| OPA | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| Cedar | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | NO-EV (formal analysis is of Cedar's own policies, not a translator into Cedar) | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| OpenFGA | Downstream infra | N/A | YES | N/A | N/A | N/A | N/A | N/A | N/A | N/A | PARTIAL | YES | N/A | N/A | N/A |
| Microsoft Agent Governance Toolkit | Downstream (**Public Preview**) | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL (identity/RBAC, not institutional standing) | NOT-EVAL | N/A | NO-EV | PARTIAL | **PARTIAL‡** (deterministic tool-call interception against supplied policy; a genuinely closed/normalized action-universe model with unknown/overlap handling, distinct from evaluating named tool calls against policy, was not independently confirmed) | YES | PARTIAL (Merkle-chained audit log is tamper-evident, not confirmed independently recomputable from raw inputs) | NOT-EVAL | YES |
| Permit0 | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | NOT-EVAL | N/A | NO-EV | PARTIAL | **PARTIAL‡** (project describes a "canonical action taxonomy"; independent confirmation of closed/normalized coverage with unknown-action handling, beyond the project's own description, was not obtained in this scan) | YES | PARTIAL (project describes a "signed audit trail" for decisions — **corrected from AC-024B's "replayable and signed" quote, which was not verbatim**; independent recomputation mechanism not confirmed) | NOT-EVAL | NOT-EVAL |
| Veridex agentic-payments | Downstream/Runtime | NO-EV (searched; the literal phrase "regulatory mandates" does not appear — see [§4](#4-high-materiality-deep-dives)) | YES | NOT-EVAL | NO-EV | PARTIAL | PARTIAL (mandate version field, not confirmed content digest of a governed artifact) | N/A | NO-EV | PARTIAL | **PARTIAL‡** (an 8-rule `PolicyEngine` over payment actions specifically, a bounded domain; a generally closed/normalized action-universe model with unknown/overlap handling beyond that payment-specific scope was not confirmed) | YES | PARTIAL (`EvidenceBundle` hash/signature verification, not confirmed independent recomputation from raw inputs) | **PARTIAL‡** (mandate versioning observed; a correction/supersession *workflow*, distinct from a version field, was not independently confirmed) | NOT-EVAL |
| OpenEAGO | Downstream/Control-plane | NO-EV | YES | NO-EV | NOT-EVAL | PARTIAL | NOT-EVAL | N/A | NO-EV | NOT-EVAL | **PARTIAL‡** (governs agent traffic broadly per its own description; a formally closed/normalized action-universe model with unknown/overlap handling was not independently confirmed) | YES | PARTIAL (blockchain audit trail records activity; not confirmed as independently recomputable verdicts) | NOT-EVAL | NOT-EVAL |
| Permguard | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | PARTIAL (Git-versioned policy, not a confirmed content digest distinct from Git's own object hash) | N/A | NO-EV | NOT-EVAL | **PARTIAL‡** (fine-grained resource-permission model; not confirmed as a closed *action*-universe model specifically, as distinct from relationship/permission authorization) | YES | NOT-EVAL | PARTIAL‡ (Git versioning; correction/supersession workflow not independently confirmed) | NOT-EVAL |
| Safe Hands | Downstream/Runtime (physical) | NO-EV | YES (Cedar policy) | N/A | N/A | NO-EV | NOT-EVAL | N/A | NO-EV | NOT-EVAL | **PARTIAL‡** (a benchmarked list of 46 blocked commands across 11,728 test cases is tested-prohibition-coverage, not by itself a formally closed/normalized action-universe model with unknown-action handling — the two are related but not identical, and this was scored YES in error in AC-024A) | YES | PARTIAL (audit log of law/decision per action) | NOT-EVAL | NOT-EVAL |
| SmartPolicy | Downstream (**not independently audited**) | NO-EV | YES | N/A | N/A | PARTIAL (on-chain registry owner, not institutional standing) | PARTIAL (immutable on-chain record, not a canonical-artifact digest scheme like dekimuhq's) | N/A | NO-EV | NOT-EVAL | NOT-EVAL | YES | PARTIAL (EIP-712 signed grants) | NOT-EVAL | NOT-EVAL |
| kyndryl aiagent-portable-authorization | Downstream | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | NOT-EVAL | N/A | NO-EV | PARTIAL | **PARTIAL‡** (credential-scoped constraints over specific claim-data access; a generally closed/normalized action-universe model was not independently confirmed) | YES | PARTIAL (signed decisions; recomputability from raw inputs not confirmed) | NOT-EVAL | NOT-EVAL |
| Google AP2 | Downstream/Runtime | NO-EV | YES | NOT-EVAL | NO-EV | PARTIAL | PARTIAL (VC = signed credential; content-digest scheme not confirmed) | N/A | NO-EV | **NO-EV‡** (I is runtime *fact* provenance/admissibility/type/freshness; a wallet-signed Mandate authorizes an *action* and is not itself evidence about the provenance/freshness of a runtime fact — the prior YES conflated action-authorization signing with fact provenance) | PARTIAL (three defined Mandate *types* — Intent/Cart/Payment — are a bounded, typed structure, narrower than a closed action universe over arbitrary agent actions) | YES | PARTIAL (signed Mandates; independent recomputation contract not confirmed) | PARTIAL | NOT-EVAL |
| alibaba/open-agent-auth | Downstream (**public beta**) | NO-EV | YES | NOT-EVAL | NO-EV | NO-EV (OIDC identity is not institutional standing) | NOT-EVAL | N/A | NO-EV | PARTIAL | **PARTIAL‡** (identity-bound operation authorization; a closed/normalized action-universe model with unknown/overlap handling was not independently confirmed) | YES | PARTIAL (audit trails; recomputability not confirmed) | NOT-EVAL | PARTIAL (labels itself public beta) |
| in-toto | Infrastructure | N/A | N/A | N/A | N/A | NO-EV (authorized functionaries are an identity mechanism, not institutional standing) | **NO-EV‡** (link metadata records hashes of a step's *materials and products* — an evidence-of-execution record — not a separate content-hash/digest of the *governing layout itself*; in-toto's own documentation describes the layout as authenticated by functionary **signature**, not by a distinct digest/identity scheme for the layout as the governed semantic object; corrected from the AC-024B YES, which conflated link-metadata hashing with layout identity) | N/A | N/A | N/A | N/A | N/A | YES (layout/materials/products verification is genuinely independently recomputable — this L score is unaffected by the F correction above, since L concerns replay/recomputation of recorded steps, not identity of the governing layout) | PARTIAL‡ (layouts can be updated/re-issued; a documented correction/supersession *workflow*, distinct from the update mechanism itself, was not independently confirmed) | N/A |
| decide.fyi | Downstream/Decision-evidence | NO-EV | YES | NO-EV (`UNKNOWN`/review states are runtime input-completeness, not confirmed source-interpretation ambiguity) | NO-EV | NOT-EVAL | YES (`rulebook.hash`, over the governed rulebook content itself) | N/A | NO-EV | PARTIAL | YES (closed refund/cancel/trial/return decision domain with explicit `UNKNOWN`/review handling) | YES | PARTIAL (hash-compare replay confirmed; not confirmed to recompute from raw un-hashed inputs each time versus re-hashing stored inputs) | YES ("immutable historical snapshots" is direct evidence of preserved history across changes, closer to the literal M definition than a bare version field) | NOT-EVAL |
| Sigstore | Infrastructure | N/A | N/A | N/A | N/A | PARTIAL (signer identity) | N/A | N/A | N/A | N/A | N/A | N/A | **PARTIAL‡** (transparency-log-backed signature verification confirms a payload was signed and logged; it is not itself independent recomputation of a decision verdict from raw inputs) | N/A | N/A |
| DSSE | Infrastructure | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | **NO-EV‡** (DSSE is a generic signing-envelope specification for arbitrary payloads; it establishes that a signer signed a payload, not that a decision verdict is independently recomputable from raw inputs — split out from Sigstore and corrected from the AC-024A YES) | N/A | N/A |

Standards (LegalRuleML/Akoma Ntoso) and pure infrastructure rows
(GitHub/GitLab required checks, Conftest, OPA/Cedar/OpenFGA, Sigstore,
DSSE) are included because AuthContract's target architecture is
explicitly meant to sit *on top of* several of them, not replace them.

---

## 4. High-materiality deep dives

### `dekimuhq/regulation-as-code`

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
  authoritative legal source. Nothing in this grammar mediates or gates a
  live *agent action* — the obligations describe compliance conditions
  over stored evidence, not a runtime action-decision boundary.
- **`spec/compilation.md`** — compilation is a deterministic, fail-closed,
  eight-error-code static-check pipeline (`schema-invalid`,
  `duplicate-id`, `unknown-fact`, `fact-type-mismatch`, `unknown-family`,
  `unknown-dependency`, `dependency-cycle`, `nested-dependson-invalid`).
  On success it emits a `CompiledManifest` carrying a `manifestHash`:
  the SHA-256, over RFC-8785-derived canonical JSON, of a five-field
  intermediate representation — materially the same digest discipline
  AuthContract's own `digest.py` uses for `.ac` artifacts (RFC 8785 JCS +
  SHA-256), independently arrived at, and computed over the governed
  regulation-encoding content itself rather than over a generic software
  release.
- **`spec/evidence.md`** — the evidence corpus is an open, extensible
  family registry of `CorpusReceipt` records (five fields: `family`,
  `claimId`, `issuedAt`, `active`, optional `eventType`), matched by exact
  string equality, with `active` supporting revocation-style semantics —
  scoped to individual evidence receipts, not to the manifest's own
  authorial standing.
- **`spec/receipt.md`** — an `EvaluationReceipt` binds four content hashes
  (`manifestHash`, `factsHash`, `corpusDigest`, `reportHash`) under an
  Ed25519 signature over exactly `{kind, alg, input, reportHash}`.
  Independent verifiers need only the public spec, the three raw inputs
  (manifest, facts, corpus), and a trust-anchor key resolver, and produce
  three independent booleans: `manifestMatches`, `reproducible`,
  `signatureValid`. This is the clearest, most literal match to
  AuthContract's own target "recompute the receipt from raw inputs and
  compare" behavior found in this scan.
- **`spec/evaluation.md`** — obligations resolve to exactly one of five
  states (`satisfied`, `at-risk`, `expired`, `missing`, `not-applicable`).
  The specification explicitly states there is no "unresolved,"
  "undetermined," or "ambiguous" evaluation state — a directly observed
  *absence*, not merely an unsearched one. dekimuhq's `missing` state
  means "no satisfying evidence was found," not "the regulation itself is
  unclear here." No passage in any of the six files inspected was found
  distinguishing which of the specification's own features are currently
  implemented versus planned/future — the document reads as a frozen v1
  specification throughout, which is a versioning fact, not itself
  evidence of the project practicing an explicit implemented-vs-target
  distinction the way AuthContract's own documentation does.
- **`profiles/gdpr/v1.md`** — a reference profile (v1.2.0) encoding eight
  GDPR obligations (Arts. 5, 6, 13, 15–22, 17, 35, 36) against named
  evidence families, explicitly framed as "reference material, not legal
  advice."

**What this means for AuthContract's claim, scoped precisely:**
`dekimuhq/regulation-as-code`'s canonical-digest-and-receipt mechanics —
specifically `manifestHash` and the `EvaluationReceipt` verification
contract — are, in this inspected corpus, the closest match found to
AuthContract's own digest/receipt design for that one mechanic. This is
not a claim that dekimuhq is the closest comparator to AuthContract as a
whole system, and not a market-ranking claim — dekimuhq itself does not
mediate agent actions, establish institutional authority/standing for its
manifest authors, or bind to a Git PR/merge result, all of which remain
open per [S5](#5-composite-substitution-attacks) below.

### Veridex / agentic-payments — corrected quote-level analysis

AC-024 attributed to Veridex's README a sentence about policy rules being
"author-defined based on autonomous-agent safety practices rather than
regulatory mandates," presented as if quoting the repository. **Re-fetching
the actual README directly** (at the exact repository,
[`github.com/veridex-protocol/agentic-payments`](https://github.com/veridex-protocol/agentic-payments),
commit `329a200afa6748c7965a6fc896b24eb6c8c25c5a`, branch `main`) **finds
no such sentence, and specifically no occurrence of the phrases
"regulatory mandates" or "external governance sources" anywhere in it.**

What the README *does* literally say, quoted directly: **"Human sets
limits → Agent gets session key → Makes autonomous payments"**, and **"Give
your agent a wallet with human-set spending limits."** Session
configuration is `dailyLimitUSD`, `perTransactionLimitUSD`, `expiryHours`,
`allowedChains`. No maturity/status label (beta, production, experimental)
was found in the inspected README.

Corrected classification: **it is a direct, primary-source (E4) fact that
Veridex's spending limits are configured by the human wallet creator.** It
is a **separate, search/inspection-scope (E8) finding** that no mention of
external regulatory or governance sourcing was found in the inspected
README — this absence finding does not itself appear as an assertion
anywhere in Veridex's own text, and is not presented as though it does.
Both facts point the same direction (Veridex's policy provenance is
author/operator-configured, not source-derived), but they are different
evidence classes, kept separate here, and are treated in
[S6](#5-composite-substitution-attacks) as counterevidence to a
hypothesis, not as its refutation.

### OpenEAGO — corrected quote-level analysis

Direct fetch of `docs/overview/overview.md` (repository
[`finos-labs/open-eago`](https://github.com/finos-labs/open-eago), commit
`f03627fce810a8e0ba423147fe29a854b5fcd3b2`, branch `main`) finds the
literal sentence: **"Immutable audit trails spanning multiple regulatory
frameworks for examination by FCA, MAS, and FinCEN"** and **"Audit
Continuity: Blockchain trails provide immutable records across all
interactions."** Both are E4 direct facts about audit *recording* across
named regulators. **The document was inspected for, and did not contain,
any passage tracing a specific policy back to a specific regulatory
clause** — an E8 inspection-scope finding about what the document does not
contain, kept explicitly separate from the E4 facts about what it does
say. No explicit project maturity/status label (alpha, beta, RFC, stable)
was found in the inspected document.

### Microsoft Agent Governance Toolkit

**Status, preserved as stated by the project:** the README's own words are
"production-quality public preview releases. May have breaking changes
before GA" — this document calls it **Public Preview**, not
production-grade.

**Strongest overlap:** deterministic pre-execution interception of agent
tool calls against YAML/OPA/Cedar policy, with a Merkle-chained
tamper-evident audit log and an explicit `GovernanceDenied` record shape.
**Policy provenance — E4 direct facts plus a bounded analyst inference,
kept separate.** The exact recorded primary source (README.md at commit
`b5705588883fac48b88cbe6fd0bd7d48c798453e`) directly, literally states:
"Govern any tool function in two lines" with a user-supplied
`policy="policy.yaml"` argument, and "On every call, `safe_tool`
evaluates the YAML policy, logs the decision to an audit trail, and
raises `GovernanceDenied` when the policy blocks the action." These are
E4 direct facts: policy is user/application-supplied, and the toolkit
intercepts, evaluates, and logs against that supplied policy. Separately,
the README maps its controls to OWASP Agentic AI Top 10, NIST AI RMF, EU
AI Act, and SOC 2 as *compliance mappings*, not as claimed sources the
policies are derived from.

**Correction from AC-024B:** the prior version of this document presented
the sentence "does not cite institutional authority for the actual
policies it enforces" as a direct, quoted E4 fact. A targeted re-fetch of
the exact recorded commit found neither "institutional authority" nor
"does not cite" anywhere in the text — that sentence was this document's
own analyst inference from the E4 facts above, not a repository
quotation, and is restated here as such: **inference, not quotation** —
given that policy is user-supplied and mapped only to frameworks as
compliance targets rather than cited as its derivation source, this
document infers the toolkit does not establish institutional authority
for the policies it enforces. This inference is bounded by what the
inspected README does and does not say (an E8 inspection-scope
observation: no institutional-authority mechanism was found in the
material inspected); it is not a claim that no such mechanism exists
anywhere in the project.
**L-axis:** the Merkle-chained audit log is tamper-*evident* (you can
detect if it was altered); this scan did not confirm it is independently
*recomputable* from raw inputs the way dekimuhq's receipt contract is —
scored PARTIAL. **J-axis:** deterministic interception of named tool calls
against supplied policy is real and directly evidenced; a formally
closed/normalized action-space model with unknown/overlap handling,
beyond evaluating known tool calls against a policy engine, was not
independently confirmed in the inspected README — scored PARTIAL, not
YES, corrected in this amendment.

### decide.fyi

**Strongest overlap:** the closest system in this scan (alongside
dekimuhq) to AuthContract's rule→runtime→evidence half — a versioned,
hashed rulebook (`rulebook.hash`), deterministic verdicts, `input_hash`,
Ed25519-signed attestation bundles, and replay that compares hashes
against the original run.
**C-axis:** decide.fyi's `UNKNOWN`/review-required verdict states read, in
the inspected material, as "the input data needed to decide is missing or
unclear" for a specific refund/cancel/trial/return case, not "the
underlying policy text is ambiguous." No passage was found distinguishing
those two things — scored NO-EVIDENCE-FOUND for source-interpretation
ambiguity specifically, not YES.
**L-axis:** decide.fyi's own materials describe replay as comparing
hashes against the original run; whether replay recomputes from the raw,
un-hashed rulebook/input each time or re-derives from already-stored
hashes was not confirmed at the code level in this scan — scored PARTIAL.
**M-axis:** decide.fyi's own materials state that "successful evaluations
are registered as **immutable tenant-scoped snapshots**" and that
"historical replay restores the original canonical input and stored
rulebook snapshot rather than trusting a caller override or the current
application deployment." (**Correction from AC-024B:** the prior wording
"immutable tenant-scoped snapshot metadata" inserted the word "metadata,"
which does not appear in the source; the exact phrase is "immutable
tenant-scoped snapshots.") This is direct evidence of preserved history
across policy changes, closer to the literal correction/supersession-continuity
definition than a bare version field, so this axis is scored YES, unlike
most other systems in this matrix where only a version field was found.
**Capability that remains strong here:** a live decision API with a
GitHub Action that hashes vendor policy pages daily and opens an issue on
change — a working instance of exactly the kind of source-drift detection
AuthContract's target architecture describes only conceptually.

---

## 5. Composite-substitution attacks (re-run after evidence corrections)

Each disposition below attaches to the literal stated hypothesis, not to
whichever supporting evidence paragraph reads strongest — this
directionality check was re-applied to every attack in this amendment,
not only S6.

**S1 — TNO Calculemus/FLINT + Git/CI + OPA/Cedar + in-toto reproduces the
full AuthContract architecture.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED.** Positive evidence:
FLINT gives source→structured interpretation (A/B); OPA/Cedar give runtime
policy evaluation (J/K, both PARTIAL on the closed-action-universe
question); in-toto gives signed, independently verifiable supply-chain
evidence (L — a genuine match, unlike most agent-governance audit logs).
Missing transition: no evidence these four have been integrated for this
purpose, and specifically no evidence of a PR/CI gate re-resolving live
merge-base ancestry, or of runtime facts checked against
verifier-established context rather than caller-supplied policy input.
What to reuse: FLINT's source-decomposition methodology.

**S2 — Catala/L4 + Conftest/GitHub required checks + a runtime policy
engine + in-toto reproduces it.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED.** Same shape as S1.

**S3 — OSCAL + C2P + OPA/Cedar + GitHub + evidence/attestation reproduces
it for enterprise controls.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED**, the composition
whose upstream half is closest to operational for enterprise-control
domains specifically (C2P's GitOps pipeline is real). C2P's F and G axes
are both PARTIAL on re-audit (a UUID/version field, not a confirmed
content digest of a governed artifact; a control→policy mapping mechanism,
not a confirmed conformance result) — this narrows, rather than
strengthens, this composition's claim relative to the AC-024A version.

**S4 — Obligation-First + an executable encoding (Catala/Blawx/OpenFisca) +
a runtime governor + in-toto reproduces it.**
Disposition: **OPEN.** Architecturally plausible — Obligation-First
explicitly defers to this composition — but no evidence was found of
anyone having actually built it end to end.

**S5 — Regulation-as-Code (`dekimuhq`) + Microsoft AGT / Permit0 / OpenEAGO
+ in-toto / receipt systems can reproduce the AuthContract composite.**
**Disposition: STRONGLY SUPPORTED — NOT ESTABLISHED.** Fully executed, not
`NOT EVALUATED`.

Positive evidence, by transition:
- **(a) author/profile supplies the machine meaning** — YES, directly
  evidenced. dekimuhq's `SourceManifest` grammar is exactly this: an
  author writes typed facts, conditions, and requirements.
- **(b) semantic fidelity to authoritative source** — **NOT ESTABLISHED.**
  `citationUrl` is optional, points to a URL for human reference, and
  nothing in `grammar.md`, `compilation.md`, or `evaluation.md` checks
  that the encoded obligation actually matches what the cited regulation
  says.
- **(c) institutional authority/standing** — **NO-EVIDENCE-FOUND.** No
  spec file inspected defines who is authorized to publish a
  `SourceManifest`, or any lifecycle/revocation concept for the
  manifest's own authorial standing (as opposed to the evidence corpus's
  `active` field, which is about individual receipts).
- **(d) final Git source-relative merge-result admissibility** —
  **NO-EVIDENCE-FOUND.** No PR/CI integration was found in the inspected
  spec files; combining dekimuhq with Microsoft AGT/Permit0/OpenEAGO does
  not close this gap either — none of those three were found to
  re-resolve live Git merge-base ancestry; they gate agent *tool calls*,
  not GitHub PR merges.
- **(e) runtime fact/action enforcement** — **PARTIAL, via composition
  only.** dekimuhq itself does not enforce anything at agent-action time.
  Microsoft AGT/Permit0/OpenEAGO do enforce at agent tool-call time, but
  each was independently rescored PARTIAL, not YES, on the J axis (closed
  action universe) in this amendment — none was confirmed to have a
  formally closed/normalized action-space model, only deterministic
  evaluation of named/known tool calls against supplied policy. No
  evidence was found of anyone actually wiring dekimuhq's obligation
  output into one of these three systems' policy input.
- **(f) independently recomputable evidence** — **YES**, and this remains
  the strongest single transition in the whole S1–S5 set. dekimuhq's
  receipt contract (`manifestMatches`/`reproducible`/`signatureValid`,
  computed from raw manifest+facts+corpus) is a genuine, literal match to
  AuthContract's target evidence behavior, on its own — no composition
  needed for this specific transition.

**Net verdict:** this composition comes closest to AuthContract's full
target chain among everything tested, specifically because dekimuhq
closes transition (f) outright and partially closes (a). Transitions (b),
(c), and (d) remain open, and (e) is weaker than the AC-024A version
described, once J is corrected across the three runtime systems. **S5
does not establish collapse or full equivalence with AuthContract's target
architecture in the inspected corpus; full equivalence remains NOT
ESTABLISHED.** This is the single strongest evidence in this scan that
the evidence/receipt half of AuthContract's target claim already has
close, independently-arrived-at open precedent, and any future
AuthContract architecture work on the receipt/evidence side should study
dekimuhq's receipt contract directly.

**S6 — Veridex or OpenEAGO already carries enough mandate/contract
provenance that AuthContract is redundant upstream.**

**Hypothesis disposition: OPEN.** No positive evidence was found
establishing that either system's mandate/policy content is
institutionally source-derived (which would support the hypothesis), and
no positive evidence was found affirmatively contradicting AuthContract's
claim either (which would refute it) — the corrected evidence is
counterevidence, not proof either way, and a search-absence finding
cannot establish REFUTED on its own.

**Separately, a bounded counter-finding: STRONGLY SUPPORTED — NOT
ESTABLISHED** that, in the inspected refs, these systems begin from
supplied/operator-configured policy and no upstream source-derivation
mechanism was found:
- **E4 direct primary-source facts:** Veridex's README literally states
  spending limits are human-configured at session creation. OpenEAGO's
  `overview.md` literally describes audit trails as spanning multiple
  regulatory frameworks for regulator examination.
- **E8 search/inspection-scope findings:** neither document was found, in
  the files inspected, to contain the phrase "regulatory mandate,"
  "external governance source," or any mechanism tracing a specific policy
  clause back to a specific regulatory provision.
- **What would need to be true for the S6 hypothesis itself to be
  REFUTED:** a literal statement, in either project's primary source,
  affirmatively describing its policy/mandate content as
  user/operator-configured *and explicitly disclaiming* any
  source-derivation mechanism. Neither project's inspected material does
  this, so REFUTED is not the correct disposition for the hypothesis
  either — the hypothesis stays OPEN, and the counter-finding above is
  reported alongside it as a separate, bounded, evidence-limited
  statement.

**S7 — decide.fyi's rulebook/trusted-adapter/replay model already collapses
the rule→runtime→evidence portion sufficiently that AuthContract only adds
source interpretation.**
Disposition: **STRONGLY SUPPORTED — NOT ESTABLISHED.** decide.fyi's
`UNKNOWN` state is not counted as source-ambiguity preservation (see
[§4](#4-high-materiality-deep-dives)), and its replay mechanism is scored
PARTIAL pending code-level confirmation of what exactly is recomputed.
What remains true and strong: hashed rulebooks, deterministic verdicts,
signed attestation, preserved historical snapshots, and automated daily
source-drift monitoring of decide.fyi's own policy inputs are all directly
evidenced. Missing: no PR/CI gate bound to a Git merge result; no per-fact
verifier-established-context binding distinguishing a claim's value from
who asserted it.

**Net read across S1–S7 after correction:** S5 is the strongest attack in
the set — dekimuhq closes the independently-recomputable-evidence
transition outright — but it was not found to establish collapse or full
equivalence of AuthContract's target chain in the inspected corpus. S6's
hypothesis remains OPEN, with a separate, narrower counter-finding at
STRONGLY SUPPORTED — NOT ESTABLISHED. No tested composition, including S5,
was found to close the institutional-authority-standing or
Git-merge-result-binding transitions, or to establish a genuinely closed
action-universe model anywhere this scan looked. The honest claim remains
a **composite/seam** claim, not an ingredient claim.

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
  metadata format (as an envelope/integrity layer; not as a substitute for
  AuthContract's own recompute-and-compare receipt contract, which needs
  the dekimuhq-style contract above it).
- **Rulebook/replay UX patterns and history-continuity modeling** —
  decide.fyi's hash-then-replay model and its immutable snapshot approach
  to preserving history across policy changes.

## 7. What AuthContract is trying to connect

None of the systems above, including the corrected S5 composition, were
found integrating *all* of: source citation, unresolved-state preservation,
professional/authority standing, canonical artifact digest, a PR/CI gate
bound to the actual merge result, a genuinely closed/normalized action
universe with unknown/overlap handling, runtime fact/action admissibility
checked against verifier-established context, and a reconstructable
evidence receipt — in one continuous, non-relocatable chain. AuthContract's
target architecture is that seam, not any one ingredient in it, and — per
this amendment's own findings — not even the two closest ingredients found
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

**Final claim ceiling, as evidence-limited as the corrected corpus
supports:**

> Open systems in the inspected corpus cover substantial individual
> portions of the source→rule→delivery→runtime→evidence chain. Dekimu
> Regulation-as-Code provides particularly close precedent for canonical
> content identity and independently recomputable evaluation receipts. The
> inspected corpus did not establish a single system or tested composition
> that carries the complete chain through source-semantic fidelity,
> institutional standing, final merge-result admissibility, runtime
> fact/action enforcement, and reconstructable evidence. This is a
> corpus-bounded result, not evidence of uniqueness or nonexistence.
> Current AuthContract MVP-alpha does not implement broad automated
> natural-language source→rule semantic verification end to end.

---

## 9. Source-evidence appendix

**One row per system that appears in the [§3](#3-comparison-matrix) matrix
or a [§4](#4-high-materiality-deep-dives) deep dive — no system is grouped
into a prose catch-all.** "SHA (via commit-history page)" means obtained
from GitHub's commit-list web page or JSON API in this session; these were
not independently re-verified with a local `git clone` and should be
treated as reported-and-cited evidence, not cryptographically re-derived
by this scan itself. "— / not captured" is used honestly where no
SHA/date/status was obtained, rather than omitting the row.

| Project | Canonical URL | Inspected | Branch/ref | Commit SHA | Files inspected | Status (if directly evidenced) | Evidence class |
|---|---|---|---|---|---|---|---|
| `dekimuhq/regulation-as-code` | https://github.com/dekimuhq/regulation-as-code | 2026-08-23 | main | `11ba12bfd6851800ab11a2c925b99ad09ba90d98` | README.md, spec/grammar.md, spec/compilation.md, spec/evidence.md, spec/receipt.md, spec/evaluation.md, profiles/gdpr/v1.md | not established from inspected source | E4 |
| Microsoft Agent Governance Toolkit | https://github.com/microsoft/agent-governance-toolkit | 2026-08-23 | main | `b5705588883fac48b88cbe6fd0bd7d48c798453e` (via commit-history page) | README.md | **Public Preview** (project's own words) | E4 |
| Veridex agentic-payments | https://github.com/veridex-protocol/agentic-payments | 2026-08-23 | main | `329a200afa6748c7965a6fc896b24eb6c8c25c5a` (via commit-history page) | README.md | not established from inspected source | E4 |
| Veridex agents-treasury | https://github.com/veridex-protocol (org listing; exact repo URL not separately captured) | 2026-08-23 | main | — / not captured | README.md (via org listing) | not established from inspected source | E4 |
| OpenEAGO | https://github.com/finos-labs/open-eago | 2026-08-23 | main | `f03627fce810a8e0ba423147fe29a854b5fcd3b2` | README.md, docs/overview/overview.md, ROADMAP.md | not established from inspected source | E4 |
| decide.fyi | https://github.com/decidefyi/decide | 2026-08-23 | main | `21ff7def1899ea75a5f02408c221fec538dc4517` | README.md, decide.fyi/resources/docs | production-binding vs. non-binding modes distinguished in-product | E4 |
| Loom | https://github.com/jsuppe/loom | 2026-08-23 | main | `104ac0b4e2ea8cca72db9f829a61d8b6fd66ddfc` | README.md (direct fetch after initial search miss) | not established from inspected source | E4 |
| Mantra | https://github.com/mhatzl/mantra | 2026-08-23 | main | `f295cb88b9cc5126759b65f19e446af633783271` | README.md (direct fetch after initial search miss) | Rust-focused; other-language support described as planned | E4 |
| Safe Hands | https://github.com/arcadeai-labs/safe-hands | 2026-08-23 | main | `52088c179d78e414db1a49e98e4853eaec9a7648` | README.md (direct fetch after initial search miss) | not established from inspected source | E4 |
| SmartPolicy | https://github.com/smartpolicy-protocol/smartpolicy | 2026-08-23 | main | `534f4e382756a9e54733766a24cf447741ffd5eb` | README.md (direct fetch after initial search miss) | contracts tested (54 Foundry tests); literal quote "NOT audited; internal until mature" (project's own words — corrected from AC-024B's non-verbatim "internal pending maturity") | E4 |
| kyndryl aiagent-portable-authorization | https://github.com/kyndryl-open-source/aiagent-portable-authorization | 2026-08-23 | main | `53328ce3a28e958316da378c9d97dbccdb974234` | README.md | not established from inspected source | E4 |
| Catala | https://github.com/CatalaLang/catala | 2026-08-23 | master | `08832f46b26f5d3936c7b6ac156540cd90e7d500` | README.md, doc/formalization/README.md | active (recent commit history) | E4 |
| OSCAL Compass Compliance-to-Policy | https://github.com/oscal-compass/compliance-to-policy | 2026-08-23 | main | `6ec821d4c253baf85e5b4d171ee9f9fb7affc1e0` | README.md, architecture docs | not established from inspected source | E4 |
| OSCAL Compass Compliance-to-Policy (Go) | https://github.com/oscal-compass/compliance-to-policy-go | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| Compliance Trestle | https://github.com/oscal-compass/compliance-trestle | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| ComplianceAsCode/content | https://github.com/ComplianceAsCode/content | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| FINOS Common Cloud Controls | https://github.com/finos/common-cloud-controls | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source; "CC4AI" not found in this README (see §2 correction) | E4 |
| FINOS Open RegTech SIG | https://github.com/finos/open-regtech-sig | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| Google AP2 | https://github.com/google-agentic-commerce/AP2 | 2026-08-23 | main | `e1ea56db72a6385bce3e5c1112b3a56ce60acb43` | README.md, src/ap2/types/mandate.py | v0.2.0 (stated in repo) | E4 |
| Permit0 | https://github.com/permit0-ai/permit0 | 2026-08-23 | main | `c5e8f7db3d119591d70a3a7d64d195f6d4432127` | README.md | not established from inspected source | E4 |
| alibaba/open-agent-auth | https://github.com/alibaba/open-agent-auth | 2026-08-23 | — / not captured | — / not captured | README-level | **public beta** (project's own words) | E4 |
| Permguard | https://github.com/permguard/permguard | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| in-toto | https://github.com/in-toto/in-toto | 2026-08-23 | — / not captured | — / not captured | README.md | active, CNCF-graduated project | E4 |
| Sigstore | https://github.com/sigstore | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| DSSE | https://github.com/secure-systems-lab/dsse | 2026-08-23 | — / not captured | — / not captured | spec-level | not established from inspected source | E3 (specification) |
| TNO Calculemus/FLINT | https://gitlab.com/normativesystems | 2026-08-23 | — / not captured (GitLab; no commit SHA captured) | — | Choppr / Flint Ontology / Calculemus Calculator repo pages | not established from inspected source | E4 |
| Blawx | https://github.com/Lexpedite/blawx | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| L4 / Natural L4 | https://github.com/smucclaw/l4-ide (+ https://github.com/smucclaw/dsl) | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| Logical English | https://github.com/LogicalContracts/LogicalEnglish | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| OpenFisca | https://github.com/openfisca/openfisca-core | 2026-08-23 | — / not captured | — / not captured | README-level, one country package glanced | not established from inspected source | E4 |
| Accord Project (Cicero/Ergo) | https://github.com/accordproject | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| Obligation-First | https://obligationfirst.org/ (+ https://github.com/snapsynapse/obligation-first) | 2026-08-23 | — / not captured (schema site, not a single repo ref) | — | schema page, GitHub examples | v0.4.1 (stated on schema site) | E4 |
| LegalRuleML / Akoma Ntoso | https://www.oasis-open.org/committees/tc_home.php?wg_abbrev=legaldocml | 2026-08-23 | — (standard, not a repo) | — | spec/standard pages | OASIS Standard (Akoma Ntoso v1.0, 2018); v2.0 Part 2 in public review as of this scan | E3 (specification) |
| Conftest | https://github.com/open-policy-agent/conftest | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| fiberplane/drift | https://github.com/fiberplane/drift | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| OPA | https://github.com/open-policy-agent/opa | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| Cedar | https://github.com/cedar-policy/cedar | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| OpenFGA | https://github.com/openfga/openfga | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |
| Permify | https://github.com/Permify/permify | 2026-08-23 | — / not captured | — / not captured | README-level | not established from inspected source | E4 |

---

## 10. Search method and limitations

**Method:** two-direction search plus adjacency terms (rules as code,
legislation as code, policy as code, compliance as code, requirements
traceability, semantic drift, agent governance, GitOps controls,
continuous compliance, warrant, mandate, obligation) across GitHub,
GitLab, and primary project/spec pages, run independently against the
Engineering Lead's seed ledger, amended twice after independent review
found direct-fetch verification and matrix-semantics gaps.

**Exact corpus accounting:** 56 distinct candidate projects/specifications
screened (the complete list, with URL, discovery origin,
included/excluded/near-miss disposition, reason, inspection depth, and
ref/commit where available, is deposited in full in the AC-024B Drive
return record — see [§11](#11-how-to-update-this-sota)); 33 inspected
beyond search snippets using primary README/spec/code/docs; 33 systems
represented in the [§3](#3-comparison-matrix) comparison matrix (Sigstore
and DSSE are counted as two rows in the matrix, split in this amendment
from one combined row in AC-024A).

**The complete screening/exclusion ledger — every one of the 56 screened
candidates, with exact canonical URL, discovery query/class, included/
excluded/near-miss disposition, reason, and inspection depth — is
deposited in full in the AC-024B Drive return record**, per that work
order's explicit instruction not to substitute a summary or a "see
docs/SOTA.md" pointer for it.

**Material correction carried from AC-024A (unchanged):** four
repositories AC-024 reported as unlocatable — `dekimuhq/regulation-as-code`,
`mhatzl/mantra`, `arcadeai-labs/safe-hands`, `smartpolicy-protocol/
smartpolicy` — are real and were found immediately by directly fetching
their exact URLs. This document's method: **an exact, named repository
may be reported unlocatable only after a direct URL fetch attempt fails**,
and the exact fetch attempt and its result must be recorded (see
[§9](#9-source-evidence-appendix)).

**Newly discovered comparators not in the Engineering Lead's original seed
ledger** (carried forward, unchanged): Google's Agent Payments Protocol
(AP2), `alibaba/open-agent-auth`, FINOS Open RegTech SIG,
`fiberplane/drift`, Permify.

**Limitations:** this is a three-session (AC-024, AC-024A, AC-024B),
point-in-time (2026-08-23) web and repository scan. It did not clone or
execute any comparator's code; findings come from README/doc/spec text
and file listings as fetched via web search, direct URL fetch, or the
GitHub commit-history page/API. Several commit SHAs in
[§9](#9-source-evidence-appendix) were obtained via a webpage/API fetch
rather than independently re-derived by cloning and hashing locally, and
are reported as such. GitHub/GitLab search-engine coverage gaps (confirmed
at four repositories in AC-024A) mean this document's remaining
`NO-EVIDENCE-FOUND` rows are bounded by what direct fetch could reach
across three sessions, not by systematic repository enumeration.

## 11. How to update this SOTA

1. Re-run the two-direction search in [§10](#10-search-method-and-limitations)
   with the current date, including the adjacency terms listed there.
2. **Before concluding any exact, named repository is unavailable, fetch
   its URL directly.** Do not rely on a zero-result search alone.
3. Re-verify every `NO-EVIDENCE-FOUND` row in [§3](#3-comparison-matrix) —
   a negative finding here is a search-corpus statement, not a permanent
   fact.
4. Before scoring any cell YES, re-read the literal axis definition in
   [§3](#3-comparison-matrix) and confirm the evidence satisfies it
   specifically — not a neighboring capability (a version field for a
   content digest, a signature for independent recomputation, an identity
   credential for institutional standing, a benchmarked command list for a
   closed action universe, a compiler for a conformance result). This
   amendment exists because that check was not applied rigorously enough
   twice before.
5. Re-run the S1–S7 composite-substitution attacks in
   [§5](#5-composite-substitution-attacks) — this is the fastest-moving
   part of the landscape, and check that each disposition attaches to the
   literal stated hypothesis rather than to the strongest available
   evidence.
6. When citing what a primary source "says," quote it directly and check
   the quote against the actual fetched text before publishing.
7. Give every matrix/deep-dive system its own row in
   [§9](#9-source-evidence-appendix) — do not group any system into a
   prose summary sentence, even when its inspection was shallow; use
   "— / not captured" honestly instead of omitting the row.
8. Update the scan date at the top of this document and add a dated note
   in [§0](#0-amendment-notices) summarizing what changed, rather than
   silently overwriting prior findings.
