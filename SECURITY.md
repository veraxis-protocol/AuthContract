# Security policy

## 1. What this repository is

AuthContract is an **experimental reference implementation at TRL 4**. It is
not audited, not security-certified, and not production-ready. Maturity is
assessed in [`docs/TRL-ASSESSMENT.md`](docs/TRL-ASSESSMENT.md).

Treat it as research and engineering evidence. Do not place it on a path where a
security failure would have real consequences.

## 2. Supported versions

**Only the current `main` is supported.**

There is no released version, no tag, no published package, and no backport
branch. A fix, if one is made, lands on `main` and nowhere else. Any older
commit you have checked out is unsupported, and nothing in this repository
promises that a fix will be applied to it.

## 3. Reporting a vulnerability

**Do not open a public GitHub issue for a suspected vulnerability**, and do not
attach exploit details to a pull request. Public issues are the right channel
for ordinary bugs and for claims that do not hold — not for security reports.

**Current status of the private reporting route: NOT ESTABLISHED.**

At the time of writing, this repository publishes no verified private
vulnerability-reporting channel:

- GitHub Private Vulnerability Reporting could not be confirmed as enabled. The
  repository metadata reachable from this project's tooling does not expose
  that setting, so its state is *unknown*, not *enabled*.
- No security contact address is published here. None is invented for this
  document — a reporting address that does not demonstrably reach someone is
  worse than an honest absence, because it silently swallows reports.

**Owner action required.** The smallest sufficient fix is to enable GitHub
Private Vulnerability Reporting on this repository (Settings → Advanced
Security → Private vulnerability reporting), which gives reporters a
first-class private channel at
`https://github.com/veraxis-protocol/AuthContract/security/advisories/new`
without publishing any address. Once enabled, this section should be replaced
with that link.

Until then, a reporter who needs a private channel should contact the owner
through [veraxis.io](https://veraxis.io) and **withhold technical detail until a
private channel is agreed**.

## 4. Triage policy

Bounded to what an experimental TRL 4 reference implementation can honestly
commit to. These are handling intentions, not a service-level agreement, and no
response time is promised.

| Severity | Meaning here | Handling |
|---|---|---|
| **Critical** | Enables an unauthorized ALLOW, forges or defeats receipt verification, or breaks the fail-closed property | Work stops on other changes. Fixed on `main`, or the affected capability is documented as unsafe and its limitation stated in `README.md` and `AGENTS.md`. |
| **High** | Compromises canonical identity, digest binding, projection closure, fact admissibility, or the merge-result gate without directly producing a false ALLOW | Fixed on `main` before further feature work, with a regression test that fails without the fix. |
| **Medium** | Correctness or robustness defect with no path to a false ALLOW — crashes, unhandled input, misleading output | Recorded as a finding and scheduled. May be fixed alongside other work. |
| **Low** | Hardening, defence in depth, documentation that could mislead a reader into an unsafe assumption | Recorded. Fixed opportunistically. |

Every accepted finding gets a regression test. A fix without a test that
demonstrates the original failure is not considered closed.

## 5. What automated checks do and do not establish

This repository runs an automated dependency-advisory check
(`.github/workflows/security.yml`) against its declared, version-controlled
dependency set.

**A passing scanner is not an audit.** It establishes only that the specific
advisory database consulted contained no matching published advisory for those
specific pinned versions at that moment. It does **not** establish:

- that no vulnerability exists — absence of a published advisory is not absence of a defect;
- that this project's own code is free of vulnerabilities — no scanner in this repository analyses it for security defects;
- that any third party has reviewed the design, the cryptographic binding, or the refusal logic;
- any certification, accreditation, or compliance status whatsoever.

No independent security review of AuthContract has ever been performed. That
gap is recorded in [`docs/TRL-ASSESSMENT.md`](docs/TRL-ASSESSMENT.md) as a
condition for TRL 6 and is not closed by any check in this repository.

## 6. Responsible disclosure

If you find something:

- **Report privately first** if the finding could enable a false ALLOW, forge a
  receipt, or defeat a refusal — even though the private route above is not yet
  established, initiate contact before publishing detail.
- **Give the owner a reasonable chance to respond** before public disclosure.
  Because no response-time commitment exists, a reporter is entitled to set
  their own reasonable deadline and say what it is.
- **Do not test against systems you do not own.** Everything needed to
  reproduce a finding is in this repository: the fixtures, the specimens, and
  the falsification harness (`falsify.py`) all run locally with no network and
  no credentials.
- **Publishing a finding is welcome once disclosed responsibly.** This project's
  stated purpose is to be falsifiable. A demonstrated failure is a contribution,
  not an attack, and it will be recorded rather than quietly repaired.
