# AuthContract benchmark baseline

**Commit measured:** `e4e1a97509df1a66c44b090c0a0ca0a03907f4dc`
**Tree:** `9967077e7f9f9c661199c728c5a2e7fe496be07a`
**Work order:** AC-035
**Raw results:** [`benchmarks/results/`](../benchmarks/results/)

This is the first end-to-end operational and performance baseline for
AuthContract. It measures the bounded MVP-alpha path that exists today. It is
not a marketing document and contains no projected or extrapolated figures.

---

## 1. Environment

| | |
|---|---|
| Python | 3.11.15 (CPython) |
| Platform | Linux x86_64 |
| Dependencies | `rfc8785` 0.1.4, `pytest` 9.1.1 |
| Process | single, single-threaded |

Figures are environment-specific. Absolute latencies will differ on other
hardware; the *shape* of the curves and the relative cost of stages are the
transferable results.

---

## 2. What was measured

The complete implemented path:

```
contract artifact
  → parse
  → digest-scope validation + sibling binding agreement
  → RFC 8785 (JCS) canonicalization
  → SHA-256 contract digest
  → deterministic projection into the declared action domain
  → runtime fact admission (issuer / trust basis / freshness / evidence binding)
  → action check against the projection
  → ALLOW or REFUSE
  → decision receipt
  → independent receipt verification from raw inputs
  → mutation / truncation detection
```

---

## 3. End-to-end correctness

**7 / 7 end-to-end specimens pass. 38 / 38 adversarial specimens pass.**

| ID | Specimen | Expected | Observed |
|---|---|---|---|
| E2E-01 | Happy path | ALLOW + receipt verifies | PASS |
| E2E-02 | Stale runtime fact | REFUSE | PASS (`RUN_FACT_STALE`) |
| E2E-03 | Malformed contract | fail closed | PASS |
| E2E-04 | Action outside projection domain | fail closed | PASS |
| E2E-05 | Receipt mutation + truncation | detected | PASS (20/20 variants detected) |
| E2E-06 | Source/version change, stale binding | REFUSE | PASS (`AC_DIGEST`) |
| E2E-07 | Deterministic replay ×100 | identical | PASS |

E2E-05 mutates **every** protected receipt field in turn and additionally
removes each field in turn — 20 variants total — rather than testing one
representative field. All 20 are detected.

The adversarial battery covers 38 specimens across: missing required fields,
unknown fields where forbidden, malformed types, out-of-domain values, stale
facts, future and timezone-naive timestamps, self-assertion where prohibited,
lossy representations, duplicate identifiers, caller-claim vs
verifier-established evidence divergence (value / asserter / fact_id / staleness),
digest mutation, sibling digest disagreement, self-referential digests,
cross-object substitution, suspended contracts, malformed admission shapes,
contract-declaration defects, key reordering, replay, and receipt context
substitution.

---

## 4. Latency by stage

Warm figures, warmup discarded. Microseconds.

| Stage | n | p50 | p95 | p99 | mean |
|---|---:|---:|---:|---:|---:|
| contract parse | 2000 | 9.6 | 15.1 | 18.0 | 10.6 |
| validation + binding | 2000 | 104.0 | 159.6 | 173.9 | 112.4 |
| canonicalization (JCS) | 2000 | 88.6 | 140.9 | 158.5 | 96.4 |
| canonical digest | 2000 | 87.9 | 158.6 | 166.8 | 98.8 |
| projection | 2000 | 122.9 | 170.7 | 181.5 | 124.2 |
| projection digest | 2000 | 61.0 | 79.5 | 89.1 | 59.4 |
| action check | 2000 | 7.8 | 11.2 | 13.4 | 8.4 |
| decision + receipt | 1000 | 376.4 | 484.7 | 562.4 | 377.6 |
| receipt verification | 1000 | 453.6 | 569.0 | 634.3 | 445.6 |
| **complete end-to-end** | **1000** | **701.6** | **1083.3** | **1149.9** | **760.8** |

