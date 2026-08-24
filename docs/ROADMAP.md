# AuthContract roadmap

Derived from the AC-035 benchmark run measuring implementation
`e4e1a97509df1a66c44b090c0a0ca0a03907f4dc` (DUT), with harness
`a7f6ba374b1362e624a3f8b912b265dd03da4cdd`. Every item below cites the
observed evidence that motivates it. Items with no supporting measurement are
placed under **Research / not yet established** and are explicitly not
commitments.

Raw evidence: [`benchmarks/results/`](../benchmarks/results/) ·
Analysis: [`docs/BENCHMARKS-AC-039.md`](BENCHMARKS-AC-039.md)

---

## NOW
*Required to move from current MVP-alpha to a stronger developer-testable alpha.*

### N1 — Cache canonicalization within a transaction

| | |
|---|---|
| **Evidence** | Canonicalization costs ~91 µs mean (p50 83.9, p95 143.6) and is performed by validation, digest, and projection independently; `verify_receipt` then re-runs the entire decision path. Action check by contrast is 5.6 µs. Canonicalization dominates the ~633 µs end-to-end path. |
| **Limitation** | The same contract body is canonicalized several times per transaction with no intra-transaction reuse. |
| **Capability** | Canonicalize once per artifact per transaction and reuse the bytes across validation, digest, and projection. |
| **Acceptance** | End-to-end p50 improves measurably against the 574.0 µs recorded baseline with **zero** change to any correctness or adversarial specimen result, and digests remain byte-identical to the recorded baseline. |
| **Dependency** | None. |
| **Maturity impact** | Removes the dominant cost without touching security semantics. |

### N2 — Decide whether admission approvals gate authorization

| | |
|---|---|
| **Evidence** | Finding AC-035-F1: forged `admission.approvals` yields `ALLOW`. The binding holds — `admission_digest` and `receipt_digest` both change and cross-verification fails — but nothing gates on approval content at decision time. |
| **Limitation** | Approvals are carried and bound as evidence but are never evaluated. A reader may reasonably assume otherwise. |
| **Capability** | Either (a) implement approval evaluation as a declared gate, or (b) document explicitly that approvals are evidence-only at this maturity. |
| **Acceptance** | If (a): a specimen with insufficient approvals REFUSEs with a distinct reason code, with positive and negative fixtures. If (b): README and contract-shape docs state the boundary and a regression test pins it. |
| **Dependency** | None. |
| **Maturity impact** | Closes an ambiguity that currently invites over-reading of what the system enforces. |

### N3 — Rename the misleading `*_mutated.json` fixtures

| | |
|---|---|
| **Evidence** | Finding AC-035-F4: the fixtures are mutated *and re-sealed*, so they are validly-bound variants. The first draft of the benchmark suite mis-expected them to refuse. |
| **Limitation** | Fixture names actively suggest a security property they do not exercise. |
| **Capability** | Rename to reflect what they are (e.g. `..._variant_resealed.json`) and add genuinely stale-bound counterparts as committed fixtures. |
| **Acceptance** | Names describe content; the stale-binding attack exists as a fixture, not only as programmatic construction in the benchmark. |
| **Dependency** | None. |
| **Maturity impact** | Removes a documented tripwire for external evaluators. |

### N4 — Publish the benchmark as a regression gate

| | |
|---|---|
| **Evidence** | The suite runs in ~100 s and exits non-zero on any correctness failure; 342 existing tests pass alongside it. |
| **Limitation** | Benchmark results are a point-in-time artifact; nothing prevents silent regression of latency or of the 38-specimen adversarial matrix. |
| **Capability** | Run the correctness and adversarial matrices in CI; track latency with a tolerance band rather than a hard threshold. |
| **Acceptance** | CI fails on any adversarial regression; latency drift is reported without failing on noise. |
| **Dependency** | N1 (so the tracked baseline is the post-optimization one). |
| **Maturity impact** | Converts a one-off measurement into a standing guarantee. |

---

## NEXT
*Required for realistic external engineering evaluation.*

### X1 — Multi-contract evaluation and selection

| | |
|---|---|
| **Evidence** | Scale curves recorded `NOT EVALUATED` for multi-contract corpora: the runtime evaluates one artifact per invocation and has no registry or cross-contract selection path. |
| **Limitation** | Any realistic deployment holds many contracts; none of that behaviour exists or can be measured. |
| **Capability** | A contract registry with deterministic selection and explicit conflict/overlap semantics. |
| **Acceptance** | Scaling measured across 1/10/100/1000 contracts; overlapping-scope conflicts resolve deterministically or refuse explicitly; `select_matching_projection` semantics are covered by adversarial specimens. |
| **Dependency** | None. |
| **Maturity impact** | Removes the largest single `NOT EVALUATED` gap. |

