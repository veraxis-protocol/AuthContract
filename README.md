# AuthContract

**Proof that the rule you shipped is actually supported by the source.**

AuthContract turns an institutional rule into a canonical, testable artifact — then keeps that artifact bound to the actions your software takes, and issues evidence anyone can independently recompute.

```text
source → rule → PR → check → merge → runtime → proof
```

**Implementation status:** experimental reference implementation (TRL 4). The current code tests the mechanical trust chain for one synthetic banking specimen; the automated natural-language source-to-rule comparison shown in the examples below is target behavior and is not yet implemented end to end. Nothing here is production-ready, audited, or certified. See [What is *not* implemented](#what-is-not-implemented) — read it before forming expectations — and [Current status](#current-status) for the full boundary.

---

## The problem this addresses

Software increasingly does consequential things on an institution's behalf: sends payments, approves transactions, changes customer state. Developers translate requirements into executable rules — and a rule can look reasonable, pass ordinary unit tests, and still introduce a threshold or exception the source never established.

Ordinary tests ask *did the code run correctly?* AuthContract adds a second question: **which rule authorized this action, what version applied, and can anyone else verify that independently?**

---

## Quick start

Requires **Python 3.10+** and `git`. No credentials, no services, no network beyond the clone and dependency install.

```bash
git clone https://github.com/veraxis-protocol/AuthContract.git
cd AuthContract
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
```

Confirm the install:

```bash
make test          # expect: 342 passed
make falsify       # expect: 4/4 bounded outcomes observed
```

> Not on PyPI. Install from source, as above.

---

## A successful end-to-end run

This exercises the whole implemented chain — contract → validation and digest binding → projection → runtime facts → authorization → receipt:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json \
  --execution-result SIMULATED_SUCCESS
```

Actual output (reformatted for reading; the CLI emits one line of JSON):

```json
{
  "status": "PASS",
  "decision": "ALLOW",
  "reason_code": "OK",
  "artifact": "banking_payment_specimen.json",
  "action_file": "send_payment_valid.json",
  "facts_file": "facts_valid.json",
  "receipt": {
    "activation_id": "act:banking-specimen-001:v1",
    "contract_digest": "sha256:d94a65607e756a2d4e3c92fc1de4a23d7cf614dd1dbe8f3fd20fe6e459c9b842",
    "projection_digest": "sha256:c7f6dccb5f3f6b7c70b305e838ad87877805d19bd6d3e225f41a40151aa5659b",
    "runtime_fact_set_digest": "sha256:57fe990d8320793f92894d31d16d55598e8f30cb63d227bd35e9b2bb3daaab09",
    "exact_action_digest": "sha256:55bc4dd36b705f58a123c110bc4d5b398182524cb51c4fae499c2c1455d6470f",
    "admission_digest": "sha256:1c631041f126de51afeeb5838d47501616083cd31d4ad0ca9691c71a74ec2a68",
    "decision": "ALLOW",
    "execution_result": "SIMULATED_SUCCESS",
    "decision_time": "2026-08-23T00:10:00+00:00",
    "receipt_digest": "sha256:2cfa754d40ed2b9df4a4be7dcc0082bbc1097e2b6a88cb73ea9f9af950bc5a9a"
  }
}
```

Exit code `0`. The action was permitted, and you now hold a receipt describing exactly what authorized it.

### Independently verify that receipt

The receipt is only worth something if someone else can check it without trusting you. It trusts no field in the receipt itself.

Re-run the evidence — independently recompute the receipt bindings from the raw artifact, action, and fact inputs and compare:

```bash
authcontract verify-receipt \
  fixtures/runtime/receipt_valid.json \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_valid.json
```

```json
{"status": "PASS", "reason_code": "OK", "receipt": "receipt_valid.json",
 "artifact": "banking_payment_specimen.json", "action_file": "send_payment_valid.json",
 "facts_file": "facts_valid.json"}
```

Exit code `0`. Tamper with any bound field and this refuses — see below.

---

## A deliberate refusal

**A refusal is a successful demonstration.** The system is designed to fail closed, and you should see it do so.

### Refusal 1 — an action outside the declared rule

The specimen declares exactly one mediated action, `send_payment`. Here we propose `issue_refund`:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_unknown_action_type.json \
  fixtures/runtime/facts_valid.json \
  --execution-result SIMULATED_SUCCESS
```

```json
{"status": "REFUSED", "reason_code": "RUN_UNCLASSIFIED_ACTION",
 "message": "RUN_UNCLASSIFIED_ACTION: 'issue_refund' is not in the closed mediated-action universe for this projection"}
```

Exit code `1`. **In plain language:** the rule never granted authority to issue refunds, so AuthContract refuses rather than improvising. An undeclared action is not a permitted action.

### Refusal 2 — a runtime fact too old to rely on

The contract requires a secondary approval no older than 15 minutes. This bundle supplies a stale one:

```bash
authcontract run-specimen \
  fixtures/banking_payment_specimen.json \
  fixtures/actions/send_payment_valid.json \
  fixtures/runtime/facts_stale.json \
  --execution-result SIMULATED_SUCCESS
```

```json
{"status": "REFUSED", "reason_code": "RUN_FACT_STALE",
 "message": "RUN_FACT_STALE: secondary_approval.present is older than 0:15:00"}
```

Exit code `1`. **In plain language:** the approval existed, but not recently enough to satisfy the rule. Stale evidence is not treated as current permission.

Note that **no receipt is issued on refusal** — a refused decision never produces evidence claiming a decision was made.

---

## Falsify it yourself

Reproducing a happy path proves very little. The useful question is whether this
system refuses when it should — and whether you can watch it do so.

```bash
python3 falsify.py
```

One command, no credentials, no network. It runs five cases against the
committed fixtures and checks each against a **declared expected disposition**:

| Case | Expected |
|---|---|
| Valid specimen | `PASS` / `OK` / exit 0, receipt issued |
| Undeclared action | `REFUSED` / `RUN_UNCLASSIFIED_ACTION` / exit 1, no receipt |
| Stale runtime fact | `REFUSED` / `RUN_FACT_STALE` / exit 1, no receipt |
| Untampered receipt | `PASS` / `OK` / exit 0 |
| Tampered receipt binding | `REFUSED` / `VEIP_RECEIPT_MISMATCH` / exit 1 |

A case fails if what happens differs from what was expected **in either
direction**. An unexpected refusal fails; so does an unexpected pass. The
harness exits non-zero on any mismatch, so it works as a check in your own CI.

If you find a mismatch, that is a real result. Please
[open an issue](https://github.com/veraxis-protocol/AuthContract/issues).

---

## What the result means

| Field | Meaning |
|---|---|
| `status` | `PASS` or `REFUSED` — the outcome of the check |
| `decision` | `ALLOW` on a permitted action; absent on refusal |
| `reason_code` | Machine-facing identifier (e.g. `RUN_FACT_STALE`). Branch on this rather than on prose — but see the note below on cross-version stability |
| `message` | Human-readable explanation of a refusal |
| `contract_digest` | Canonical identity (RFC 8785 JCS + SHA-256) of the rule that applied |
| `projection_digest` | Identity of the action domain the rule was projected into |
| `runtime_fact_set_digest` | Identity of the exact facts relied on |
| `exact_action_digest` | Identity of the exact action authorized |
| `admission_digest` | Identity of the admission state bound to the decision |
| `decision_time` | Bound to the fact bundle's declared `now`, **not** wall-clock — so replays are byte-identical |
| `receipt_digest` | Identity of the receipt as a whole |

Every digest is recomputable from raw inputs. That is what makes the receipt checkable by a third party rather than merely assertable by you.

Exit codes: `0` pass · `1` refusal.

**On `reason_code` stability.** Reason codes are the intended programmatic signal within the currently documented and tested interface, and are accurate for this commit. This repository does **not** yet establish a versioned public-interface commitment that they remain unchanged across future releases — no versioning or pinning mechanism exists. Re-check them if you upgrade, and do not treat them as a frozen API contract. `message` is human-readable and is not contractual at any version.

---

## How to integrate it today

Only interfaces that **actually exist** are listed. Each was executed while writing this section.

### CLI — available

```
authcontract verify           Verify one rule artifact's canonical identity
authcontract project          Project a rule into its declared runtime action domain
authcontract check-action     Check an action against a rule's declared domain
authcontract git-gate         Check a CI result against the version that would actually merge
authcontract run-specimen     Run the rule/fact/action check end to end; issue a receipt on PASS
authcontract verify-receipt   Re-run the evidence: recompute the receipt bindings and compare
```

Structured JSON on stdout, non-zero exit on refusal — so shell and CI integration is straightforward.

### Python library — available

```python
import json
from authcontract.veip import run_specimen, verify_receipt

artifact = json.load(open("fixtures/banking_payment_specimen.json"))
action   = json.load(open("fixtures/actions/send_payment_valid.json"))
facts    = json.load(open("fixtures/runtime/facts_valid.json"))

result = run_specimen(artifact, action, facts, execution_result="SIMULATED_SUCCESS")
print(result.decision, result.reason_code)        # ALLOW OK

if result.decision == "ALLOW":
    check = verify_receipt(result.receipt, artifact, action, facts)
    print(check.status, check.reason_code)        # PASS OK
```

`run_specimen` returns a `RunResult` (`decision`, `reason_code`, `message`, `receipt`) and does **not** raise on an ordinary refusal — refusals are return values, not exceptions.

### GitHub merge-gate workflow — available

The repository includes `.github/workflows/authcontract-gate.yml`, which runs `authcontract git-gate` on pull requests. It re-resolves the base ref live and proves the evaluated commit really contains both the base and the PR head, so a stale or isolated-head result cannot pass the gate's own check.

**The workflow's presence does not mean GitHub requires it.** Whether a check is *enforced* — that is, whether branch protection blocks a merge when it fails — is a separate GitHub repository-configuration concern, set in branch protection or rulesets rather than in the workflow file. Do not infer enforcement from the fact that this workflow exists; verify the repository's own branch-protection settings if you need to know what is actually required to merge.

### Runtime invocation and receipt verification — available

`run-specimen` and `verify-receipt`, via CLI or library, as shown above.

### Not available

- **No published package.** Not on PyPI; install from source.
- **No HTTP/gRPC service.** In-process library and CLI only.
- **No persistence layer.** Stateless over in-memory inputs; receipts are not stored for you.
- **No multi-contract registry.** One artifact is evaluated per invocation; there is no cross-contract selection.
- **No replay protection.** Replayed identical requests produce identical receipts — this is determinism, not protection. No nonce or single-use semantics exist.

---

## What is *not* implemented

Read this before forming expectations. The worked conceptual examples later in this document describe **target** behavior.

- **Automated natural-language source-to-rule comparison is not implemented end to end.** This is the product's defining target capability and does not exist yet. Rules are authored as `.ac` artifacts today.
- Not production-ready. Not audited. Not security-certified. Not regulatory-approved. No formal proof.
- No universal policy correctness, general legal correctness, or arbitrary-domain compatibility.
- No production-grade institutional identity or PKI.
- No concurrency, distribution, or measured multi-core scaling.
- Evidence scope is one synthetic banking specimen family — not a general solution.

Measured evidence and its limits: [`docs/BENCHMARKS-AC-039.md`](docs/BENCHMARKS-AC-039.md) (current; [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) is the superseded earlier baseline) · maturity assessment: [`docs/TRL-ASSESSMENT.md`](docs/TRL-ASSESSMENT.md).

---

## License

Licensed under the PolyForm Noncommercial License 1.0.0.
Noncommercial use, modification, testing, and distribution are permitted
subject to the license terms. Commercial use requires a separate written
license from Veraxis.

---

## Where to go next

| If you want to… | Go to |
|---|---|
| See measured performance and correctness evidence | [`docs/BENCHMARKS-AC-039.md`](docs/BENCHMARKS-AC-039.md) |
| See the earlier, superseded baseline | [`docs/BENCHMARKS.md`](docs/BENCHMARKS.md) |
| Reproduce the benchmarks yourself | [`benchmarks/README.md`](benchmarks/README.md) |
| Understand current maturity honestly | [`docs/TRL-ASSESSMENT.md`](docs/TRL-ASSESSMENT.md) |
| See what is planned and why | [`docs/ROADMAP.md`](docs/ROADMAP.md) |
| Validate a clean clone yourself | [`docs/CLEANROOM-VALIDATION-RUNBOOK.md`](docs/CLEANROOM-VALIDATION-RUNBOOK.md) |
| See how this repository was usability-tested | [`docs/REPOSITORY-USABILITY.md`](docs/REPOSITORY-USABILITY.md) |
| See the release-readiness verification record | [`docs/RELEASE-READINESS.md`](docs/RELEASE-READINESS.md) |
| Try to falsify it | run `python3 falsify.py` |
| Know what you can depend on across versions | [`docs/VERSIONING.md`](docs/VERSIONING.md) |
| Report a suspected vulnerability | [`SECURITY.md`](SECURITY.md) |
| Understand the contribution situation | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Understand the terminology | [`docs/DEVELOPER-LANGUAGE.md`](docs/DEVELOPER-LANGUAGE.md) |
| Review dependency and SBOM policy | [`DEPENDENCIES.md`](DEPENDENCIES.md) |
| Review security reporting | [`SECURITY.md`](SECURITY.md) |
| Review compatibility policy | [`VERSIONING.md`](VERSIONING.md) |
| See how this compares to other systems | [`docs/SOTA.md`](docs/SOTA.md) |
| Understand the full conceptual model | keep reading below |
| Use AuthContract from an AI coding agent | [`AGENTS.md`](AGENTS.md) |

---

## Getting help, reporting problems, and commercial use

| | |
|---|---|
| **Found a bug, or a claim that doesn't hold?** | Open a [GitHub issue](https://github.com/veraxis-protocol/AuthContract/issues). Reproduction steps against the committed fixtures are the most useful thing you can include. |
| **Benchmark didn't reproduce?** | Include your OS, Python version, and the `benchmarks/results/` JSON your run produced — the harness records the DUT and harness SHAs it verified. |
| **Commercial or institutional use** | [veraxis.io](https://veraxis.io) |

**Contributions.** There is no contribution process established yet, and no
contributor licence or review policy exists. Issues are the reliable path today.
If you are considering a substantive contribution, open an issue first so it
isn't wasted effort. [`CONTRIBUTING.md`](CONTRIBUTING.md) states exactly what
does and does not exist, including evidence, role-separation, and
agent-provenance expectations for an owner-agreed change.

**Security.** Do not report a suspected vulnerability through a public issue.
[`SECURITY.md`](SECURITY.md) sets out the triage policy and the current state of
the private reporting route.

**A note on scope of support.** This is an experimental reference implementation
maintained as research and engineering evidence. There is no support commitment,
response-time expectation, or maintenance guarantee attached to it.

If the clean-room run above was useful to you, a GitHub star helps other
engineers evaluating this space find it — entirely optional, and only if it
actually earned one.

---
---

# How it works — the full model

Everything above is runnable today. Everything below explains the model the implementation is built toward, including worked examples of the **target** source-to-rule comparison that is not yet implemented end to end.

---

## See it in a pull request

Suppose the source says:

```text
§4.2

Payments above $50,000 require secondary approval.
```

Your current rule is:

```yaml
secondary_approval:
  required_above: 50000
```

A pull request changes it:

```diff
 secondary_approval:
-  required_above: 50000
+  required_above: 100000
```

Ordinary CI may see perfectly valid YAML and perfectly valid application logic.

AuthContract sees a source-linked behavior change.

```text
FAIL

Rule changed behavior from its source.

Source
  §4.2

Source says
  Secondary approval is required above $50,000.

PR says
  Secondary approval is required above $100,000.

The new behavior is not supported by the referenced source.

Do not merge.
```

---

## It also catches invented rules

A developer adds:

```yaml
manual_review:
  required_when:
    customer_risk_score: "> 72"
```

But the referenced source never establishes `72`.

AuthContract should not infer that the threshold is probably reasonable.

It should say:

```text
FAIL

Source does not establish this condition.

Introduced rule
  customer_risk_score > 72

Referenced source
  §7.1

No supporting threshold was established in the referenced source.

The PR introduces executable behavior that cannot be justified
from the source.

Do not merge.
```

---

## And it does not turn uncertainty into permission

Sometimes the source is not clear enough to produce one defensible rule.

For example:

```text
Enhanced review may be required for unusually large transactions.
```

There is no threshold.

There may be no single machine-operational interpretation.

AuthContract does not silently choose one.

```text
UNRESOLVED

The source does not establish a machine-operational threshold.

Source
  §6.3

Open question
  What amount qualifies as "unusually large"?

No executable threshold should be merged until this is resolved.
```

`UNRESOLVED` is not a soft pass.

It means there is still a decision for the responsible people to make.

---

## The developer workflow

AuthContract is designed to fit where developers already work.

```text
git push
   ↓
pull request
   ↓
AuthContract check
   ↓
source ↔ rule ↔ behavior
   ↓
PASS / FAIL / UNRESOLVED
   ↓
merge or fix
```

The developer should not need to learn a new governance vocabulary to use it.

The working vocabulary is familiar:

**source → rule → diff → test → failure → CI → merge → ship**

---

## What PASS means

A green check should mean more than:

> The file parsed.

or:

> The tests passed.

For the bounded rule under evaluation, AuthContract is intended to establish that:

1. the rule is linked to an identified source;
2. the behavior represented by the rule is supported by that source;
3. unresolved meaning has not been silently converted into executable behavior;
4. the tested rule has a stable identity;
5. the version being merged is the version that was actually checked;
6. the runtime rule can be tied back to the rule that passed;
7. evidence can later reconstruct what governed the action.

A `PASS` is therefore evidence about a specific rule, source, version, and evaluation.

It is not a claim that every legal, regulatory, business, or operational question has been solved.

---

## From PR to runtime

Pre-merge proof is necessary, but it is not enough.

A developer can correctly ask:

> You proved the PR was supported by the source. How do I know the agent later acted under that same rule?

AuthContract is designed to keep that continuity intact.

```text
source
   ↓
source-backed rule
   ↓
pull request
   ↓
AuthContract check
   ↓
PASS
   ↓
exact merged version
   ↓
runtime rule
   ↓
agent action
   ↓
decision evidence
```

The rule your agent acts on should be the same rule that passed the source-linked check.

That lets you move from:

> This rule passed CI.

to:

> This action was governed by the exact source-backed rule that passed CI.

---

## After the action

The evidence should let someone reconstruct the decision without trusting a screenshot, a dashboard, or a developer's memory.

For a consequential action, the reconstruction should be able to answer questions such as:

```text
What source supported this rule?

What exact rule passed?

What version of the rule was active?

What commit contained it?

What runtime facts were relied on?

What action was requested?

Was the action inside the rule's declared boundary?

What decision was produced?

What happened afterward?
```

The goal is not simply to create logs.

The goal is to preserve the relationship:

```text
source → rule → version → runtime decision → action → evidence
```

---

## A successful check

A successful rule change should be equally easy to understand.

```text
PASS

Rule is supported by its source.

Source
  §4.2

Source says
  Secondary approval is required above $50,000.

Rule says
  Secondary approval is required above $50,000.

Behavior
  Matched

Rule identity
  Verified

Result
  Safe to continue through the configured merge workflow.
```

Machines can keep reason codes, digests, identifiers, and structured evidence.

Humans should not have to decode them just to understand what happened.

---

## AuthContract is not a policy engine

AuthContract does not replace OPA, Rego, Cedar, or another runtime policy system.

Those systems are good at evaluating rules.

AuthContract focuses on a different boundary.

A policy engine can answer:

> Given this rule and this input, what is the result?

AuthContract is intended to help answer:

> Why is this the rule?

> What source supports it?

> Did this PR change what the source means?

> Did anything unresolved get turned into executable behavior?

> Is the runtime using the same rule that passed?

> Can the resulting action be reconstructed afterward?

A runtime policy engine can therefore be a downstream execution target for an AuthContract-backed rule.

---

## A simple mental model

Think of AuthContract as a test suite for the relationship between a source and executable behavior.

Ordinary tests might check:

```text
input → code → expected output
```

AuthContract adds another relationship:

```text
source → rule → expected behavior
```

And for agentic systems, one more:

```text
verified rule → runtime action → evidence
```

---

## What is an `.ac` file?

An `.ac` artifact is the machine-readable object AuthContract uses to preserve the rule and the information required to verify it.

You should not need to understand its internal architecture to use AuthContract.

At a high level it carries things such as:

- the machine-operational rule;
- links back to its source;
- conditions and exceptions;
- declared action boundaries;
- unresolved material;
- version and activation information;
- approval/admission context;
- bindings used to test and reconstruct the rule.

The `.ac` artifact exists so that the meaning being reviewed does not disappear between a source document, a pull request, a runtime system, and later evidence.

---

---

## Example: action outside the rule

Suppose the contract supports:

```text
send_payment
```

with:

```text
currency = USD
amount <= configured domain
```

A caller attempts an undeclared action:

```json
{
  "action_type": "change_beneficiary",
  "parameters": {
    "account": "12345"
  }
}
```

AuthContract refuses it.

Developer-facing result:

```text
FAIL

This action is not covered by the rule.

Action
  change_beneficiary

The active rule does not declare this action.

Nothing outside the declared action set is allowed implicitly.
```

Machine-facing reason:

```text
RUN_UNCLASSIFIED_ACTION
```

---

## Example: rule conflict

If two active rules both appear to govern the same action and no explicit precedence or composition rule resolves them, AuthContract fails closed.

```text
FAIL

More than one active rule applies to this action.

AuthContract cannot determine which rule should govern the action
without inventing precedence.

Resolve the conflict before shipping.
```

Machine-facing reason:

```text
CONTRACT_SCOPE_CONFLICT
```

Load order, file name, timestamp, or "first match wins" should not silently decide institutional meaning.

---

## Example: runtime fact cannot be trusted

A rule may depend on a fact such as:

```text
secondary_approval.present == true
```

That condition is meaningless if the same agent being governed can simply assert:

```json
{
  "secondary_approval.present": true
}
```

AuthContract checks runtime facts before they are allowed to influence the decision.

A developer-facing refusal should look like:

```text
FAIL

This fact cannot be trusted from the configured source.

Fact
  secondary_approval.present

Expected
  independently established approval evidence

Observed
  assertion does not satisfy the configured evidence boundary

The action was not evaluated with this fact.
```

This is enforced through verified-assertion binding: the fact gate checks the caller's claim — the value, who asserted it, and when — against verifier-established context, not the claim alone. A claim that disagrees with the verifier-established context refuses, even if the verifier-established context alone would otherwise be admissible. The reference implementation binds and checks that supplied verifier context against the assertion; it does not itself establish how the underlying fact was verified in production outside that interface.

---

## GitHub pull-request checks

AuthContract includes a GitHub-oriented merge-result gate.

The important distinction is that a check should run against the composition that would actually merge—not only an isolated PR head.

A stale or unverifiable merge composition must not become green.

Developer-facing failure:

```text
FAIL

This check was not run against the version that would actually merge.

The target branch changed after this evaluation.

Re-run AuthContract against the current merge result.
```

Machine-facing reason:

```text
GIT_MERGE_RESULT_UNVERIFIED
```

The repository contains a GitHub Actions workflow named:

```text
AuthContract Gate
```

The gate implementation is tested.

Repository-level branch protection requiring that check is a separate GitHub configuration concern and should not be inferred merely because the workflow exists.

---

## PASS, FAIL, and UNRESOLVED

AuthContract deliberately distinguishes three developer-relevant states.

### PASS

The checked behavior is supported within the currently tested AuthContract boundary.

```text
PASS
```

### FAIL

A concrete condition was violated.

Examples:

```text
Rule differs from source.
Action is outside the declared domain.
Fact cannot be admitted.
Merge result cannot be verified.
Two active rules conflict.
```

```text
FAIL
```

### UNRESOLVED

The available source or decision context does not justify a single executable interpretation.

```text
UNRESOLVED
```

AuthContract must not convert `UNRESOLVED` into `PASS`.

---

## Why source links matter

A comment like this:

```python
# regulatory requirement
if amount > 50000:
    require_approval()
```

does not prove anything.

Neither does:

```yaml
source: "policy.pdf"
```

AuthContract is designed around stronger relationships between the rule and the material that supports it.

The useful question is not:

> Does the rule contain a source field?

It is:

> Can someone inspect the exact source material that supports this exact behavior?

That relationship needs to survive changes to the rule.

---

## Why diffs matter

A rule can remain syntactically valid while changing meaning.

```diff
- threshold: 50000
+ threshold: 100000
```

A normal code review sees a changed number.

AuthContract should be able to show the semantic consequence:

```text
Before
  approval required above $50,000

After
  approval required above $100,000

Source
  still requires approval above $50,000

Result
  FAIL
```

The useful unit of review is not merely the changed text.

It is the changed behavior relative to the source.

---

## Why runtime continuity matters

The rule that passed cannot become detached from the rule that executes.

Otherwise:

```text
source-linked rule A
       ↓
PASS
       ↓
something changes
       ↓
runtime rule B
       ↓
action
```

and the original proof says nothing about the action.

AuthContract is designed to preserve the bindings required to detect that break.

```text
source-backed rule
       ↓
stable identity
       ↓
tested version
       ↓
runtime projection
       ↓
action check
       ↓
decision evidence
```

---

## Why evidence matters

Logs usually tell you what a system says happened.

AuthContract's evidence model is intended to let an independent verifier recompute the important relationships.

For example:

```text
Was this the same contract?

Was this the active version?

Was this the same runtime projection?

Were these the facts used?

Was this the exact action evaluated?

Was the resulting decision preserved?

Did the recorded execution result belong to that decision?
```

The standard is not:

> Trust the AuthContract service.

The direction is:

> Re-run the evidence.

---

## What developers should see

AuthContract's internal implementation contains concepts required for rigorous verification.

Those concepts should not dominate the normal developer experience.

Developers should primarily see:

```text
rule
source
diff
test
check
failure
commit
merge
runtime
proof
```

Not an ontology lesson.

Internal architecture belongs in the deeper documentation.

---

## What happens underneath

AuthContract's developer-facing workflow is backed by several distinct technical responsibilities.

At a high level:

```text
source
  ↓
machine-operational rule
  ↓
rule verification
  ↓
approval / activation
  ↓
Git merge-result check
  ↓
runtime projection
  ↓
runtime fact checks
  ↓
action decision
  ↓
reconstructable evidence
```

The Veraxis research stack uses components including OIC, ZTL, OAM, VEIP, and AEP to reason about parts of this chain.

You do not need to understand those components to use the developer workflow.

Their job is to make the simple developer-facing claims harder to fake.

---

## Design rule

AuthContract follows one important principle:

> **Do not silently invent meaning.**

That applies throughout the system.

If the source does not establish something, do not manufacture it.

If two rules conflict, do not invent precedence.

If a fact cannot be trusted, do not treat it as true.

If the merge result cannot be verified, do not pretend the PR passed.

If runtime cannot be tied back to the rule that passed, do not claim continuity.

Fail closed.

Make the missing information visible.

Let a human resolve what requires human judgment.

---

## Current status

AuthContract is an experimental reference implementation under active development.

The current repository demonstrates and tests bounded pieces of the intended chain, including:

- canonical contract identity and digest behavior;
- separation of immutable rule meaning from sibling state;
- deterministic projection into a declared action domain;
- closed action classification;
- fail-closed domain handling;
- active/inactive rule behavior;
- overlapping-rule conflict detection;
- Git merge-result admissibility;
- runtime fact admissibility bound to verifier-established assertion context — the fact gate checks a caller's claim (value, asserter, timing) against verifier-established evidence, not the claim alone;
- a bounded runtime decision and AEP-style evidence-reconstruction path — verify the artifact, project it, admit its runtime facts, check the action, and issue a receipt on PASS — tested and accepted for one synthetic banking specimen;
- closed, fail-closed input shapes for runtime facts, rule declarations, and the receipt's admission binding.

**What this means today.** The worked examples earlier in this document — the §4.2 threshold change, the invented-rule check, the UNRESOLVED ambiguity case — describe AuthContract's target developer experience: automatically comparing a rule's behavior against its natural-language source. The current implementation exercises the mechanical trust chain beneath that experience (the pieces listed above) for one synthetic specimen. Automated natural-language source-to-rule comparison, as shown in those examples, is the product's target capability and is not yet implemented end to end.

The project does **not** currently claim:

- production readiness;
- universal policy correctness;
- general legal correctness;
- automatic interpretation of arbitrary source documents, or automated natural-language source-to-rule comparison;
- production-grade institutional identity or PKI;
- universal runtime integration;
- broad professional usability;
- market adoption.

Current results are bounded to the implemented and tested specimens.

---

## Current specimen

The primary development specimen is a synthetic banking payment workflow.

It is intentionally narrow.

That makes it possible to test the complete relationship among:

```text
source-backed rule
→ activation
→ pull request
→ projection
→ runtime facts
→ payment action
→ decision
→ evidence
```

without claiming a general solution before the implementation has earned one.

---

## Repository layout

```text
authcontract/
    digest.py
    facts.py
    projection.py
    git_gate.py
    veip.py
    cli.py
    ...

fixtures/
    actions/
    runtime/
    ...

tests/
    ...

docs/
    DEVELOPER-LANGUAGE.md

.github/workflows/
    ci.yml
    authcontract-gate.yml
```

Developer-facing examples and commands belong near the top of the repository.

Detailed architecture, assurance records, formal invariants, design decisions, and adversarial findings belong in deeper reference documentation.

---

## For policy-engine users

If you already use OPA/Rego, Cedar, or another policy engine, AuthContract is not asking you to replace it.

A useful division of responsibilities is:

```text
AuthContract
  Why is this the rule?
  What source supports it?
  Did the PR change its meaning?
  Is the rule's runtime boundary intact?
  Can the action be traced back to what passed?

Policy engine
  Given this rule and this input, what is the decision?
```

AuthContract can sit upstream of, around, or alongside a policy engine.

The policy engine evaluates.

AuthContract preserves and verifies the chain that makes the evaluated rule defensible.

---

## The test we care about

The decisive developer test is simple.

Take a repository containing:

1. a rule;
2. the source that supports it.

Open a pull request.

Change the rule so that it subtly departs from the source.

AuthContract should catch the change in the PR and explain it in language the developer can act on.

```text
FAIL

Rule changed behavior from its source.

Source
  approval required above $50,000

PR
  approval required above $100,000

Do not merge.
```

Then fix the rule.

```text
PASS

Rule is supported by its source.
```

Then ship it.

At runtime, the system should be able to prove that the consequential action was governed by the rule that passed.

That is the product.

---

## One sentence

**AuthContract gives you proof that the rule you shipped is actually supported by the source.**
