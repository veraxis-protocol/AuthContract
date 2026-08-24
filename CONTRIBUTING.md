# Contributing

## Current status: no unsolicited contribution workflow is established

This is stated plainly rather than left ambiguous, because an unstated process
wastes a contributor's time.

There is **no** established process for unsolicited pull requests. Specifically,
none of the following exists: a contributor licence agreement, a review-time
commitment, a maintainer rota, a triage service level, a governance model, a
code of conduct process, or a merge policy for outside contributions.

Nothing here promises any of those will exist. This is an experimental
reference implementation maintained as research and engineering evidence, not a
community-maintained project.

**Contribution is also constrained by licensing.** No license is declared (see
[`README.md`](README.md) § License), so the terms under which a contribution
could be accepted and redistributed are themselves unsettled. That is an owner
decision, not a process gap someone can work around.

## What is genuinely useful right now

**Open an issue.** Issues are read, and they are the reliable path.

The most valuable thing you can send is a **falsification**: a case where
AuthContract's documented behaviour and its actual behaviour disagree.

- Run `python3 falsify.py` — the public falsification harness — and include its
  output if a case failed.
- Include your OS, Python version, and the exact commit SHA.
- Reproduce against the committed fixtures in `fixtures/` where possible. No
  credentials or network are needed.
- If a claim in `README.md`, `AGENTS.md`, or any document under `docs/` does not
  hold, say which sentence and what you observed instead. A documented claim
  that turns out to be false is a defect, and it is recorded rather than quietly
  edited away.

For a **suspected security vulnerability**, do not open a public issue — follow
[`SECURITY.md`](SECURITY.md) instead.

## Before writing code

**Open an issue first.** A pull request that arrives without prior discussion
may sit unreviewed, and given the licensing situation above it may not be
mergeable at all. That is a genuine risk of wasted effort, so it is said up
front rather than discovered afterwards.

If a change is agreed, the practical expectations are the same ones this
repository applies to itself:

- The full suite passes: `pytest -q` → 342 passed.
- The falsification harness passes: `python3 falsify.py`.
- A fix comes with a regression test that **fails without the fix**.
- Tests are not weakened, skipped, or deleted to make CI green.
- No claim is added that the repository's own measurements do not support.
