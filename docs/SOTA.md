# State of the art: what already exists around AuthContract

**In 90 seconds:** AuthContract is not trying to invent policy engines,
signing, CI merge gates, agent authorization, or evidence receipts —
substantial open precedent already exists for each of those, individually.
What AuthContract is testing is whether a rule can stay traceable to an
authoritative source *and* be enforced deterministically at runtime *and*
gated at the actual Git merge result *and* produce evidence a third party
can independently recompute — all in one continuous chain. No system
inspected in this scan was found doing all of that together. This document
is the landscape map and the engineering consequences of that map, not a
competitor ranking: it does not claim AuthContract is unique, first, or
without equivalent anywhere.

For the full audit trail — corpus accounting, per-system evidence quotes,
the 33-system comparison matrix, the S1–S7 composite-substitution attacks,
and the update procedure — see
[`docs/SOTA-EVIDENCE.md`](SOTA-EVIDENCE.md). Nothing here overrides that
document; this page is a compressed, developer-facing front end to it, per
AC-027.

---

## The landscape, in two axes

This is an orientation device, not a claim that any system reduces
cleanly to two numbers, not a market ranking, and not a uniqueness claim.
Placement is coarse and corpus-bounded — approximate bands, not precise
coordinates — and every plotted system is traceable to the evidence in
[`docs/SOTA-EVIDENCE.md`](SOTA-EVIDENCE.md) §3/§4/§9. Systems whose
strongest contribution doesn't project cleanly onto either axis (notably
`dekimuhq/regulation-as-code` — see the note below the chart) are
annotated rather than force-fit.

**The numeric coordinates in the Mermaid source below are layout
coordinates required by the chart renderer to place each label on the
grid — they are not measured scores, rankings, percentages, or otherwise
quantitatively comparable values.** Two systems at, say, x=0.70 and
x=0.75 are not being claimed as 5% apart on any measured scale; the
coordinates only encode which coarse band (see the quadrant labels) each
system falls into.

```mermaid
quadrantChart
    title Execution control vs. rule source traceability (approximate, corpus-bounded)
    x-axis "Descriptive / advisory" --> "Deterministic runtime enforcement"
    y-axis "Developer/operator-defined" --> "Traceable to authoritative source"
    quadrant-1 "Target territory (empty in this corpus)"
    quadrant-2 "Strong grounding, limited runtime action enforcement"
    quadrant-3 "Supporting infra / partial components"
    quadrant-4 "Strong enforcement, operator-defined rules"
    TNO FLINT / Catala: [0.15, 0.78]
    OpenFisca: [0.20, 0.55]
    Obligation-First: [0.15, 0.68]
    dekimuhq (receipt mechanic, off-axis): [0.30, 0.42]
    in-toto / DSSE / Sigstore: [0.28, 0.20]
    Conftest / GitHub checks: [0.35, 0.15]
    OPA / Cedar / OpenFGA: [0.85, 0.10]
    decide.fyi: [0.80, 0.22]
    Microsoft AGT (Public Preview): [0.75, 0.30]
    Veridex / Permit0 / OpenEAGO: [0.70, 0.25]
    AuthContract (current MVP-alpha): [0.55, 0.15]
    AuthContract (target architecture): [0.92, 0.90]
```

**Reading it:**

- **Upper-right (target territory) is empty in the inspected corpus.**
  That's the finding, not an oversight — see
  [`docs/SOTA-EVIDENCE.md`](SOTA-EVIDENCE.md) §5–§7 for the composite
  attacks that tried to compose existing systems into this territory and
  came up short on institutional-standing and Git-merge-result-binding
  transitions specifically.
- **Upper-left** — TNO/FLINT, Catala, OpenFisca, Obligation-First: strong
  source-to-structured-rule traceability, but none of them mediates or
  gates a live runtime action.
- **Lower-right** — decide.fyi, Microsoft Agent Governance Toolkit,
  Veridex, Permit0, OpenEAGO, OPA/Cedar/OpenFGA: real deterministic
  runtime enforcement. Their enforcement layers consume supplied
  policy/rule content; authoritative-source traceability for that content
  was not established in the inspected corpus.
