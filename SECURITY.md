# Security policy

AuthContract is an experimental, pre-1.0 reference implementation. It is not a
production security control, certification system, or substitute for an
institution's authorization controls.

## Supported versions

Only the current `main` commit is maintained. No released or long-term-support
version exists. Reports against older commits are still useful when they show a
design or integrity defect that remains present on `main`.

## Private reporting

Do not open a public issue for an undisclosed vulnerability. Use GitHub's
[private vulnerability report](https://github.com/veraxis-protocol/AuthContract/security/advisories/new)
for this repository. Include the affected commit SHA, a minimal reproducer,
impact, and whether the issue can expose or wrongly authorize a consequential
action. If the private-report form is unavailable to your account, contact the
repository owner privately through the contact route published at
[veraxis.io](https://veraxis.io/) before disclosing details.

Never include credentials, production policy, personal data, or live
institutional evidence in a report. Use synthetic fixtures.

## Scope and triage

High-priority reports include:

- acceptance of a digest-, artifact-, action-, fact-, or receipt-tamper;
- fail-open behavior on malformed, missing, stale, or inadmissible inputs;
- mismatch between the action checked and the action represented in a receipt;
- dependency or build compromise affecting the tested package; and
- a claim in the repository that materially exceeds the measured behavior.

The owner will acknowledge receipt when practical, reproduce against an exact
commit, record whether the report is confirmed, and coordinate disclosure after
a fix or bounded explanation is available. No response-time or remediation-time
commitment is established. Reports are evidence, not authorization to publish,
deploy, or change production systems.

## Out of scope

The repository has no service, hosted endpoint, persistence layer, production
identity system, or telemetry backend. Reports that assume those nonexistent
surfaces are not applicable. Automated natural-language source-to-rule
comparison is also not implemented end to end.

