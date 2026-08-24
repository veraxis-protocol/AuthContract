# Release readiness record (AC-038)

Adjudication input for the CURRENT-SDLC public-release lifecycle. **This
document records verification results. It does not certify release, and it does
not declare the repository production-ready** — that adjudication is not the
executor's to make.

| | |
|---|---|
| Candidate commit (`main`) | `db1c745686285b229361d83f663dac2b5e8924a5` |
| Tree | `b6fa47bb8f955ed2edde3c95daea8689d9ea5d0e` |
| Method | Two independent fresh clones of `main`, plus GitHub API state |
| Environment | Linux x86_64, Python 3.11, git 2.43.0 |
| Maturity assessed elsewhere | TRL 4 — [`docs/TRL-ASSESSMENT.md`](TRL-ASSESSMENT.md) |

Every result below was executed. Nothing is inferred from an earlier commit,
from a branch head, or from documentation about the repository.

---

## Gate results

| Gate | Subject | Result | Basis |
|---|---|---|---|
| A | Engineering correctness | **VERIFIED** | `pytest -q` → 342 passed. E2E → `PASS` / `ALLOW` / `OK`, receipt with 10 bound fields, exit 0. Undeclared action → `REFUSED` / `RUN_UNCLASSIFIED_ACTION`, exit 1, `receipt` absent. Stale fact → `REFUSED` / `RUN_FACT_STALE`, exit 1, `receipt` absent. `verify-receipt` → `PASS` / `OK`, exit 0. |
| B | Evidence sufficiency | **VERIFIED** | DUT `e4e1a975`, harness `a7f6ba37`, `dut_verification.verified: true`. E2E 7/7 (0 failed). Adversarial 38/38 (0 failed, 0 not evaluated). Observed sustained E2E throughput min 1512.9 / median 1574.4 / max 1587.5 ops/sec. Determinism `true`. Claim ceiling 10 clauses. |
| C | Independent-adjudication boundary | **VERIFIED** | No self-certification string found in the repository. `docs/REPOSITORY-USABILITY.md:11` and `docs/AGENT-USABILITY.md:8` each state explicitly that adjudication does not belong to the document's author. |
| D | Git integrity | **VERIFIED** | Candidate merged via PR with exact-head green checks (below). Resulting `main` re-verified after merge; zero worktree drift against the merge commit. |
| E | Human usability from a fresh clone | **VERIFIED** | Fresh clone of `main`: install 10 s, `pytest -q` → 342 passed, **first meaningful success at 21 s** against a 5-minute budget. Refusal and receipt-verification paths reproduced. README truthfulness surfaces present. |
| F | Agent usability, independently re-executed | **VERIFIED** | Separate fresh clone; `docs/AGENT-USABILITY.md` deliberately **not** relied on. Details below. |
| G | Adoption readiness | **VERIFIED** | Issues enabled and documented as the reporting path; benchmark-reproduction reporting path documented; commercial path documented; contribution status stated honestly as *not yet established*; licence status stated honestly as *not declared*. |

### Gate F — what was independently re-executed

Executed in a fresh clone of `db1c745`, following `AGENTS.md` and `README.md`
only:

- **CLI surface.** `authcontract --help` lists exactly
  `{verify, project, check-action, git-gate, run-specimen, verify-receipt}` —
  six subcommands, matching `AGENTS.md` §5, with no undocumented extras.
- **Successful path.** `PASS` / `ALLOW` / `OK`, exit 0.
- **Refusal path.** `REFUSED` / `RUN_UNCLASSIFIED_ACTION`, exit 1.
- **Receipt verification** via the documented extraction step → `PASS` / `OK`.
- **Unsupported interfaces (§13) tested, not assumed.** `authcontract.server`,
  `.api`, `.http`, `.registry`, `.db` each raised `ModuleNotFoundError`.
- **Documented negative behaviour.** Passing the `run-specimen` wrapper to
  `verify-receipt` returned `VEIP_RECEIPT_MALFORMED` naming all nine missing
  fields, exit 1 — exactly as `AGENTS.md` §8 warns.
- **Refusals are return values.** A stale-fact `run_specimen()` call returned
  `decision=REFUSED`, `reason_code=RUN_FACT_STALE`, `receipt=None`, with **no
  exception raised**, confirming §11.
- **Workflow ≠ enforcement.** `authcontract-gate.yml` is `on: pull_request`
  only. `AGENTS.md` §12, `README.md:218` and `README.md:817` each state that
  the workflow's presence does not establish that GitHub requires it.
- **Licensing boundary.** No `LICENSE` file; no licence field in
  `pyproject.toml`. `AGENTS.md` §15 and `README.md:249` state this and instruct
  against describing the project as open source.
- **Claim ceiling.** `AGENTS.md` §14 states the ceiling and forbids softening
  it; §16 forbids inventing commands, flags, endpoints, or maturity claims.
- **Reason-code semantics.** `AGENTS.md` §10 and `README.md:173` now describe
  reason codes as the intended programmatic signal **within the currently
  documented and tested interface**, and state explicitly that no versioned
  cross-version stability commitment exists. No unestablished stability claim
  remains.

---

## Release and supply integrity

