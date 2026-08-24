# AuthContract benchmark suite (AC-035)

The first end-to-end operational and performance baseline for AuthContract.

This suite measures **only capabilities that exist** at the commit under test.
Where the architecture cannot express a dimension, the result is recorded as
`NOT EVALUATED` rather than estimated.

## Two commits, and why that matters

A benchmark harness cannot exist at the commit it measures — it is written
afterwards. So there are two distinct SHAs, and conflating them makes the
results unreproducible:

| | |
|---|---|
| **`DUT_BASE_SHA`** | `e4e1a97509df1a66c44b090c0a0ca0a03907f4dc` — the AuthContract implementation **being measured** |
| **`BENCHMARK_HARNESS_SHA`** | `a7f6ba374b1362e624a3f8b912b265dd03da4cdd` — the commit containing the **harness that measured it** |

**Check out the harness commit, not the DUT commit.** `benchmarks/` does not
exist at `e4e1a975`; an earlier draft of this file said otherwise and was
wrong.

What makes the two safely comparable is not assertion but verification: before
any measurement runs, `verify_dut_unchanged()` diffs every device-under-test
path (`authcontract/`, `tests/`, `fixtures/`, `.github/`, `pyproject.toml`,
`README.md`, and the SOTA/language/runbook docs) against `DUT_BASE_SHA`. If any
byte differs, the harness **refuses to run** and exits 2, because results that
silently measured a drifted tree would not describe the commit they claim to.

## Reproduce

```bash
git clone https://github.com/veraxis-protocol/AuthContract.git
cd AuthContract
git checkout a7f6ba374b1362e624a3f8b912b265dd03da4cdd   # BENCHMARK_HARNESS_SHA
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
python3 benchmarks/run_benchmarks.py
```

Equivalently, check out the AC-035 branch head — the harness code is unchanged
between `a7f6ba3` and the branch tip, which adds only refreshed results and
documentation.

The run prints the DUT and harness SHAs it verified before measuring. Runtime
is roughly 100 seconds (the sustained-throughput phase alone is 3 operations ×
3 trials × 6 s). Results are written to `benchmarks/results/`. Exit codes: `0` all
specimens pass, `1` a correctness specimen failed, `2` DUT drift detected and
nothing was measured.

## Layout

| Path | Purpose |
|---|---|
| `run_benchmarks.py` | Entry point; runs every phase and writes results |
| `harness.py` | Timing, memory, environment capture, synthetic specimen generation |
| `specimens/__init__.py` | Declarative specimen table with expected behaviour classes |
| `results/` | Raw JSON output (committed, so results are auditable without re-running) |

## What is measured

**Path exercised.** Contract artifact → parse → digest-scope validation and
sibling binding → RFC 8785 canonicalization → SHA-256 contract digest →
deterministic projection → runtime fact admission → action check →
ALLOW/REFUSE decision → receipt emission → independent receipt verification →
mutation detection.

**Stage latency.** Each stage timed separately with warmup discarded, reported
as n/min/p50/p95/p99/max/mean/stdev in microseconds. Very fast stages use an
inner batch so they are measured above timer resolution rather than quantized
to zero.

**Throughput — two figures, deliberately kept apart.**

- *Latency-derived rate*: the reciprocal of warm mean latency. This is
  arithmetic, not measurement — it assumes zero loop overhead and no drift.
- *Observed sustained rate*: a continuous single-threaded loop over a fixed
  wall-clock window (3 trials × 5 s, 1 s warmup each), counting completed
  operations.

Both are reported. Where they disagree, the observed figure is the real one.
Neither is a concurrency or distribution claim — no such layer exists.

**Scale curves.** Two dimensions the architecture can genuinely express:
declared mediated actions (1/10/100/1000) and required facts (10/100/1000/10000).
Synthetic specimens are re-sealed with a recomputed contract digest so they are
genuinely valid — otherwise the curve would measure the refusal path.

**Correctness and adversarial matrices.** Expectations are stated as behaviour
*classes* (ALLOW vs fail-closed REFUSE) rather than exact reason codes. The
class is the security-relevant property; the observed reason code is recorded
alongside as evidence, so a change in refusal taxonomy shows up in the results
without the assertion being weakened into a tautology.

**Determinism.** 100 repeated executions per specimen, comparing decision,
reason code, contract digest, projection, and every protected receipt field.

## Methodology notes worth knowing

- **`receipt_verification` re-runs the entire decision path.** `verify_receipt`
  deliberately recomputes every binding from raw inputs rather than trusting any
  field in the receipt. That is why verification costs about as much as the
  original decision — it is a correctness property, not an inefficiency.
- **`decision_and_receipt` supersets `projection` and `action_check`.** Stage
  figures are not additive into the end-to-end figure.
- **`decisions_per_second` and `receipts_per_second` are the same measurement.**
  Receipt emission is not separately callable at this commit; `run_specimen`
  decides and emits in one pass.
- **Percentiles use nearest-rank.** For these sample sizes the difference from
  an interpolating definition is far below the measurement noise floor.
- **Memory is `tracemalloc` peak**, i.e. Python-level allocation attributable to
  one execution, excluding interpreter baseline and allocator caching.

## A finding about the `*_mutated.json` fixtures

The repository's `banking_payment_specimen_contract_mutated.json` and
`banking_payment_specimen_admission_mutated.json` fixtures are mutated **and
correctly re-sealed** — their recomputed digest matches their declared digest.
They are therefore validly-bound *variant* contracts, not post-binding mutation
attacks, and `ALLOW` is the correct outcome for them.

The first draft of this suite expected them to refuse. That expectation was
wrong, not the implementation. The genuine attack — altering contract-bound
material while leaving the declared digest stale — is constructed
programmatically in the runner as `E2E-06`, `ADV-35`, and `ADV-36`, and is
correctly refused with `AC_DIGEST`.

This is recorded rather than quietly corrected because the naming of those
fixtures invites exactly this misreading.

## Claim ceiling

These measurements establish only what they measure: a bounded MVP-alpha
implementation, one synthetic banking specimen family, one machine, one
process. They do **not** establish production readiness, regulatory or legal
correctness, universal source-to-rule derivation, arbitrary-domain
compatibility, security certification, distributed scalability, formal
correctness, or comparative superiority over any other system.
