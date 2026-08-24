# AGENTS.md — instructions for AI coding/operations agents

Machine-facing operating instructions for this repository. Every command and
behavior below was executed against committed fixtures at this commit. No
marketing language, no aspirational capability.

**Hard rule: do not invent commands, flags, interfaces, endpoints, or maturity
claims that are not listed here.** If a capability you need is not documented in
this file, it does not exist in this repository. Report that as a limitation
rather than improvising a substitute or assuming an undocumented interface.

---

## 1. What AuthContract is

AuthContract turns an institutional rule into a canonical, digest-bound artifact,
evaluates a proposed action against that rule together with runtime facts, and
issues a decision receipt whose every bound value can be independently
recomputed from the raw inputs.

Implemented chain:

```
contract artifact
  → canonical identity (RFC 8785 JCS + SHA-256) and sibling digest binding
  → deterministic projection into a declared action domain
  → runtime fact admission (issuer / trust basis / freshness / evidence binding)
  → action check against the projection
  → ALLOW or REFUSE
  → decision receipt (on ALLOW only)
  → independent receipt verification from raw inputs
```

## 2. Current maturity

Experimental reference implementation, **TRL 4**. Implemented, tested, and
benchmarked against **one synthetic banking specimen family**.

**Automated natural-language source-to-rule comparison is NOT implemented end to
end.** It is the project's target capability. Worked examples in `README.md`
below the `# How it works — the full model` divider describe target behavior, not
current behavior. Do not represent it as working.

## 3. Requirements

- Python **>= 3.10** (`pyproject.toml: requires-python = ">=3.10"`). CI tests 3.10 and 3.12.
- `git`.
- No credentials, services, or network beyond clone and dependency install.

## 4. Installation

```bash
git clone https://github.com/veraxis-protocol/AuthContract.git
cd AuthContract
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
```

Verify: `pytest -q` → `342 passed`.

**Not on PyPI.** `pip install authcontract` will not work. Install from source only.

## 4.1 Real repository skills

Agents may use only these implemented workflows:

- `make test` — execute the committed test suite;
- `make falsify` — exercise the bounded PASS/refusal/tamper cases;
- `make no-network` — run the local install/import/test/CLI network guard;
- `make sbom` — generate the bounded candidate SBOM; and
- the six CLI commands listed below.

None of these commands publishes, deploys, attests a release, or adjudicates its
own result. Producers must state `NOT SELF-ADJUDICATED` and stop for independent
verification.

## 5. Supported CLI commands

Exactly six. Any other subcommand does not exist.

| Command | Purpose |
|---|---|
| `authcontract verify <artifact>` | Verify one rule artifact's canonical identity |
| `authcontract project <artifact>` | Project a rule into its declared runtime action domain |
| `authcontract check-action <artifact> <action>` | Check an action against the declared domain |
| `authcontract git-gate <context>` | Check a CI result against the version that would actually merge |
| `authcontract run-specimen <artifact> <action> <facts> --execution-result <R>` | Full end-to-end check; issues a receipt on PASS |
| `authcontract verify-receipt <receipt> <artifact> <action> <facts>` | Recompute the receipt bindings from raw inputs and compare |

`--execution-result` accepts exactly: `NOT_EXECUTED`, `SIMULATED_SUCCESS`, `SIMULATED_FAILURE`.

All commands emit **single-line JSON on stdout**.

## 6. Canonical successful end-to-end command

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json \
  --execution-result SIMULATED_SUCCESS
```

Expect `"status": "PASS"`, `"decision": "ALLOW"`, `"reason_code": "OK"`, a
`receipt` object with 10 bound fields, and **exit code 0**.

## 7. Canonical refusal commands

Undeclared action → `RUN_UNCLASSIFIED_ACTION`:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_unknown_action_type.json \
  fixtures/runtime/facts_valid.json \
  --execution-result SIMULATED_SUCCESS
```

Stale runtime fact → `RUN_FACT_STALE`:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_stale.json \
  --execution-result SIMULATED_SUCCESS
```

Both return `"status": "REFUSED"` and **exit code 1**. **No receipt is issued on
refusal.** A refusal is correct, expected behavior — do not treat it as a failure
to be worked around, and do not retry with altered inputs to force an ALLOW.

## 8. Receipt verification

```bash
authcontract verify-receipt \
  fixtures/runtime/receipt_valid.json \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json
