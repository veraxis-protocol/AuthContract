# AuthContract — TRL assessment (AC-035)

**Implementation assessed (DUT):** `e4e1a97509df1a66c44b090c0a0ca0a03907f4dc`
**Measured by harness:** `a7f6ba374b1362e624a3f8b912b265dd03da4cdd`
**Basis:** the AC-035 benchmark run only, as amended by AC-035A. Architecture documents, design intent,
and roadmap items are explicitly **not** counted as evidence.

---

## Evidence classification

The distinction that matters for TRL is *what kind* of evidence exists, not how
much of the system is written.

| Class | Status | What supports it |
|---|---|---|
| **Implemented** | YES | Canonical digest, projection, fact admission, decision path, receipt emission, receipt verification, Git merge-result gate. 2,401 lines across 8 runtime modules. |
| **Demonstrated** | YES | Complete E2E path executes: 7/7 E2E specimens, 38/38 adversarial specimens, 342 regression tests pass. |
| **Benchmarked** | YES | Per-stage latency distributions (n=1000–2000), *observed* sustained throughput (3 trials × 5 s per operation, not merely derived from latency), two scale curves, determinism over 100 replays, resource profile — all against a DUT verified byte-identical to the declared base commit before measuring. This document's basis. |
| **Externally validated** | **NO** | Every specimen, fixture, and expectation was authored by the same party that authored the implementation. No external rule has been encoded; no third party has reproduced or reviewed the results. Clean-room external *testability* was established in AC-028, but by this same executor — not by an independent evaluator. |
| **Production validated** | **NO** | No deployment, no real workload, no concurrency, no persistence, no operational history. |

---

## Current TRL: **4**, with partial TRL 5 characteristics

**TRL 4 — component and/or breadboard validation in a laboratory environment.**

### Why TRL 4 is met

- The complete architectural path runs end to end, not merely in parts.
- Behaviour is validated against an adversarial battery of 38 specimens
  spanning missing/unknown fields, malformed types, out-of-domain values,
  staleness, evidence divergence, digest mutation, substitution, and
  reordering — all failing closed.
- Tamper detection is exhaustive over the protected surface: all 20
  mutation-and-truncation variants of the receipt are detected.
- Behaviour is deterministic and measured, not asserted: 100 replays produce
  byte-identical receipts, and the digest and projection primitives each yield
  exactly one distinct value across 100 runs.
- Performance is characterized with distributions rather than single timings,
  and scaling is linear with no observed cliff across 1000× in two dimensions.

### Why TRL 5 is *not* met

TRL 5 requires validation in a **relevant** environment. Every element of the
measured environment is laboratory-constructed:

- One synthetic banking specimen family; no externally-authored rule has ever
  been evaluated (roadmap X5).
- Single process, single machine, no concurrency, no persistence, no
  operational load (roadmap L1, L2).
- Multi-contract evaluation — the shape any real deployment takes — does not
  exist and was recorded `NOT EVALUATED` (roadmap X1).
- Determinism is confirmed on exactly one platform and one Python version;
  cross-environment reproducibility, which is what makes canonical identity
  useful between parties, is untested (roadmap X4).

### Why the partial TRL 5 characteristics are real

The rigor of the *evidence discipline* exceeds typical TRL 4: measured
distributions rather than anecdotes, an adversarial matrix rather than
happy-path demos, findings recorded rather than silently repaired (AC-035-F1
through F4), explicit `NOT EVALUATED` markers rather than estimates, observed
sustained throughput rather than a latency reciprocal, and a device-under-test
whose identity is verified before measurement rather than asserted afterwards.
That methodological maturity is a genuine TRL 5 characteristic.

It does not by itself raise the TRL. **TRL is determined by the environment the
evidence was gathered in, not by the quality of the measurement** — improving
benchmark methodology (as AC-035A did) makes the TRL 4 assessment *better
supported*, not higher. External independent reproduction remains absent, which
is the binding constraint.

---

## What would move AuthContract to TRL 5

All four are necessary; none alone is sufficient.

1. **An externally-authored rule evaluated end to end** (roadmap X5), with every
   unsupported construct reported as a finding rather than worked around by
   reshaping the rule to fit.
2. **Multi-contract evaluation implemented and measured** (roadmap X1),
   including deterministic selection and explicit conflict semantics — closing
   the largest `NOT EVALUATED` gap.
3. **Cross-platform and cross-version determinism demonstrated** (roadmap X4):
   identical digests and receipts across at least two Python versions and two
   operating systems. Canonical identity that only holds in one environment
   cannot support third-party verification.
4. **Independent reproduction by a party that did not author the system**
   (roadmap L4) — someone else running the benchmark, on their hardware,
   reaching the same correctness results.

## What would move it to TRL 6

Beyond the above: sustained operation under concurrent load with a stated
saturation point (L1), a documented operating envelope with measured limits
(L3), and an independent security review whose findings are published
unmodified (L4).

---

## Claim ceiling

This assessment is bounded by the measurements in
[`docs/BENCHMARKS.md`](BENCHMARKS.md). It does not establish production
readiness, regulatory or legal correctness, universal source-to-rule
derivation, arbitrary-domain compatibility, security certification, distributed
scalability, formal correctness, or comparative standing against any other
system.
