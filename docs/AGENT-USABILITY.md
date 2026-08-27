# Agent usability test record (AC-037)

Clean-room test of this repository from the perspective of an AI coding /
operations agent, using **only** repository files: `README.md`, `AGENTS.md`, and
the executable interfaces. No hidden coaching, no undocumented commands.

**This document records observations. It does not certify CURRENT-SDLC Gate F** —
that adjudication belongs to the Engineering Lead.

## Test conditions

| | |
|---|---|
| Method | Fresh `git clone` into an empty directory, checkout of the candidate commit |
| Candidate commit | `7e7f28d6d8ba8d94cd42d8f3ff4989bf637068d6` |
| Environment | Linux x86_64, Python 3.11.15, git 2.43.0 |
| Instructions used | `AGENTS.md` and `README.md` only |
| Prior knowledge assumed | None |

Every command below was executed. Results are pasted from real output.

---

## Criterion matrix

| # | Criterion | Result | Evidence |
|---|---|---|---|
| A | Determine what AuthContract currently does | **PASS** | `AGENTS.md` §1 states the implemented chain in seven steps; §2 states TRL 4 and that automated natural-language source-to-rule comparison is **not** implemented end to end. |
| B | Install it | **PASS** | `AGENTS.md` §4 commands ran verbatim. `pytest -q` → **342 passed**. |
| C | Execute the successful E2E path | **PASS** | §6 command → `status PASS`, `decision ALLOW`, `reason_code OK`, receipt with **10** bound fields, **exit 0**. |
| D | Intentionally produce REFUSED | **PASS** | §7 command 1 → `REFUSED` / `RUN_UNCLASSIFIED_ACTION`, exit 1. Command 2 → `REFUSED` / `RUN_FACT_STALE`, exit 1. Both confirmed `receipt` absent, matching the documented "no receipt is issued on refusal". |
| E | Verify a receipt | **PASS** | §8 command on the committed fixture → `PASS` / `OK`, exit 0. The documented extraction step also verified: extracting `.receipt` from the wrapper → `PASS` / `OK`. |
| F | Interpret PASS/REFUSED and `reason_code` | **PASS** | §9 exit-code table and §10 reason-code families match observed output. Codes in §10 were extracted from source, not recalled. |
| G | Invoke it from Python | **PASS** | §11 example run verbatim → `decision ALLOW reason OK`, then `status PASS OK`. The documented "refusals are return values, not exceptions" claim was tested directly: a stale-fact run returned `REFUSED` / `RUN_FACT_STALE` with **no exception raised**. |
| H | Determine which interfaces do NOT exist | **PASS** | §13 claims tested rather than assumed: `authcontract.server`, `.api`, `.http`, `.registry`, `.db` all raise `ModuleNotFoundError`. `authcontract --help` lists exactly the six documented subcommands and no others. |
| I | Recognize that workflow presence ≠ enforced branch protection | **PASS** | §12 states the distinction explicitly and instructs the agent not to report the gate as enforced. Independently corroborated: `authcontract-gate.yml` is `on: pull_request` only. |
| J | Recognize the claim ceiling | **PASS** | §14 states the ceiling and instructs against softening it. §15 states the PolyForm Noncommercial terms and instructs against describing the project as open source or implying commercial-use rights. |

**Totals: 10 PASS · 0 FAIL · 0 NOT EVALUATED.**

---

## Verified negative behavior

A usability claim is only worth as much as its failure modes, so these were
executed rather than asserted:

- **Wrapper passed to `verify-receipt`.** `AGENTS.md` §8 warns that passing
  `run-specimen`'s full JSON wrapper instead of the extracted receipt object
  returns `VEIP_RECEIPT_MALFORMED`. Confirmed exactly:
  `VEIP_RECEIPT_MALFORMED: receipt missing required field(s): ['activation_id', 'admission_digest', 'contract_digest', 'decision_time', 'exact_action_digest', 'execution_result', 'projection_digest', 'receipt_digest', 'runtime_fact_set_digest']`, exit 1.
  This is the same defect the AC-028 clean-room run originally uncovered; it is
  now documented before an agent can hit it.
- **No receipt on refusal.** Both refusal paths were checked for a `receipt`
  key. Absent in both.
- **Unsupported modules.** Five plausible module names an agent might guess were
  imported and all failed, confirming §13 rather than trusting it.

---

## Observations and limitations

1. **`AGENTS.md` is the only agent surface.** No prior `AGENTS.md`,
   `CONTRIBUTING.md`, skill file, or machine-readable usage guidance existed, so
   this is additive rather than duplicative. A separate reusable skill file was
   **deliberately not added** — see the decision note below.

2. **The reason-code list is descriptive, not a stability contract.** §10 lists
   codes extracted from the implementation at this commit. Nothing in the
   repository pins them as a versioned public interface, so an agent should
   branch on them but should not assume they are frozen across versions. This is
   a gap in the repository, not in `AGENTS.md`.

3. **Refusal semantics are the most likely agent failure mode.** An agent
   optimizing for a successful exit code could plausibly retry a refusal with
   altered inputs until it gets `ALLOW`. `AGENTS.md` §7 and §16 explicitly
   prohibit this, but the prohibition is instructional — nothing mechanically
   prevents it.

4. **Not tested: an actual third-party agent.** This record was produced by the
   same executor that wrote `AGENTS.md`. That is a real limitation on its
   evidentiary weight — it demonstrates the instructions are *accurate and
   executable*, not that an independent agent *would* follow them. Independent
   agent reproduction remains absent, consistent with the TRL 4 assessment in
   [`docs/TRL-ASSESSMENT.md`](TRL-ASSESSMENT.md).

---

## Decision: no separate skill file

AC-037 Phase 2 permits an optional reusable agent skill. **One was not added.**

`AGENTS.md` already carries the full install → run → refuse → verify → interpret
sequence with real commands and real outputs. A separate skill file would either
duplicate it — creating two surfaces that can drift apart, which is precisely the
class of defect AC-036S corrected in `README.md` — or would have to invent
tool-specific automation scaffolding that does not exist in this repository.

Recorded explicitly so the omission is understood as a decision rather than an
oversight.

---

## Claim ceiling

This record establishes only that the documented agent-facing instructions are
accurate and executable at this commit, for one synthetic banking specimen
family, on one machine. It establishes no production readiness, no regulatory or
legal correctness, no arbitrary-domain compatibility, no security certification,
and no independent validation.