- **Lower-left** — in-toto, DSSE, Sigstore, Conftest, GitHub required
  checks: commodity/supporting infrastructure that several of the above
  (and AuthContract's own target) sit on top of, rather than replace.
- **`dekimuhq/regulation-as-code`** is plotted near the lower-middle
  because neither frozen axis is where its actual strength lives: its
  `manifestHash` canonical-digest and independently-recomputable
  `EvaluationReceipt` are the single closest precedent found anywhere in
  this scan for AuthContract's own evidence/receipt design — but it has no
  runtime action-enforcement path (execution control) and only an
  *optional* source citation with no institutional-standing mechanism
  (source traceability). Its real contribution is off both axes; see
  **Build / reuse** below.
- **AuthContract (current MVP-alpha)** sits at moderate-to-strong
  execution control (Git merge-result gate, runtime fact/action
  admissibility, and a recomputable receipt — all real, all bounded to one
  synthetic banking specimen) and low source traceability (source→rule
  derivation is target behavior, not implemented yet). **AuthContract
  (target architecture)** is the aspirational upper-right marker this
  project is testing against, not a description of what runs today.

---

## Capability map: AuthContract's own chain, current status

This is AuthContract's eight-link target chain, scored for what the
*current* MVP-alpha reference implementation actually does — not a
per-comparator grid (see
[`docs/SOTA-EVIDENCE.md`](SOTA-EVIDENCE.md) §3 for that). States:
**Strong** / **Partial** / **Not established** / **Not evaluated**.

| # | Dimension | Current status | Why |
|---|---|---|---|
| 1 | Source grounding | **Not established** | No mechanism reads a statute/regulation/contract and derives or checks a rule against it. Target behavior, not implemented. |
| 2 | Authority / standing | **Not established** | No institutional-authority or professional-review binding is implemented for the current specimen. |
| 3 | Canonical artifact identity | **Strong** | RFC 8785 JCS + SHA-256 digest over the governed `contract` object; self-referential/digest-scope violations rejected. |
| 4 | CI / merge gate | **Strong** | `git-gate` re-resolves the live base ref and requires `git merge-base --is-ancestor` proof the evaluated SHA actually contains both current base and PR head — not just the isolated PR head. |
| 5 | Runtime fact admissibility | **Strong** | Verifier-established `VerifiedEvidence` context, not the caller's own claimed fields, decides issuer/trust-basis/path/corroborator identity; future/incomparable timestamps fail closed. |
| 6 | Action enforcement | **Partial** | Actions are checked against a declared, closed domain for the one synthetic specimen implemented; not yet a general cross-specimen action-universe model. |
| 7 | Evidence / replay | **Strong** | PASS issues a receipt independently recomputable from the raw artifact/action/fact inputs, not merely a signed record that logging occurred. |
| 8 | Lifecycle / correction | **Not evaluated** | No correction/supersession workflow for AuthContract's own artifacts has been implemented or scored yet. |

---

## Build / reuse / do not rebuild

- **Policy evaluation/enforcement infrastructure** — reuse OPA, Cedar, or
  OpenFGA. They evaluate policy that something else supplies and warrant;
  that "something else" is the seam AuthContract is testing, not a reason
  to build a fifth policy engine.
- **GitHub/GitLab CI merge enforcement** — reuse required-status-checks
  and branch protection as the delivery substrate (AuthContract already
  does — see `AuthContract Gate`). What isn't commodity is re-resolving
  the *live* base ref and proving ancestry before trusting a merge result;
  that part stays custom.
- **Canonicalization and digest primitives** — reuse RFC 8785 JCS +
  SHA-256 (already AuthContract's own choice, and independently the same
  discipline `dekimuhq/regulation-as-code`'s `manifestHash` uses).
- **Signing/transparency infrastructure** — reuse DSSE as the signing
  envelope and in-toto's link-metadata format as an integrity layer.
  Neither is a substitute for AuthContract's own recompute-and-compare
  receipt contract — a signature proves who signed, not that a third
  party can rederive the same verdict from raw inputs.
- **Receipt/replay patterns** — study `dekimuhq/regulation-as-code`'s
  `spec/receipt.md` directly (`manifestMatches` / `reproducible` /
  `signatureValid`, computed independently from manifest + facts +
  corpus) and decide.fyi's hash-then-replay model with immutable
  historical snapshots. Both are closer to AuthContract's own target
  receipt behavior than anything else found in this scan and are
  specified in enough detail to study line by line.
- **Source-to-structured-rule tooling** — study TNO Calculemus/FLINT's
  source-decomposition methodology and Catala's line-by-line
  legislative-text annotation before designing AuthContract's
  still-unimplemented source→rule step. Do not rebuild a rules-as-code DSL
  from scratch first.

---

## Nearest systems by seam

Only the systems that materially affect implementation decisions — see
[`docs/SOTA-EVIDENCE.md`](SOTA-EVIDENCE.md) §2/§4 for the full 33-system
corpus.

**`dekimuhq/regulation-as-code`**
Why care: the closest precedent anywhere in this scan for AuthContract's
own canonical-digest-and-receipt mechanics specifically.
Reuse: its `spec/receipt.md` verification contract as a direct design
reference.
Open seam: `citationUrl` is optional and unchecked against the cited
source; no institutional-authority/standing mechanism for who may publish
a manifest; no runtime action-enforcement path at all.

**decide.fyi**
Why care: a live, working instance of hashed rulebooks, deterministic
verdicts, signed attestation, and immutable historical snapshots —
closest working replay/history-continuity system found.
Reuse: its hash-then-replay pattern and its GitHub Action that hashes
vendor policy pages daily and opens an issue on drift.
Open seam: no source-interpretation-ambiguity concept (its `UNKNOWN`
state is input-completeness, not source ambiguity); no PR/CI gate bound
to a Git merge result; no per-fact verifier-established-context binding.

**Microsoft Agent Governance Toolkit** (Public Preview)
Why care: deterministic pre-execution interception of agent tool calls
against YAML/OPA/Cedar policy with a Merkle-chained audit log — a
high-materiality agent-governance runtime overlap in this scan.
Reuse: its `GovernanceDenied` record shape as a reference for explicit
refusal reporting.
Open seam: policy is user-supplied and only *mapped* to compliance
frameworks (OWASP/NIST/EU AI Act/SOC 2), not derived from them; no
formally closed action-universe model beyond evaluating named tool calls;
audit log is tamper-evident, not confirmed independently recomputable.

**Loom / Mantra / fiberplane/drift**
Why care: content-hash-linked requirement/spec-to-code drift detection
with a CI gate — the nearest precedent for "detect when implementation
drifts from its governing source," even though the governing source here
is a requirement or a spec doc, not a regulation.
Reuse: the drift-detection UX pattern for surfacing when code and its
linked source diverge.
Open seam: none of the three binds to an authoritative external source
with citation/standing, and none was found gating a Git merge result the
way AuthContract's `git-gate` re-resolves live base-ref ancestry.

**OPA / Cedar / OpenFGA**
Why care: downstream policy-evaluation infrastructure; no reason to
build a competing evaluator.
Reuse: directly, as the evaluation layer underneath a projection.
Open seam: all three are explicitly downstream — they evaluate whatever
policy is handed to them and establish nothing about where that policy
came from.

**in-toto / DSSE / Sigstore**
Why care: the clean, independently-recomputable-replay precedent for
supply-chain steps (in-toto's layout/materials/products verification),
plus commodity signing-envelope infrastructure (DSSE, Sigstore/cosign).
Reuse: as an integrity/attestation layer alongside AuthContract's own
receipt contract, not instead of it.
Open seam: in-toto's layout identity is authenticated by functionary
signature, not a separate content-digest of the layout as a governed
semantic object; DSSE/Sigstore establish that a signer signed a payload,
not that a decision verdict is independently recomputable from raw
inputs.

---

## Current AuthContract boundary: MVP-alpha vs. target

**What the current reference implementation does**, as of this scan:

- verifies canonical artifact identity and bindings (RFC 8785 JCS +
  SHA-256 digest);
- projects a rule into its declared runtime action domain and checks
  actions against it;
- checks a PR's actual Git test-merge composition (re-resolving the live
  base ref and requiring ancestry proof), not merely the isolated PR head;
- runs a bounded runtime fact/action decision path with
  verifier-established assertion-context binding, and issues a receipt on
  PASS, independently recomputable from the raw artifact/action/fact
  inputs;
- all of the above for **one synthetic banking specimen**.

**What it does not do:** broad automated natural-language source→rule
semantic verification is target behavior, not implemented end to end.
There is no current mechanism that reads a statute, regulation, or
contract and automatically derives or checks a rule against it — every
system in [`docs/SOTA-EVIDENCE.md`](SOTA-EVIDENCE.md) §2/§4 that attempts
anything in that space (TNO/FLINT, Catala, L4, OpenFisca, dekimuhq, etc.)
is currently more mature at that specific task than AuthContract, because
AuthContract has not attempted it yet.

This matches [`docs/DEVELOPER-LANGUAGE.md`](DEVELOPER-LANGUAGE.md)'s
implementation-status discipline and the root [`README.md`](../README.md)'s
own "Current status" section — this document does not relax or contradict
either.

**Claim ceiling, unchanged from the full evidence record:**

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

## Full research record

Corpus accounting, the 33-system comparison matrix (14-axis scoring),
per-system deep dives with direct quotes and commit SHAs, the S1–S7
composite-substitution attacks, the amendment history (AC-024 through
AC-024D), search method, and the update procedure all live in
[`docs/SOTA-EVIDENCE.md`](SOTA-EVIDENCE.md). Nothing from the prior
document was shortened or dropped — it was relocated.
