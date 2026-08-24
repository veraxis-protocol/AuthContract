# AuthContract benchmark baseline — AC-039 (current)

**DUT_BASE_SHA (implementation measured):** `8e04e9c5e60f1e4cb604689419c0bb4c24ec903b`
**BENCHMARK_HARNESS_SHA (harness that measured it):** `8e04e9c5e60f1e4cb604689419c0bb4c24ec903b`
**Work order:** AC-035 / AC-035A methodology, re-measured under AC-039
**Raw results:** [`benchmarks/results/AC-039-*.json`](../benchmarks/results/)

> **Why this exists.** AC-039 introduced a controlled dependency set
> (`constraints.txt`), which changes the environment the implementation runs
> against. Performance and correctness are properties of the code *plus* its
> dependencies, so the earlier AC-035A figures stopped being valid measurements
> of the current environment the moment that set changed. They are preserved
> unmodified in [`docs/BENCHMARKS.md`](BENCHMARKS.md) as the historical AC-035A
> record and are **not** presented as current. This document supersedes them.

> **Provenance.** Before measuring, the harness diffs every device-under-test
> path against `DUT_BASE_SHA` and refuses to run on any drift (exit 2). This
> run: `verified: true`, zero modified DUT files. It additionally records the
> declared-versus-installed dependency set: `matches_declared_set: true`.

---

## 1. Environment

| | |
|---|---|
| Python | 3.11.15 (CPython) |
| Platform | Linux x86_64 (glibc 2.39) |
| Dependency control | `constraints.txt`, verified against the installed set at measurement time |
| Runtime dependency | `rfc8785==0.1.4` |
| Test dependencies | `pytest==9.1.1`, `iniconfig==2.3.0`, `packaging==25.0`, `pluggy==1.6.0`, `Pygments==2.21.0`, `tomli==2.4.1` |
| Process | single, single-threaded |
| Wall time for the full run | 95.4 s |

Figures are environment-specific. Absolute latencies will differ on other
hardware; the *shape* of the curves and the relative cost of stages are the
transferable results.

---

## 2. Correctness

| Battery | Result |
|---|---|
| End-to-end specimens | **7 / 7 passed**, 0 failed |
| Adversarial specimens | **38 / 38 passed**, 0 failed, 0 `NOT EVALUATED` |
| Regression suite | **342 passed** |
| Public falsification harness (`falsify.py`) | **5 / 5 cases matched** their declared expected disposition |

The adversarial battery spans missing and unknown fields, malformed types,
out-of-domain values, staleness, evidence divergence, digest mutation,
substitution, and reordering. Every one fails closed.

---

## 3. Latency by stage

Microseconds. Distributions, not single timings.

| Stage | mean | p50 | p95 | p99 |
|---|---|---|---|---|
| `action_check` | 5.33 | 4.97 | 7.05 | 8.75 |
| `contract_parse` | 9.92 | 9.16 | 13.15 | 17.61 |
| `projection_digest` | 44.31 | 43.18 | 50.11 | 66.78 |
| `canonicalization` | 85.12 | 80.60 | 118.84 | 137.61 |
| `canonical_digest` | 87.27 | 83.40 | 108.72 | 150.61 |
| `validation_and_binding` | 87.86 | 85.87 | 98.36 | 119.04 |
| `projection` | 95.68 | 93.59 | 106.93 | 144.29 |
| `decision_and_receipt` | 273.74 | 273.74 | 372.52 | 453.85 |
| `receipt_verification` | 285.78 | 275.02 | 345.32 | 445.69 |
| **`complete_end_to_end`** | **585.64** | **575.76** | **675.37** | **736.88** |

Single un-warmed execution in an already-imported interpreter: 631.6 µs.
Out-of-process interpreter startup plus `import authcontract.veip`: 63.4 ms mean
over 5 samples — dominated by interpreter startup, not by this project.

---

## 4. Throughput — two different things, reported separately

Conflating these is the most common way a benchmark misleads, so both are given.

**Observed sustained throughput** — a continuous single-threaded loop over a
fixed window. 3 trials × 5 s, after a 1 s warmup. This is a measurement.

| Operation | min | median | max | total ops |
|---|---|---|---|---|
| Complete end-to-end | 1665.1 | **1680.0** | 1722.5 | 25,340 |
| Decision + receipt | — | **3596.7** | 3612.6 | — |

**Latency-derived rate** — the arithmetic reciprocal of warm mean latency. This
is *not* a measurement: it assumes zero loop overhead and no drift.

| Operation | derived rate |
|---|---|
| Complete end-to-end | 1707.5 /s |
| Decision | 3491.3 /s |

Where the two disagree, **the observed figure is the real one**. Units are
operations per second, single-threaded, single-process.

**Not claimed:** distributed throughput, multi-core scaling, or throughput under
concurrency. No concurrency or distribution layer exists at this commit.

---

## 5. Scaling

Linear-to-superlinear with no observed cliff, across 1000× in two dimensions.

**Declared mediated actions in the projection domain** (p50 µs):

| actions | 1 | 10 | 100 | 1000 |
|---|---|---|---|---|
| p50 | 255.9 | 914.0 | 7,132.0 | 72,776.5 |

**Required facts matched against the supplied bundle** (p50 µs, peak traced memory):

| facts | 10 | 100 | 1000 | 10000 |
|---|---|---|---|---|
| p50 | 761.4 | 5,448.0 | 54,761.3 | 572,254.9 |
| peak | 15.9 KiB | 140.5 KiB | 1.30 MiB | 13.15 MiB |

Every level returned `ALLOW` / `OK` — the curves measure cost, not a change in
disposition.

**NOT EVALUATED:** concurrent or distributed throughput, and multi-contract
corpora. The implementation evaluates one artifact per invocation and there is
no multi-contract registry, so neither could be measured rather than estimated.

---

## 6. Determinism

`fully_deterministic_over_fixed_inputs: true`.

- Contract digest: **1** distinct value across repeated execution.
- Projection: **1** distinct value.
- Valid and refused specimens: decision, reason code and all protected receipt
  fields stable across replays.
- `decision_time` is stable because it binds to the fact bundle's declared
  `now`, not to wall-clock time — so there is no intentionally-varying receipt
  field at this commit.

**Bounded:** this is determinism over fixed inputs in a single process. It is
**not** a claim about cross-version, cross-platform, or cross-implementation
reproducibility. None of those was tested, and closing that gap is roadmap X4.

---

## 7. Resource profile

| | |
|---|---|
| Peak traced memory, one decision | 6.07 KiB |
| Peak traced memory, one verification | 6.19 KiB |
| Whole-process peak RSS (incl. interpreter and harness) | 67,708 KB |
| Canonical contract bytes | 773 |
| Contract artifact / projection / receipt / fact bundle | 1,179 / 479 / 715 / 675 bytes |

---

## 8. Claim ceiling

These measurements establish **only** what they measured: one synthetic banking
specimen family, one machine, one operating system, one Python version, one
process, one dependency set.

They do **not** establish production readiness; regulatory or legal correctness;
universal source-to-rule derivation; arbitrary-domain compatibility; security
certification; distributed or concurrent scalability; formal proof; or
comparative superiority over any other system.

Independent reproduction by a party that did not author the system remains
absent. That is the binding constraint on maturity — see
[`docs/TRL-ASSESSMENT.md`](TRL-ASSESSMENT.md).
