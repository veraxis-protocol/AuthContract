"""AuthContract reference implementation — bootstrap.

Implements the two BRS-established repairs that are testable without a
running policy engine:

  R01  canonical object partition and digest acyclicity   (AC-I06)
  R10  runtime fact provenance and admissibility          (AC-I15)

AC-012 local defensive conformance repairs, layered on R10:
  - trusted evidence binding: issuer/trust-basis/path/corroborator identity
    are decided against a verifier-established `VerifiedEvidence`, never
    against the asserting party's own claimed fields.
  - time validation: future-dated facts fail closed, and a naive/aware
    datetime mismatch returns an explicit refusal instead of an uncontrolled
    exception.

Normative source: TDD-AC-001 v0.2.1
  sha256 3126c989186633ba060adf46281d757a0e74b5312779b4e800a3ae39bf071cfa
"""

__version__ = "0.0.1"
