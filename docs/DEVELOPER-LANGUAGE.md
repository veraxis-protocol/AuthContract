# Developer-language guardrail

This file is a contributor/editorial guardrail. It is not user-facing marketing copy.

It records the linguistic lock established by `WORK-ORDER-AC-021 — Developer-Language Freeze + Repository Documentation Rewrite`, so future edits to developer-facing documentation stay consistent without needing to re-derive the rule from scratch.

## Provenance

The controlling linguistic artifact is:

```
FROZEN-DEVELOPER-README — AuthContract — v1.0 — 2026-08-23
Drive ID: 1EdVjTAseEhOimsKjp2uuHoXWdi794-IaFVWlxVP1XGI
```

That document is Owner-approved and linguistically controlling for README, quickstart, examples, CLI human-readable text, GitHub Actions/PR annotations, and future developer-facing repository documentation, unless explicitly superseded by the Owner. This file summarizes its rules; the frozen artifact itself is the source of truth if the two ever disagree.

## The controlling product sentence

```
Proof that the rule you shipped is actually supported by the source.
```

Use this sentence, or a close paraphrase that preserves its exact meaning, wherever the repository needs a one-line description of what AuthContract is (README tagline, repository description, etc.). Do not replace it with an architecture-first or ontology-first description.

## The controlling developer spine

```
source → rule → diff → test → CI/check → PASS/FAIL/UNRESOLVED → merge → ship → runtime → proof
```

This is the vocabulary developer-facing documentation should be built around. It is a workflow a developer already recognizes, not a new governance vocabulary to learn.

## Language hierarchy

**Developer-facing first layer** — README, quickstart, examples, CLI help text and human-readable output, PR/CI annotations, developer onboarding docs:

- source
- rule
- diff
- test
- CI / check
- PASS / FAIL / UNRESOLVED
- merge
- ship
- runtime
- proof

**Deeper/internal layer** — introduced only after the developer workflow is already clear, and appropriate in formal/internal technical documentation (module docstrings, TDD/SAR/ADR-style specification text, assurance records):

- `.ac` artifact structure
- canonical identity / digests
- projection
- fact admissibility
- merge-result binding
- OIC / ZTL / OAM / VEIP / AEP
- assurance/invariant/reason-code detail, BRS repair IDs, `AC-Ixx` invariant references

Developer-facing surfaces (README, quickstart, examples, CLI explanations, PR annotations) must not **lead** with BRS repair IDs, `AC-Ixx` invariants, authority ontology, warrant/admissibility vocabulary, or research-program acronyms. The deeper layer is not deleted or dumbed down — it stays available, further down the document or in linked reference material, for readers who want it.

## Human/machine dual-language rule

Machine reason codes stay stable and precise — they are not renamed or softened. Human-facing explanations, where they exist, should lead with plain developer language and let the reason code follow as detail, not the other way round.

```
Human:   FAIL — This check was not run against the version that would actually merge.
Machine: GIT_MERGE_RESULT_UNVERIFIED

Human:   FAIL — This action is not covered by the rule.
Machine: RUN_UNCLASSIFIED_ACTION

Human:   FAIL — More than one active rule applies and AuthContract cannot determine
         which one should win.
Machine: CONTRACT_SCOPE_CONFLICT
```

## Developer-facing vs. formal/internal documentation

This lock is about hierarchy and surface, not about deleting technical precision. It does not require mechanically rewriting formal TDD/SAR/ADR/specification text, module-level design-rationale docstrings, or assurance records into developer language — those may retain exact ontology and invariant terminology. It applies to what a developer sees first: the root README, quickstart material, CLI help/output, and PR/CI-visible text.

## Implementation-status discipline

Developer-facing documentation must describe what the accepted implementation actually does, not imply that the full product vision (for example, automated natural-language source-to-rule comparison) is already implemented end to end where it is still the target capability. Where a worked example illustrates the target experience, the document should make that distinction explicit rather than silently overstate current behavior. See README.md's "Current status" section for the current instance of this distinction.

If a future change to the accepted implementation would make a frozen README sentence technically false, do not silently rewrite it — flag the exact conflict and propose the narrowest factual correction for Engineering Lead approval, the same way `WORK-ORDER-AC-021`'s return record did.