### X2 — Replay protection semantics

| | |
|---|---|
| **Evidence** | Finding AC-035-F3: replayed identical requests produce identical receipts. Determinism is confirmed; replay *protection* does not exist. |
| **Limitation** | An intercepted receipt is indistinguishable from a legitimately re-derived one. |
| **Capability** | Nonce, sequence, or single-use decision semantics, with an explicit statement of the threat model addressed. |
| **Acceptance** | A replayed request is distinguishable from a fresh one; adversarial specimens cover replay within and across freshness windows. |
| **Dependency** | Requires deciding whether the runtime may hold state — it is currently stateless. |
| **Maturity impact** | Addresses a threat class the current design does not cover at all. |

### X3 — Reduce verification cost, or justify it explicitly

| | |
|---|---|
| **Evidence** | Verification (296 µs mean) costs ~as much as the original decision (283 µs mean) because it recomputes every binding. |
| **Limitation** | A verifier-heavy workload costs the same as a decider-heavy one; that is a deliberate trade but is undocumented as a capacity-planning input. |
| **Capability** | Either reduce redundant work inside `verify_receipt` (subject to N1) while preserving zero trust in receipt fields, or document the cost as an intentional property with guidance. |
| **Acceptance** | Verification remains fully independent — no receipt field trusted — and either measurably improves or is documented with a capacity-planning note. |
| **Dependency** | N1. |
| **Maturity impact** | Makes verification cost a designed, stated property rather than an emergent one. |

### X4 — Cross-platform and cross-version determinism

| | |
|---|---|
| **Evidence** | Determinism is confirmed for one process, one platform, one Python version. §7 explicitly does not claim more. |
| **Limitation** | Canonical identity is only useful across parties if it is stable across their environments — untested. |
| **Capability** | Reproduce digests across Python versions, OSes, architectures, and ideally an independent implementation. |
| **Acceptance** | Identical contract digests and receipts across at least two Python versions and two OSes, published as evidence. |
| **Dependency** | None. |
| **Maturity impact** | Upgrades determinism from a local observation to a portable property — a precondition for third-party verification. |

### X5 — Real external rule evaluation

| | |
|---|---|
| **Evidence** | Every measurement uses one synthetic banking specimen family. The runbook's own claim ceiling states no external rule has been integrated. |
| **Limitation** | Nothing demonstrates the contract shape can express a rule authored outside this project. |
| **Capability** | Encode at least one externally-authored rule end-to-end and publish the gaps found. |
| **Acceptance** | An external rule is evaluated, and every unsupported construct is reported as a finding rather than worked around by reshaping the rule. |
| **Dependency** | Possibly X1. |
| **Maturity impact** | First evidence of generality beyond the synthetic specimen. |

---

## LATER
*Required for production-class deployment.*

### L1 — Concurrency and sustained-load behaviour
**Evidence:** throughput is single-process only; concurrency recorded `NOT EVALUATED`.
**Acceptance:** throughput and tail latency under sustained concurrent load, with a stated saturation point.
**Dependency:** X1.

### L2 — Interpreter startup amortization
**Evidence:** startup ~68 ms vs ~0.28 ms per decision — a ~240× ratio. Any per-decision-process deployment is dominated by startup.
**Acceptance:** a long-lived service or batch shape whose measured per-decision cost approaches the in-process figure.
**Dependency:** L1.

### L3 — Large-corpus operating envelope
**Evidence:** 10,000 facts → ~0.65 s and ~13 MiB per decision, linear.
**Acceptance:** documented supported envelope with measured limits, plus explicit refusal or degradation beyond it.
**Dependency:** N1, X1.

### L4 — Independent security review
**Evidence:** 38 adversarial specimens pass, but all were authored by the same party that wrote the implementation.
**Acceptance:** external review with findings published unmodified.
**Dependency:** X4, X5.

---

## RESEARCH / NOT YET ESTABLISHED
*Requires architecture, formalization, or experiment that does not exist. Not commitments.*

- **Automated natural-language source-to-rule derivation.** Not implemented; no
  measurement exists. Would require a validation methodology establishing that a
  derived rule faithfully represents its source — itself an open problem.
- **Formal proof of the authorization semantics.** No formal model exists. The
  38-specimen battery is testing, not proof.
- **Cross-jurisdiction / cross-domain generality.** One synthetic banking family
  measured. Any claim of generality needs evidence from materially different
  domains.
- **Distributed consensus on decisions.** No distribution layer exists; there is
  no architecture to evaluate.
- **Regulatory or legal sufficiency of receipts as evidence.** Entirely outside
  what any measurement here can establish; requires legal analysis, not
  benchmarking.
