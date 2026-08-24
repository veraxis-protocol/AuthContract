# Dependency policy

AuthContract has one runtime dependency: `rfc8785`, which supplies the JSON
Canonicalization Scheme used in identity-bearing digests. Because a
canonicalization change can change artifact identity, the supported range is
bounded to the audited `0.1` line: `>=0.1.2,<0.2`.

The test extra bounds pytest to `>=7,<10`. Build tooling is declared separately
in `pyproject.toml`; it is not a runtime dependency.

This repository uses ranges for compatibility testing rather than claiming a
single universal lock across Python 3.10 and 3.12. Evidence must record the
resolved environment for the exact run. Pull requests receive dependency-diff
review and an advisory scan through `.github/workflows/security.yml`.
The scan upgrades its own `pip` environment before auditing and skips the local
editable AuthContract package, which is not a published PyPI dependency.

`make sbom` records the installed AuthContract and runtime dependency versions
in a deterministic CycloneDX document for the current candidate. It does not
attest a release, include operating-system packages, or establish that a
dependency is vulnerability-free.

Dependency updates that could affect canonical bytes, digests, exit behavior,
or receipt verification require the positive and negative verification suite.
