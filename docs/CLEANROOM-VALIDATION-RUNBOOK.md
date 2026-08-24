# Clean-room validation runbook

**Baseline main SHA:** `639ada4ba5b2cbd73af9089320a6cd3abcfd2228`

This runbook is written to be run literally, from a brand-new clone, by
an independent engineer with no prior context on this project. Every
command below was executed verbatim in a fresh disposable directory,
fresh Python virtual environment, no reused local state, before this
document was committed — see the AC-028 clean-room evidence transcript
for the exact recorded run.

---

## 1. What you are about to prove

You will clone the public repository, install it, run one PASS ("happy
path") specimen evaluation, run one FAIL/refusal specimen path, and
independently recompute the resulting evidence receipt from raw inputs.
You will then tamper one bound field in that receipt and confirm
verification refuses it. This proves the mechanical trust chain works
end to end for one bounded synthetic specimen — nothing broader.

---

## 2. Prerequisites

- Git
- Python 3.10 or 3.12 (this repository's CI tests both; 3.11 also works
  in practice but is not part of the tested matrix)
- `pip`
- Network access sufficient to clone the GitHub repository and install
  Python dependencies from the configured package index/download hosts.
  If all required dependencies are already locally cached, no additional
  dependency-download access is required. No secrets or credentials of
  any kind are required.

---

## 3. Clean-clone and checkout

```bash
git clone https://github.com/veraxis-protocol/AuthContract.git
cd AuthContract
git checkout 639ada4ba5b2cbd73af9089320a6cd3abcfd2228
```

---

## 4. Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

---

## 5. Happy path

Run the full test suite first, to confirm the clean-clone environment
matches what CI already verified:

```bash
pytest -q
```

Expected: all tests pass (342 at this baseline SHA).

Then run the one PASS specimen path directly through the CLI:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json \
  --execution-result SIMULATED_SUCCESS
```

**Expected result:** a JSON object with `"decision": "ALLOW"` and a full
receipt (`activation_id`, `admission_digest`, `contract_digest`,
`decision_time`, `exact_action_digest`, `execution_result`,
`projection_digest`, `receipt_digest`, `runtime_fact_set_digest`). Exit
code `0`.

---

## 6. Receipt/evidence artifact — what to inspect

The command above prints a JSON wrapper to stdout with a nested
`"receipt"` object. Save the full output, then extract just the receipt
object — `verify-receipt` (step 8) expects the receipt object alone, not
the wrapper:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json \
  --execution-result SIMULATED_SUCCESS > /tmp/my_receipt_full.json

python3 -c "
import json
d = json.load(open('/tmp/my_receipt_full.json'))
json.dump(d['receipt'], open('/tmp/my_receipt.json', 'w'))
"
```

Every field in `/tmp/my_receipt.json` (`activation_id`,
`admission_digest`, `contract_digest`, `decision`, `decision_time`,
`exact_action_digest`, `execution_result`, `projection_digest`,
`receipt_digest`, `runtime_fact_set_digest`) is a bound receipt field.
Their typed roles include digests, identifiers, decision/execution
values, and declared time values — not free-form log lines. The verifier
(step 8) independently recomputes and compares these bound values
against the raw inputs. `contract_digest` and `projection_digest` do
not change if you re-run this exact command (deterministic);
`decision_time` is bound to the fact bundle's own declared `now`, not
wall-clock time at invocation.

---

## 7. One accepted refusal vector

The repository's own accepted negative fixtures include a stale runtime
fact. Run the same specimen against it:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_stale.json \
  --execution-result SIMULATED_SUCCESS
```

**Expected result:** `"status": "REFUSED"`, `"reason_code":
"RUN_FACT_STALE"`, non-zero exit code, and **no receipt is issued** — a
refused decision does not produce evidence claiming a decision was made.

---

## 8. Independent receipt verification

Using the receipt saved in step 6, independently recompute and compare
every bound value from the raw inputs:

```bash
authcontract verify-receipt \
  /tmp/my_receipt.json \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json
```

**Expected result:** `"status": "PASS"`, `"reason_code": "OK"`, exit code
`0`. This recomputes `contract_digest`, `projection_digest`,
`runtime_fact_set_digest`, `exact_action_digest`, `admission_digest`, and
the decision itself from the three raw fixture files — it does not trust
any single field in the receipt at face value.

---

## 9. Mutate a bound receipt component

Tamper one field the receipt binds and confirm verification refuses it:

```bash
cp /tmp/my_receipt.json /tmp/tampered_receipt.json
python3 -c "
import json
r = json.load(open('/tmp/tampered_receipt.json'))
r['decision'] = 'DENY'
json.dump(r, open('/tmp/tampered_receipt.json', 'w'))
"
authcontract verify-receipt \
  /tmp/tampered_receipt.json \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json
```

**Expected result:** `"status": "REFUSED"`, `"reason_code":
"VEIP_RECEIPT_MISMATCH"`, message `"field 'decision' does not match the
independently recomputed value"` (the recomputed decision — `ALLOW`,
from the unchanged raw inputs — no longer matches the tampered receipt's
claimed `DENY`), non-zero exit code. The same test exists in the accepted suite
(`tests/test_cli_veip.py::test_cli_b8_mutation_matrix`); this step
reproduces it manually via the CLI rather than pytest, to prove it
outside the repository's own test harness.

---

## 10. What this proves

- A clean, public clone of this exact commit installs and runs without
  any private setup, secret, or manual fix.
- One PASS path and one REFUSED path both behave as documented.
- A third party running the public AuthContract verifier against the raw
  artifact/action/fact files can recompute and compare the bound receipt
  values.
- Tampering a single bound field in the receipt is detected, not
  silently accepted.

---

## 11. What this does NOT prove

- Production readiness of AuthContract for any real deployment.
- General regulatory, legal, or contractual correctness.
- Compatibility with any specific external enforcement rule or
  threshold — none has been integrated or tested.
- Broad automated natural-language source-to-rule semantic verification
  — not implemented; see `README.md`'s "Current status" and
  `docs/SOTA.md`'s current-vs-target boundary.
- General cross-domain correctness beyond the one synthetic banking
  payment specimen exercised above.
- Any security certification or formal proof of the full target
  architecture described in `docs/SOTA.md`.

This exercise establishes only clean-clone external testability of the
bounded MVP-alpha / synthetic Specimen 001 path, for this exact commit.

---

## 12. Replacing the synthetic specimen with an external rule

To evaluate a real enforcement rule or threshold instead of the synthetic
banking specimen, at minimum:

1. Author a new `.ac`-shaped JSON fixture (see
   `fixtures/banking_payment_specimen.json` for the shape: `contract`,
   `admission`, `activation`, `projection` domain, mediated-action
   declarations) encoding the external rule's declared action(s),
   parameter domain, and required runtime facts, instead of the
   synthetic payment fields.
2. Author corresponding action and fact fixtures (see
   `fixtures/actions/` and `fixtures/runtime/`) representing the
   external inputs to be evaluated against that rule.
3. Run the same `authcontract run-specimen` / `authcontract verify-receipt`
   commands above against the new fixtures in place of the synthetic
   ones.
4. Do **not** assume this repository already supports arbitrary
   enforcement domains, jurisdictions, or institutional rule types beyond
   what is exercised in steps 1–3 above — every claim in this runbook is
   bounded to what those specific fixtures exercise, not a general
   external-rule integration. Any gap discovered while doing this (an
   unsupported value type, an action shape the current projection
   domain rejects, etc.) is a legitimate finding to report back, not
   something to work around by modifying the fixture to avoid it.
