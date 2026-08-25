# Versioning and compatibility

AuthContract is currently version `0.0.1`: experimental and pre-1.0. The
repository has no published package or release compatibility promise. Pin an
exact commit SHA when reproducing or integrating it.

## Versioned surfaces

The following are public integration surfaces at a pinned commit, but may
change incompatibly before 1.0:

- the six CLI subcommands and their flags;
- exit codes (`0` for PASS/ALLOW, `1` for refusal or error);
- JSON `status`, `decision`, and `reason_code` values;
- the Python functions and result objects documented in `AGENTS.md`;
- contract artifact, runtime-fact, action, and receipt JSON structures; and
- canonicalization and digest rules used to bind those structures.

Human-readable messages are never a compatibility interface. Consumers should
branch on structured fields, while still pinning the exact commit because the
reason-code set is not yet frozen.

## Change rules

Before 1.0, a change to a CLI name or flag, exit semantics, reason code, Python
signature, required JSON field, canonicalization rule, or digest scope is a
breaking change. Such a change must:

1. be explicit in the pull request and documentation;
2. update positive and negative fixtures and tests;
3. identify affected receipts and artifacts;
4. avoid silently reinterpreting an existing digest; and
5. use a new artifact/schema/version identity when old and new bytes could
   otherwise be confused.

Adding an optional field is compatible only when older consumers safely ignore
it and its presence cannot widen authority. A new refusal condition is treated
as behaviorally consequential even when it fails closed.

## Releases and artifacts

No distributable release or attestation is established. Source installs are the
only supported installation route. An SBOM may be generated for a candidate
commit with `make sbom`; it is evidence about resolved package metadata, not a
release attestation or security guarantee.

