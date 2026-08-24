# Agent observability and provenance

AuthContract has no telemetry client, analytics endpoint, hosted agent gateway,
or MCP server. Local reads and reasoning are dark unless a contributor records
them; this repository must not imply otherwise.

## Observable events

GitHub can attribute commits, pull requests, reviews, comments, checks, and
workflow runs to the authenticated GitHub actor. Those events establish
transport attribution only. They do not prove that an actor held institutional
authority, that a model performed the work claimed, or that a review was
independent.

Contributors may add commit trailers:

```text
Agent-Assisted-By: <system and model>
Veraxis-Skill: <skill or workflow name>
Agent-Execution-ID: <optional attributable execution identifier>
```

Trailers are supplemental provenance, not authorization or adjudication.
Producer, verifier, and adjudicator must remain distinct.

## Dark local activity

File reads, prompts, local model reasoning, and commands outside an attributable
system are not observable from Git history. Do not reconstruct or claim those
events without literal evidence. A missing trailer does not prove that no agent
was used; a trailer does not prove the described execution occurred.

## No outbound analytics

Run `make no-network` to install the local project without an index and exercise
package import, the full tests, and a CLI command with Python socket connections
blocked. A PASS is bounded to the exercised Python processes at the tested
commit. It does not inspect operating-system traffic from unrelated tools or
prove facts about a future binary.

## Unimplemented remote surfaces

A hosted AuthContract verifier, Veraxis gateway, remote context service, and MCP
server are **NOT IMPLEMENTED** in this repository. No URL, execution identifier,
or remote-observability claim should be invented for them.