```

Expect `"status": "PASS"`, `"reason_code": "OK"`, exit `0`. This recomputes every
bound value from raw inputs and trusts no field in the receipt.

`verify-receipt` requires the **receipt object itself**, not the full
`run-specimen` wrapper. Extract it first:

```bash
authcontract run-specimen ... > /tmp/full.json
python3 -c "import json; json.dump(json.load(open('/tmp/full.json'))['receipt'], open('/tmp/receipt.json','w'))"
```

Passing the wrapper returns `VEIP_RECEIPT_MALFORMED`.

## 9. Exit-code semantics

| Exit | Meaning |
|---|---|
| `0` | PASS / ALLOW |
| `1` | REFUSED, or an error condition |

Branch on the JSON `status` and `reason_code` fields rather than parsing prose.

## 10. Reason codes

`reason_code` is a **machine-facing identifier** in the current implementation;
`OK` on success. Branch on it rather than on prose — within the currently
documented and tested interface it is the intended programmatic signal.

**Cross-version stability is not guaranteed.** This repository establishes no
versioned public-interface commitment that reason codes remain unchanged across
future releases; no such versioning or pinning mechanism exists yet. Treat the
set below as accurate for this commit, and re-check it if you upgrade. Do not
represent these codes as a stable API contract.

`message` (present on refusal) is human-readable and **not** contractual at any
version — do not parse it.

Codes observed in the implementation, by family:

- **Artifact/identity:** `AC_DIGEST`, `AC_DIGEST_SCOPE`, `AC_INVALID_JSON`, `AC_INVALID_STRUCTURE`, `AC_IO_ERROR`, `AC_INTERNAL_ERROR`
- **Projection/action:** `RUN_UNCLASSIFIED_ACTION`, `RUN_DOMAIN_ESCAPE`, `RUN_INACTIVE_CONTRACT`, `CONTRACT_SCOPE_CONFLICT`
- **Runtime facts:** `RUN_FACT_STALE`, `RUN_FACT_INADMISSIBLE`, `RUN_FACT_IDENTITY_MISMATCH`, `RUN_FACT_EVIDENCE_MISMATCH`, `RUN_FACT_UNATTESTED`, `RUN_FACT_SELF_ASSERTED`, `RUN_FACT_TRUST_BASIS`, `RUN_FACT_REPRESENTATION`, `RUN_FACT_FUTURE_TIMESTAMP`, `RUN_FACT_TIME_UNVERIFIABLE`, `RUN_FACT_TYPE_UNSUPPORTED`, `RUN_FACT_CORROBORATION_MISSING`, `RUN_FACT_CONTRACT_INVALID`
- **Orchestration/receipt:** `VEIP_REFUSED`, `VEIP_MALFORMED_INPUT`, `VEIP_MISSING_ACTIVATION_ID`, `VEIP_INVALID_EXECUTION_RESULT`, `VEIP_FACT_BUNDLE_INCOMPLETE`, `VEIP_RECEIPT_MALFORMED`, `VEIP_RECEIPT_MISMATCH`
- **Git gate:** `GIT_FAIL`, `GIT_ERROR`, `GIT_UNRESOLVED`, `GIT_NEUTRAL_CONCLUSION`, `GIT_MERGE_RESULT_UNVERIFIED`, `GIT_GATE_REFUSAL`

## 11. Python library integration

```python
import json
from authcontract.veip import run_specimen, verify_receipt

artifact = json.load(open("fixtures/banking_payment_specimen.json"))
action   = json.load(open("fixtures/actions/send_payment_valid.json"))
facts    = json.load(open("fixtures/runtime/facts_valid.json"))

result = run_specimen(artifact, action, facts, execution_result="SIMULATED_SUCCESS")
# result.decision -> "ALLOW"; result.reason_code -> "OK"

if result.decision == "ALLOW":
    check = verify_receipt(result.receipt, artifact, action, facts)
    # check.status -> "PASS"
```

`run_specimen` returns a `RunResult` (`decision`, `reason_code`, `message`,
`receipt`). `verify_receipt` returns a `VerifyResult` (`status`, `reason_code`,
`message`).

**Refusals are return values, not exceptions.** `run_specimen` does not raise on
an ordinary refusal. Check `.decision` / `.status`; do not wrap these calls in
try/except expecting refusal to surface as an exception.

Other useful entry points: `authcontract.digest` (`contract_digest`,
`verify_artifact`, `canonical_bytes`), `authcontract.projection` (`project`,
`check_action`, `projection_digest`).

## 12. GitHub merge-gate workflow

`.github/workflows/authcontract-gate.yml` exists and runs `authcontract git-gate`
on `pull_request` events. It re-resolves the base ref live and proves the
evaluated commit contains both base and PR head.

**The workflow's presence does NOT mean GitHub requires it.** Whether a check is
*enforced* — whether branch protection blocks a merge on failure — is separate
repository configuration (branch protection / rulesets), not workflow content.
Do not report the gate as an enforced required status check. If you need to know
what is actually required to merge, read the repository's branch-protection
settings directly.

## 13. Interfaces that do NOT exist

Do not attempt these, and do not report them as available:

- **No PyPI package.** Source install only.
- **No HTTP or gRPC service.** No server, no endpoint, no daemon. In-process library and CLI only.
- **No persistence layer.** Stateless over in-memory inputs. Receipts are not stored for you.
- **No multi-contract registry.** One artifact per invocation; no cross-contract selection or resolution.
- **No replay protection.** Replayed identical requests produce identical receipts — that is determinism, not protection. No nonce, sequence, or single-use semantics.
- **No concurrency or distribution layer.**
- **No telemetry.**
- **No authentication, identity, or PKI subsystem** of production grade.

## 14. Claim ceiling

This repository establishes **only** what its measurements demonstrate, bounded
to one synthetic banking specimen family on a single machine and process. It does
**not** establish: production readiness; regulatory or legal correctness;
universal source-to-rule derivation; arbitrary-domain compatibility; security
certification; distributed scalability; formal proof; or comparative superiority
over any other system.

Do not soften, omit, or paraphrase this ceiling when summarizing the project.

## 15. Licensing

**No license is declared.** No `LICENSE` file exists and `pyproject.toml`
declares no license field, so default copyright applies and no usage rights are
granted. Treat this as source-available for evaluation and reading. **Do not
describe it as open source**, and do not assume redistribution or derivative
rights. Direct licensing questions to the repository owner.

## 16. Prohibition on invention

If asked to do something this repository does not support:

1. State plainly that the capability does not exist here.
2. Cite the relevant section above.
3. Do **not** fabricate a command, flag, endpoint, config key, or package name.
4. Do **not** infer capability from the roadmap, from target-behavior examples,
   or from the presence of a workflow file.
5. Do **not** weaken or bypass a refusal to produce a desired outcome.

Further reading: [`README.md`](README.md) · measured evidence
[`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) · maturity
[`docs/TRL-ASSESSMENT.md`](docs/TRL-ASSESSMENT.md) · planned work
[`docs/ROADMAP.md`](docs/ROADMAP.md).