Run-to-run variation on this shared machine is roughly ±15% on the end-to-end
figure (a prior run measured p50 616 µs). The relative cost of stages is stable
across runs; treat the absolute numbers as an order-of-magnitude baseline, not
a precise constant.

Stage figures are **not additive** into the end-to-end figure: `decision +
receipt` already contains projection and action check.

### What the distribution says

- **Canonicalization is the dominant primitive cost.** At ~96 µs it is roughly
  11× the action check and accounts for most of validation, digest, and
  projection cost. Every one of those stages canonicalizes.
- **The authorization logic itself is nearly free.** Action check is 8.4 µs —
  about 1% of the end-to-end path. Cost is overwhelmingly in canonical identity,
  not in deciding.
- **Verification costs as much as deciding** (446 µs vs 378 µs), because
  `verify_receipt` recomputes every binding from raw inputs rather than trusting
  any field in the receipt. This is the property that makes receipts
  independently checkable; the cost is the point, not a defect.
- **p99 is ~1.6× p50**, with no long tail — consistent with a pure-CPU path with
  no I/O, locking, or allocation cliffs.

---

## 5. Throughput

Single process, single thread, derived from warm mean latency.

| Metric | Rate |
|---|---:|
| Decisions / sec | 2,648 |
| Receipts / sec | 2,648 |
| Receipt verifications / sec | 2,244 |
| Complete E2E transactions / sec | 1,314 |

Decisions/sec and receipts/sec are the *same measurement*: receipt emission is
not separately callable at this commit. A complete E2E transaction is
decide-plus-independently-verify, which is why it is roughly half the decision
rate.

**Not claimed:** distributed throughput, multi-core scaling, or sustained
throughput under concurrency. No concurrency layer exists at this commit.

---

## 6. Scale curves

### Declared mediated actions — sublinear to linear

| Actions | mean latency | peak traced memory | decision |
|---:|---:|---:|---|
| 1 | 407 µs | 6.1 KiB | ALLOW |
| 10 | 1,202 µs | 9.4 KiB | ALLOW |
| 100 | 8,489 µs | 40.8 KiB | ALLOW |
| 1,000 | 81,995 µs | 366.1 KiB | ALLOW |

1000× the domain size costs ~201× the time and ~60× the memory. Growth is
linear in the large-N regime (the 100→1000 step costs ~9.7× for 10× the size)
with a fixed overhead that dominates at small N, which is why the endpoint ratio
reads as sublinear.

### Required facts — approximately linear

| Facts | mean latency | peak traced memory | decision |
|---:|---:|---:|---|
| 10 | 1,016 µs | 15.9 KiB | ALLOW |
| 100 | 6,531 µs | 140.5 KiB | ALLOW |
| 1,000 | 57,995 µs | 1.3 MiB | ALLOW |
| 10,000 | 566,644 µs | 13.1 MiB | ALLOW |

1000× the fact count costs ~558× the time and ~847× the memory — linear in
both, with no observed nonlinear degradation or cliff in the tested range. Each
10× step costs ~9–10× consistently.

**Practical reading:** a 10,000-fact contract takes ~0.57 s and ~13 MiB per
decision. That is workable for batch evaluation and marginal for interactive
use. The linearity means cost is predictable; the constant is dominated by
repeated canonicalization (§8, finding F2).

### NOT EVALUATED

| Dimension | Why |
|---|---|
| Multi-contract corpora | The runtime evaluates one artifact per invocation. No registry or cross-contract selection path exists whose scaling could be measured without inventing architecture. |
| Concurrent / distributed throughput | No concurrency or distribution layer exists at this commit. |
| Persistent storage scaling | The runtime is stateless over in-memory inputs. No storage backend exists to scale. |

---

## 7. Determinism

**Fully deterministic over fixed inputs**, across 100 repeated executions:

