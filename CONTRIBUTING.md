# Contributing

## Current status: no unsolicited contribution workflow is established

There is no established process for unsolicited pull requests, contributor
licence agreement, review-time commitment, maintainer rota, governance model,
or merge policy for outside contributions. AuthContract is experimental
research and engineering evidence, not a community-maintained project. No
license is declared, so contribution acceptance and redistribution terms are
also unsettled owner decisions.

## What is genuinely useful right now

Open an issue first. Include the exact commit SHA, OS, Python version, and a
minimal reproducer against the committed synthetic fixtures. Falsifications of
documented behaviour are especially useful:

- `make ci` runs the full producer verification surface;
- `make falsify` exercises the bounded Wave 1 harness; and
- `python3 falsify.py` exercises the AC-039 public harness.

For suspected vulnerabilities, do not open a public issue; follow
[`SECURITY.md`](SECURITY.md).

If a code change is agreed, create a focused pull request rather than pushing
to `main`, include a regression test, preserve negative tests, report literal
command output at the exact commit, identify producer and proposed independent
verifier, classify claims as proved, measured, argued, or assumed, and state
`NOT SELF-ADJUDICATED`.

AI-assisted contributions should add these trailers when applicable:

```text
Agent-Assisted-By: <system and model>
Veraxis-Skill: <skill or workflow name>
Agent-Execution-ID: <optional attributable execution identifier>
```

Trailers are supplemental provenance. They do not establish authorship,
authority, independent verification, acceptance, or a licence grant.
