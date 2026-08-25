# Versioning and public interface policy (AC-039)

What a downstream user or agent may depend on, and what may change without
warning. Written so nobody has to infer stability from silence.

---

## Current version status

| | |
|---|---|
| Package version | `0.0.1` (`pyproject.toml`) |
| Status | **pre-1.0, experimental** |
| Maturity | TRL 4 — see [`docs/TRL-ASSESSMENT.md`](TRL-ASSESSMENT.md) |
| Released versions | **None.** No tag, no GitHub Release, no published package. |
| Supported version | `main` only — see [`SECURITY.md`](../SECURITY.md) §2 |

**`0.0.1` is not a release number.** It is a placeholder that has never been
published anywhere, and it has not been incremented as the implementation
changed. Two checkouts both reporting `0.0.1` may differ substantially. **The
commit SHA, not the version string, is the only reliable identity for this
project today.** Pin a commit if you depend on behaviour.

**Semantic Versioning is not claimed.** This project does not currently
implement SemVer: version numbers are not bumped per change, so they carry none
of the guarantees SemVer attaches to major/minor/patch. Do not treat the version
string as a compatibility signal. Adopting SemVer is a 1.0 question, recorded
below, not a present-tense claim.

---

## Declared public interface surface

These are the surfaces this repository documents and tests, and therefore the
only ones a downstream consumer should build against. Anything not listed here
is internal, regardless of whether Python's import system will let you reach it.

### 1. CLI commands — six, exactly

```
authcontract verify           <artifact>
authcontract project          <artifact>
authcontract check-action     <artifact> <action>
authcontract git-gate         <context> [--repo REPO]
authcontract run-specimen     <artifact> <action> <facts> --execution-result <R>
authcontract verify-receipt   <receipt> <artifact> <action> <facts>
```

### 2. CLI flags intended for consumers

| Flag | Command | Accepted values |
|---|---|---|
| `--execution-result` | `run-specimen` | `NOT_EXECUTED`, `SIMULATED_SUCCESS`, `SIMULATED_FAILURE` |
| `--repo` | `git-gate` | path to the Git repository to verify merge composition against |

### 3. Output and exit semantics

- Every command emits **single-line JSON on stdout**.
- Exit `0` = PASS / ALLOW. Exit `1` = REFUSED, or an error condition.
- Branch on the JSON `status` and `reason_code`. `message` is human-readable
  prose and is **not** contractual at any version — do not parse it.

### 4. Python entry points

| Module | Public names |
|---|---|
| `authcontract.veip` | `run_specimen`, `verify_receipt` |
| `authcontract.digest` | `contract_digest`, `verify_artifact`, `canonical_bytes` |
| `authcontract.projection` | `project`, `check_action`, `projection_digest` |

`run_specimen` returns a `RunResult` (`decision`, `reason_code`, `message`,
`receipt`); `verify_receipt` returns a `VerifyResult` (`status`, `reason_code`,
`message`). **Refusals are return values, not exceptions.**

### 5. Receipt fields

Ten bound fields, issued on ALLOW only: `activation_id`, `contract_digest`,
`projection_digest`, `runtime_fact_set_digest`, `exact_action_digest`,
`admission_digest`, `decision`, `execution_result`, `decision_time`,
`receipt_digest`.

### 6. Reason codes

The machine-facing identifiers listed in [`AGENTS.md`](../AGENTS.md) §10. See
the policy below — they are the intended programmatic signal, with an explicitly
bounded stability commitment.

### 7. File-format surfaces

The `.ac` / JSON artifact, action, and runtime-fact shapes consumed by the
commands above, as exercised by the committed fixtures in `fixtures/`. There is
no published schema document; the fixtures and the tests are the specification.

### 8. Workflow-facing surface

`authcontract git-gate` and the context JSON it consumes
(`.github/workflows/authcontract-gate.yml` shows the exact shape). The presence
of that workflow does **not** mean GitHub requires it — enforcement is branch
protection, which is separate repository configuration.

### Not public

Everything else, including `authcontract.facts`, `authcontract.git_gate`
internals, `authcontract.cli` internals, module-private helpers, exception
class hierarchies, benchmark harness code, and the exact wording of any
`message`.

---

## Change policy before 1.0

**Pre-1.0 interfaces may change, including in breaking ways, without a major
version bump.** That is what pre-1.0 means here, stated plainly rather than
left to be discovered.

What this project *does* commit to before 1.0:

1. **Reason codes will not change meaning silently under the same version.**
   If a reason code is removed, renamed, or has its semantics changed, that
   change is recorded in the commit message and in `AGENTS.md` §10. A code
   never quietly starts meaning something else. This is the strongest interface
   commitment in the project, and it is deliberately scoped to *not silently* —
   it is not a promise that codes never change.

2. **A breaking change to any declared surface above carries a release note.**
   Concretely: the commit that makes it says what broke and what to do instead.
   With no releases to attach notes to, the commit message is the release note.

3. **The claim ceiling is never weakened to accommodate a change.** If an
   interface change would make a documented limitation untrue in the
   *optimistic* direction, the limitation is re-verified, not deleted.

What this project explicitly does **not** commit to before 1.0:

- No cross-version stability guarantee of any kind beyond point 1 above. There
  is no versioning or pinning mechanism that would make such a guarantee
  checkable, and a guarantee nobody can check is not a guarantee.
- No deprecation period. A pre-1.0 interface may be removed in the same commit
  that replaces it.
- No backports. Fixes land on `main` only.

---

## What 1.0 would require

Recorded so "pre-1.0" is a stage with an exit condition rather than an
indefinite disclaimer. All of these are absent today:

- An explicit versioning scheme actually implemented and applied per change —
  SemVer or a documented alternative.
- Tags and releases, so a version string identifies a specific artifact.
- A stated deprecation policy with a real notice period.
- A license, so downstream use is legally possible at all
  ([`README.md`](../README.md) § License).
- The maturity conditions in [`docs/TRL-ASSESSMENT.md`](TRL-ASSESSMENT.md),
  including independent external reproduction.

Until then: **pin the commit SHA.**
