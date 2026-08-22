# AuthContract — reference implementation

Bootstrap implementation of the two BRS-established repairs from the frozen
v0.2.1 normative baseline that are testable without a running policy engine.

| Module | Repair | Invariant |
|---|---|---|
| `authcontract/digest.py` | **R01** canonical object partition | AC-I06 |
| `authcontract/facts.py` | **R10** runtime fact contract | AC-I15 |

## Why the partition

v0.1 placed `approvals[]` inside the hashed `payload` while requiring each
approval to carry a digest of that payload. That needs a SHA-256 fixed point
over a structure containing its own digest — infeasible. `digest.py` rejects
the structure rather than documenting a convention against it.

## Why the fact gate

A control requiring `secondary_approval.present == true` is decorative if the
governed agent may assert that fact. `facts.py` runs admissibility **before**
policy evaluation: issuer, trust basis, freshness, assertion path,
self-assertion policy, corroboration, and wire representation.

## On R02

The v0.1 float64 counterexample was **refuted**. Tested against OPA v1.19.1 on
its own JSON decode path: 0/5 divergences — OPA preserves `json.Number` and
compares exactly. The surviving hazard is a *host decoder* flattening
`decimal(scale)` before the engine sees it. `test_float_ingestion_is_rejected`
covers it at the ingestion boundary, which is where it actually lives.

## Run

```bash
pip install -e ".[test]"
pytest -q
```

Normative source: TDD-AC-001 v0.2.1
`sha256:3126c989186633ba060adf46281d757a0e74b5312779b4e800a3ae39bf071cfa`