| Check | State |
|---|---|
| Git tags | **None.** No tag exists in the repository. |
| GitHub releases | **None.** No release, draft or published. |
| Package publication | **Not published.** Not on PyPI; source install only, stated in `README.md` and `AGENTS.md` §4. |
| Signed release artifacts / provenance attestation | **NOT APPLICABLE** — no release artifact is produced or distributed. |
| Release-artifact checksums | **NOT APPLICABLE** — same reason. |
| Tracked-file secret scan | **Clean.** 82 tracked files scanned for key/token/password/private-key patterns; no match. The only matches in the working tree were inside an untracked local `.venv`. |
| Runtime dependencies | One: `rfc8785>=0.1.2`. Test extra: `pytest>=7.0`. |
| CI actions | `actions/checkout@v4`, `actions/setup-python@v5` in both workflows. |
| Workflow secrets usage | None. Neither workflow references `secrets.*`. |
| Branch protection / rulesets | **NOT VERIFIED — no read access.** This session has no branch-protection read endpoint. No claim about what is required to merge is made anywhere in the repository, which is the correct posture given this limitation. |

---

## Findings and disposition

### Closed in this cycle

**U6 — the README described the merge-gate workflow as a required status
check.** Enforcement is branch-protection configuration, not workflow content,
and could not be independently verified from this session. **CLOSED.** The claim
was removed; `README.md:218`, `README.md:817` and `AGENTS.md` §12 now state the
distinction explicitly and instruct readers not to infer enforcement from the
workflow's existence.

**U7 — reason codes were described as a "stable machine-facing identifier".**
No versioning or pinning mechanism exists in the repository, so cross-version
stability was unestablished. **CLOSED.** Corrected narrowly in both
`AGENTS.md` §10 and `README.md` (table row at line 159, note at line 173):
reason codes remain the recommended programmatic signal, now bounded to this
commit's documented and tested interface, with the absence of a versioned
commitment stated plainly.

### Open, with disposition

**U1 — no licence is declared.** Default copyright applies and no usage rights
are granted. **OPEN — owner decision.** Choosing a licence has legal effect and
is not an executor decision. Stated truthfully in `README.md` and `AGENTS.md`
§15 rather than left for a reader to discover. This is the single largest
adoption barrier in the repository.

**U5 — the benchmark DUT guard treats `README.md` as a protected surface, so
documentation-only changes trip it.** **OPEN — deliberately not worked around.**
The guard is behaving correctly: it refuses to publish results claiming to
describe a commit whose declared device-under-test paths differ. Splitting
`DUT_PATHS` into behavioural and documentary sets would report documentation
drift without blocking; that is a benchmark-design change and was not made here
to obtain a green run.

**U8 — `docs/AGENT-USABILITY.md` was authored by the same executor that wrote
`AGENTS.md`.** **OPEN — inherent, and disclosed in the document itself.** Gate F
above reduces but does not remove this: the re-execution was independent of the
*document*, not of the *author*. Independent agent reproduction by a third party
remains absent, consistent with the "externally validated: NO" row in
[`docs/TRL-ASSESSMENT.md`](TRL-ASSESSMENT.md).

### New in this cycle

**U9 — internal governance vocabulary appears in public documentation.**
`docs/DEVELOPER-LANGUAGE.md`, `docs/REPOSITORY-USABILITY.md`,
`docs/AGENT-USABILITY.md` and `docs/SOTA-EVIDENCE.md` reference
`CURRENT-SDLC`, "Engineering Lead", and `WORK-ORDER-AC-021` by name. No
work-order body, specification, or derivation machinery is exposed — only the
process vocabulary and identifiers. **OPEN — recorded, not unilaterally
remediated.** Some of these strings sit inside accepted, guard-pinned
documentation-language text, and rewording them is a boundary decision rather
than an executor correction.

**U10 — no `SECURITY.md`, `CONTRIBUTING.md`, or `CODE_OF_CONDUCT.md`.**
**OPEN.** The absence is currently consistent with the repository's stated
posture — `README.md` says plainly that no contribution process exists yet and
that there is no support commitment — so nothing is *overclaimed*. A
vulnerability-reporting path in particular is worth adding before wider
distribution.

**U11 — neither workflow declares an explicit `permissions:` block.** Both
therefore inherit the repository's default `GITHUB_TOKEN` permissions rather
than a least-privilege grant. **OPEN.** Neither workflow uses `secrets.*` or
writes to the repository, so `permissions: contents: read` would be sufficient.
Not changed here: modifying workflow permissions is repository configuration and
was not within this work order's authorization.

**U12 — GitHub Actions are pinned to mutable major tags** (`@v4`, `@v5`) rather
than immutable commit SHAs. **OPEN.** A tag can be repointed by its publisher,
so the executed action content is not pinned by the repository. Low severity
given no secrets are exposed to these workflows, but it is a supply-chain
surface and worth recording rather than assuming.

**U13 — dependency versions are floors, not pins, and no lockfile exists.**
`rfc8785>=0.1.2` and `pytest>=7.0` permit different resolved versions between
installs. **OPEN.** This is in direct tension with roadmap item X4
(cross-environment determinism): canonical identity that depends on an
unpinned canonicalization library is not yet demonstrably reproducible across
installs. Recorded as a finding rather than repaired, because pinning changes
`pyproject.toml`, which is a protected DUT path, and would invalidate the
benchmark's device-under-test verification without a fresh measurement run.

---

## What this record does not establish

Bounded to one synthetic banking specimen family, on one machine, one operating
system and one Python version. It does not establish production readiness,
regulatory or legal correctness, universal source-to-rule derivation,
arbitrary-domain compatibility, security certification, distributed
scalability, formal correctness, independent external validation, or comparative
standing against any other system.
