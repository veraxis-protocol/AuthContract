# AuthContract benchmark suite (AC-035)

The first end-to-end operational and performance baseline for AuthContract.

This suite measures **only capabilities that exist** at the commit under test.
Where the architecture cannot express a dimension, the result is recorded as
`NOT EVALUATED` rather than estimated.

## Reproduce

```bash
git clone https://github.com/veraxis-protocol/AuthContract.git
cd AuthContract
git checkout e4e1a97509df1a66c44b090c0a0ca0a03907f4dc
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
python3 benchmarks/run_benchmarks.py
```

Runtime is roughly 45 seconds. Results are written to `benchmarks/results/`.
The process exits non-zero if any correctness specimen fails.

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

**Throughput.** Single-process, single-threaded, derived from warm mean
latency. Not a distributed or multi-core claim.

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
