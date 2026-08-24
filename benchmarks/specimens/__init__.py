"""Specimen definitions for the AC-035 benchmark.

Specimens are declarative: each names the fixtures it composes and the
behaviour class the architecture is expected to produce. Expectations are
stated as *classes* (ALLOW vs fail-closed REFUSE, verification PASS vs FAIL)
rather than exact reason codes, because the class is the security-relevant
property. The exact observed reason code is recorded alongside as evidence, so
a change in refusal taxonomy is visible in the results without silently
weakening the assertion into a tautology.
"""

from __future__ import annotations

from typing import Any, NamedTuple


class Specimen(NamedTuple):
    specimen_id: str
    description: str
    artifact_fixture: str
    action_fixture: str
    facts_fixture: str
    expected: str  # "ALLOW" or "REFUSE"
    category: str


# --------------------------------------------------------------------------
# Phase 2 — the seven mandated end-to-end specimens
# --------------------------------------------------------------------------

E2E_SPECIMENS: tuple[Specimen, ...] = (
    Specimen(
        "E2E-01",
        "Happy path: valid contract, valid facts, permitted action",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "ALLOW",
        "happy_path",
    ),
    Specimen(
        "E2E-02",
        "Stale runtime fact: freshness window exceeded",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_stale.json",
        "REFUSE",
        "stale_fact",
    ),
    Specimen(
        "E2E-03",
        "Malformed contract artifact",
        "malformed.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "malformed_contract",
    ),
    Specimen(
        "E2E-04",
        "Action outside the declared projection domain",
        "banking_payment_specimen.json",
        "actions/send_payment_unknown_action_type.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "unsupported_domain",
    ),
    # E2E-05 (receipt mutation), E2E-06 (source/version mutation) and E2E-07
    # (deterministic replay) are constructed programmatically by the runner
    # rather than declared here.
    #
    # E2E-06 specifically must mutate contract-bound material while leaving the
    # binding STALE. The repository's `*_mutated.json` fixtures are mutated
    # *and correctly re-sealed* — their recomputed digest matches their declared
    # digest — so they are validly-bound variant contracts, not mutation
    # attacks. They are exercised below as ALLOW controls, and the genuine
    # stale-binding attack is built in the runner.
)


# --------------------------------------------------------------------------
# Phase 8 — adversarial battery
# --------------------------------------------------------------------------
# Every entry composes real accepted fixtures. Each is expected to fail closed;
# the happy-path control is included so a battery that trivially refuses
# everything is distinguishable from one that discriminates correctly.

