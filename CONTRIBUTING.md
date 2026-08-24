# Contributing

AuthContract is an experimental evidence repository with no general acceptance
promise. Start with a GitHub issue describing the bounded problem, the exact
commit SHA, and a reproducer against synthetic fixtures. This is the reliable
path for bugs, claim corrections, and proposed changes.

For a code contribution:

1. agree scope with the owner before substantial work;
2. create a focused branch and pull request—never push directly to `main`;
3. run `make ci` and include the literal output and commit SHA;
4. state the producer and proposed independent verifier;
5. label claims as proved, measured, argued, or assumed; and
6. state `NOT SELF-ADJUDICATED` in the pull request.

AI-assisted contributions should add these trailers when applicable:

```text
Agent-Assisted-By: <system and model>
Veraxis-Skill: <skill or workflow name>
Agent-Execution-ID: <optional attributable execution identifier>
```

Trailers are supplemental provenance. They do not establish authorship,
authority, independent verification, or acceptance. Security reports follow
`SECURITY.md`, not the public issue path.

No contributor licence agreement or licence grant is established by this file.

