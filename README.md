# AuthContract — reference implementation

Bootstrap implementation of the two BRS-established repairs from the frozen
v0.2.1 normative baseline that are testable without a running policy engine.

| Module | Repair | Invariant |
|---|---|---|
| `authcontract/digest.py` | **R01** canonical object partition | AC-I06 |
| `authcontract/facts.py` | **R10** runtime fact contract | AC-I15 |
| `authcontract/projection.py` | machine-checkable projection domain + closed mediated-action universe | AC-016 / AC-017 |

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

## Install

```bash
pip install -e ".[test]"
```

## Verify a fixture

```bash
authcontract verify fixtures/valid.json
# or, without installing a console script:
python -m authcontract verify fixtures/valid.json
```

Exits `0` only on `PASS`; any refusal or error exits non-zero. Both cases
print one deterministic JSON object to stdout:

```json
{"status": "PASS", "reason_code": "OK", "contract_digest": "sha256:...", "fixture": "valid.json"}
```

`fixtures/` holds the committed specimen matrix:

| Fixture | Expected |
|---|---|
| `valid.json` | `PASS` / `OK` |
| `sibling_digest_mismatch.json` | `REFUSED` / `AC_DIGEST` |
| `self_referential.json` | `REFUSED` / `AC_DIGEST_SCOPE` |
| `malformed.json` | `REFUSED` / `AC_INVALID_STRUCTURE` |
| `cross_object_substitution.json` | `REFUSED` / `AC_DIGEST` |

This CLI implements only the currently-tested canonical partition/digest/binding
rules (`authcontract/digest.py`). It does not implement VEIP decision binding,
AEP reconstruction, or production PKI/provenance verification — those are
later gates.

## Project a fixture

```bash
authcontract project fixtures/banking_payment_specimen.json
```

Computes the deterministic operational projection of one fixture: an explicit
machine-checkable projection domain (`contract.projection_domain`), bound to
`contract_digest` and activation identity, with its own stable
`projection_digest`. A fixture with no `projection_domain` refuses with
`RUN_DOMAIN_ESCAPE` (e.g. AC-015's `fixtures/valid.json` — projection is
opt-in per contract, not retrofitted onto every fixture).

## Check an action against a fixture's projection domain

```bash
authcontract check-action fixtures/banking_payment_specimen.json fixtures/actions/send_payment_valid.json
```

The closed mediated-action universe pre-decision gate: `<action-json>` is a
path to a committed JSON file `{"action_type": "...", "parameters": {...}}`,
matching `<fixture>`'s own file-path convention. Refuses (never coerces or
drops fields) on:

| Condition | reason_code |
|---|---|
| projection's `activation_state` is not exactly `"ACTIVE"` (SUSPENDED, REVOKED, missing, or any other value) | `RUN_INACTIVE_CONTRACT` |
| action type not declared by the contract | `RUN_UNCLASSIFIED_ACTION` |
| unknown top-level field on the action input, unknown field anywhere in `projection_domain`/an action spec/a parameter spec | `RUN_DOMAIN_ESCAPE` |
| unknown parameter | `RUN_DOMAIN_ESCAPE` |
| missing required parameter | `RUN_DOMAIN_ESCAPE` |
| parameter value outside declared type/enum (e.g. a float where `decimal(N)` requires a string) | `RUN_DOMAIN_ESCAPE` |

`activation_state` is checked before the action is evaluated against the
domain at all — an inactive contract refuses every action, regardless of
whether the action itself is otherwise well-formed (AC-017 F1). `project()`
still builds a `Projection` for a SUSPENDED/REVOKED fixture (needed for
inspection and `select_matching_projection`'s overlap checks); only
`check_action`/`check-action` enforce activation.

`projection_domain`, each action spec, each parameter spec, and the action
input each have an exact allowed-key set (AC-017 F2) — see
`authcontract.projection.PROJECTION_DOMAIN_ALLOWED_KEYS` and its siblings.
An unrecognised key at any of these levels refuses rather than being
silently dropped, and a declared `required` field must be a real boolean
(not a truthy string or number).

Enum membership is checked with strict type semantics (AC-017 F3): each
enum member is itself validated against the parameter's declared
`value_type` when the domain is loaded (a boolean enum may contain only
`true`/`false`, an integer enum only genuine ints — never `bool`, a
`decimal(N)` enum only decimal strings), and membership comparison at
action-check time never falls back to Python's cross-type `==` — so an
integer `1` can never satisfy a boolean enum containing `true`, and vice
versa.

`fixtures/actions/` holds the committed action specimen matrix exercising each
case above against `fixtures/banking_payment_specimen.json`.

Two ACTIVE contracts matching the same action with no declared
precedence/composition rule, and zero ACTIVE contracts matching an action,
are refused as `CONTRACT_SCOPE_CONFLICT` and `RUN_UNCLASSIFIED_ACTION`
respectively — see `authcontract.projection.select_matching_projection` and
`tests/test_projection.py`. This is a bounded runtime closure check for one
synthetic specimen, not a universal policy-conflict solver, and is not yet
wired into a CLI command of its own (no VEIP-style decision layer exists to
call it from at this stage).

## Test

```bash
pytest -q
```

`.github/workflows/ci.yml` runs the full suite on every push and pull request.

Normative source: TDD-AC-001 v0.2.1
`sha256:3126c989186633ba060adf46281d757a0e74b5312779b4e800a3ae39bf071cfa`