| Output | Stable? |
|---|---|
| Decision | yes |
| Reason code | yes |
| Contract digest | yes (1 distinct value / 100 runs) |
| Projection | yes (1 distinct value / 100 runs) |
| All 10 protected receipt fields | yes |

Notably `decision_time` is **stable**, because it is bound to the fact bundle's
own declared `now` rather than to wall-clock time at invocation. At this commit
there is therefore **no intentionally-varying receipt field** — the entire
receipt is byte-identical across replays of a fixed specimen.

**Scope of the claim:** this is determinism over fixed inputs in a single
process on one platform and one Python version. Cross-version, cross-platform,
and cross-implementation reproducibility were **not** tested and are not
claimed.

---

## 8. Findings

Recorded during the measurement run, not repaired during it.

**AC-035-F1 — Admission approvals are bound as evidence but are not an
authorization gate.**
Forging `admission.approvals` yields `ALLOW`. The evidence binding does hold:
`admission_digest` and `receipt_digest` both change, and a receipt issued for
the unforged admission does not verify against the forged one. So the forgery is
*detectable after the fact* but is not *prevented at decision time*. Whether
approvals should gate the decision is an unimplemented policy capability, not a
break in the evidence chain.

**AC-035-F2 — Canonicalization is repeated several times per transaction.**
Validation, digest, and projection each canonicalize, and `verify_receipt`
re-runs the whole decision path. At ~96 µs per canonicalization this is the
dominant cost and the clearest optimization target. It is *correct* — recomputing
rather than trusting is the security property — but it is not currently *cached*
within a single transaction.

**AC-035-F3 — No replay protection semantics exist.**
A replayed identical request produces an identical receipt. This documents
determinism, not replay *protection*: there is no nonce, sequence number, or
single-use semantics, so an intercepted receipt is indistinguishable from a
legitimately re-derived one. Recorded as an architectural gap, not a defect
against current specified behaviour.

**AC-035-F4 — `*_mutated.json` fixture names are misleading.**
`banking_payment_specimen_contract_mutated.json` and
`..._admission_mutated.json` are mutated *and correctly re-sealed*, so they are
validly-bound variant contracts rather than mutation attacks. The first draft of
this suite expected them to refuse; that expectation was wrong, not the
implementation. Genuine post-binding mutation (stale digest) is correctly
refused with `AC_DIGEST`.

---

## 9. Resource profile

| Metric | Value |
|---|---|
| Interpreter + import cost | 60–123 ms (mean 80 ms), out-of-process |
| Peak traced memory, one decision | 6.07 KiB |
| Peak traced memory, one verification | 6.19 KiB |
| Process max RSS (whole benchmark) | ~63 MiB |

Artifact sizes (compact JSON, bytes):

| Artifact | Size |
|---|---:|
| Contract artifact | 1,179 |
| Contract body | 773 |
| Canonical contract bytes | 773 |
| Action | 148 |
| Fact bundle | 675 |
| Projection | 479 |
| Receipt | 715 |

Process startup (~80 ms) is **more than two orders of magnitude larger** than a
single decision (~0.38 ms). Any deployment shape that pays interpreter startup
per decision would be dominated entirely by startup.

---

## 10. Limitations

- One synthetic banking specimen family. No real institutional rule has been
  integrated or evaluated.
- One machine, one Python version, one OS. No cross-platform comparison.
- Single process. No concurrency, no distribution, no persistence.
- Scale curves are synthetic: generated by widening a real specimen, not drawn
  from production corpora.
- Percentiles are nearest-rank, computed from in-process `perf_counter` samples.
- Memory figures are Python-level allocation (`tracemalloc`), not RSS
  attributable per decision.

## 11. Claim ceiling

This benchmark establishes only what it measures. It does **not** establish
production readiness, regulatory correctness, legal correctness, universal
source-to-rule derivation, arbitrary-domain compatibility, security
certification, distributed scalability, formal proof, or industry-wide
superiority.