ADVERSARIAL_SPECIMENS: tuple[Specimen, ...] = (
    Specimen(
        "ADV-00-control",
        "Control: the valid specimen must still be ALLOWed",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "ALLOW",
        "control",
    ),
    # --- action-side attacks -------------------------------------------------
    Specimen(
        "ADV-01",
        "Missing required action parameter",
        "banking_payment_specimen.json",
        "actions/send_payment_missing_required_parameter.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "missing_required_field",
    ),
    Specimen(
        "ADV-02",
        "Unknown action parameter where unknown fields are forbidden",
        "banking_payment_specimen.json",
        "actions/send_payment_unknown_parameter.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "unknown_field_forbidden",
    ),
    Specimen(
        "ADV-03",
        "Out-of-domain enum value",
        "banking_payment_specimen.json",
        "actions/send_payment_out_of_enum_value.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "out_of_domain_value",
    ),
    Specimen(
        "ADV-04",
        "Lossy decimal representation in action parameter",
        "banking_payment_specimen.json",
        "actions/send_payment_lossy_value.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "malformed_type",
    ),
    Specimen(
        "ADV-05",
        "Action type outside declared mediated scope",
        "banking_payment_specimen.json",
        "actions/send_payment_unknown_action_type.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "action_outside_scope",
    ),
    # --- fact-side attacks ---------------------------------------------------
    Specimen(
        "ADV-06",
        "Required fact absent from bundle",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_missing_required.json",
        "REFUSE",
        "missing_required_field",
    ),
    Specimen(
        "ADV-07",
        "Stale fact beyond freshness window",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_stale.json",
        "REFUSE",
        "stale_fact",
    ),
    Specimen(
        "ADV-08",
        "Future-dated fact timestamp",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_future_timestamp.json",
        "REFUSE",
        "malformed_type",
    ),
    Specimen(
        "ADV-09",
        "Timezone-naive fact timestamp (unverifiable ordering)",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_naive_timestamp.json",
        "REFUSE",
        "malformed_type",
    ),
    Specimen(
        "ADV-10",
        "Self-asserted fact where policy prohibits self-assertion",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_self_asserted_prohibited.json",
        "REFUSE",
        "trust_basis_violation",
    ),
    Specimen(
        "ADV-11",
        "Lossy wire representation of fact value",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_lossy_representation.json",
        "REFUSE",
        "malformed_type",
    ),
    Specimen(
        "ADV-12",
        "Duplicate fact_id in bundle",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_duplicate_fact_id.json",
        "REFUSE",
        "malformed_structured_input",
    ),
    Specimen(
        "ADV-13",
        "Unknown field on fact object",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_unknown_fact_field.json",
        "REFUSE",
        "unknown_field_forbidden",
    ),
    Specimen(
        "ADV-14",
        "Unknown field on fact bundle",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_unknown_bundle_field.json",
        "REFUSE",
        "unknown_field_forbidden",
    ),
    Specimen(
        "ADV-15",
        "Unknown field on verified-evidence object",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_unknown_evidence_field.json",
        "REFUSE",
        "unknown_field_forbidden",
    ),
    # --- caller-claim vs verifier-established evidence divergence ------------
    Specimen(
        "ADV-16",
        "Claimed value diverges from verifier-established evidence value",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_verified_value_mismatch.json",
        "REFUSE",
        "evidence_mismatch",
    ),
    Specimen(
        "ADV-17",
        "Claimed asserter diverges from verifier-established asserter",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_verified_asserter_mismatch.json",
        "REFUSE",
        "evidence_mismatch",
    ),
    Specimen(
        "ADV-18",
        "Claimed fact_id diverges from verifier-established fact_id",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_verified_fact_id_mismatch.json",
        "REFUSE",
        "evidence_mismatch",
    ),
    Specimen(
        "ADV-19",
        "Stale verified evidence presented with a fresh caller claim",
        "banking_payment_specimen.json",
        "actions/send_payment_valid.json",
        "runtime/facts_verified_time_stale_claimed_fresh.json",
        "REFUSE",
        "evidence_mismatch",
    ),
    # --- contract/binding attacks -------------------------------------------
    Specimen(
        "ADV-20",
        "Variant contract, mutated AND correctly re-sealed (binding intact)",
        "banking_payment_specimen_contract_mutated.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        # ALLOW is correct: this fixture's declared digest matches its
        # recomputed digest, so it is a different-but-validly-bound contract.
        # The stale-binding attack is ADV-35/ADV-36, built in the runner.
        "ALLOW",
        "validly_bound_variant",
    ),
    Specimen(
        "ADV-21",
        "Sibling digest disagreement across bound locations",
        "sibling_digest_mismatch.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "digest_mutation",
    ),
    Specimen(
        "ADV-22",
        "Self-referential contract digest",
        "self_referential.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "digest_scope_violation",
    ),
    Specimen(
        "ADV-23",
        "Cross-object digest substitution",
        "cross_object_substitution.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "digest_mutation",
    ),
    Specimen(
        "ADV-24",
        "Malformed artifact",
        "malformed.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "malformed_type",
    ),
    # --- activation / admission attacks -------------------------------------
    Specimen(
        "ADV-25",
        "Suspended contract (activation state not ACTIVE)",
        "banking_payment_specimen_suspended.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "inactive_contract",
    ),
    Specimen(
        "ADV-26",
        "Admission carrying approvals, contract binding intact",
        "banking_payment_specimen_admission_mutated.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        # ALLOW is correct at this commit: admission approvals are bound into
        # admission_digest (and therefore into receipt_digest) as evidence, but
        # they are not evaluated as an authorization gate. ADV-37 asserts the
        # binding property; the missing gate is recorded as finding AC-035-F1.
        "ALLOW",
        "admission_evidence_binding",
    ),
    Specimen(
        "ADV-27",
        "Admission present as JSON null",
        "banking_payment_specimen_admission_null.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "malformed_structured_input",
    ),
    Specimen(
        "ADV-28",
        "Admission present as JSON list",
        "banking_payment_specimen_admission_list.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "malformed_structured_input",
    ),
    # --- contract-declaration attacks ---------------------------------------
    Specimen(
        "ADV-29",
        "Duplicate required-fact declaration",
        "banking_payment_specimen_duplicate_required_fact.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "malformed_structured_input",
    ),
    Specimen(
        "ADV-30",
        "Unknown field on required-fact declaration",
        "banking_payment_specimen_unknown_required_fact_field.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "unknown_field_forbidden",
    ),
    Specimen(
        "ADV-31",
        "Corroboration required but not satisfiable as declared",
        "banking_payment_specimen_bad_corroboration_required.json",
        "actions/send_payment_valid.json",
        "runtime/facts_valid.json",
        "REFUSE",
        "corroboration_missing",
    ),
)
