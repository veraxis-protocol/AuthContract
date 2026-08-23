"""Minimal VEIP-bound runtime decision + AEP-style receipt. Implements C-08.

Composes the existing, unmodified gates — digest.verify_artifact (R01/
AC-I06) via projection.project, projection.check_action (AC-016/AC-017),
and facts.admit (AC-I15/AC-012/AC-020) — into one bounded orchestration path
for the synthetic banking specimen. This module never reimplements or
reinterprets any of those gates' semantics; it only sequences them and, if
every one of them admits, produces a cryptographically bound receipt.

Order (mirrors the CONTROLLING DECISION structure already established by
the accepted gates):
  1. verify canonical artifact identity/bindings + build projection  (project())
  2. require ACTIVE projection/action closure                        (check_action())
  3. admit every contract-declared required fact                     (facts.admit())
  4. only if every step above admitted: issue an AEP-style receipt

ALLOW means exactly: the exact artifact verified; projection/action was
in-domain and ACTIVE; every contract-declared required fact was admitted
by the existing fact gate; no preceding gate refused. It does NOT mean
institutional authority or provenance was established — VerifiedEvidence
remains an injected, verifier-established interface here, never
cryptographic provenance verification. This module does not assert any
equation between the action parameter `secondary_approval_present` and the
fact `secondary_approval.present` beyond what already independently holds:
both must pass their own gate for ALLOW; neither implies the other.

The receipt binds contract_digest, activation_id, projection_digest,
runtime_fact_set_digest, exact_action_digest, admission_digest, decision,
execution_result, and decision_time, plus a receipt_digest over exactly
those nine fields — deliberately never over bytes containing itself, the
same structural discipline digest.py already enforces for contract_digest/
R01. All digests use RFC 8785 JCS + SHA-256, consistent with the
repository's existing digest discipline.

execution_result is a caller-chosen, bounded synthetic label (see
ALLOWED_EXECUTION_RESULTS) representing what happened AFTER an ALLOW
decision. This module never claims a real payment/bank side effect
occurred, never performs one, and never claims production institutional
authorization or cryptographic provenance verification.

AC-020 / C-08 amendment (F2 repair): the AC-019 receipt omitted
decision-relevant temporal/assertion/admission context, so a caller could
mutate any of them without changing the receipt. This amendment:
  - binds `decision_time` — the exact evaluation time used for freshness;
  - extends `runtime_fact_set_digest` to also bind each admitted fact's
    VERIFIED asserting identity and VERIFIED assertion time (AC-020 C2),
    consistent with facts.py now sourcing those from VerifiedEvidence;
  - adds `admission_digest` — a deterministic digest over the artifact's
    exact `admission` sibling object (AC-020 C3). This is evidence
    continuity only: it proves which admission/approval context
    accompanied the decision, never that the admission constitutes valid
    institutional authority. `contract_digest` remains scoped to `contract`
    only and is unaffected by admission content (R01 unchanged).
  - the fact bundle's runtime shape is now closed (AC-020 B1-B4): duplicate
    runtime fact_ids, duplicate contract required_facts declarations, any
    unrecognised bundle/fact/evidence field, and a non-boolean
    `corroboration_required` declaration all refuse rather than being
    silently accepted.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import rfc8785

from .digest import ContractDigestMismatch, DigestScopeError
from .facts import (
    AssertedFact,
    FactContract,
    FactInadmissible,
    VerifiedEvidence,
    admit,
)
from .projection import (
    InactiveContract,
    ProjectionDomainError,
    UnclassifiedAction,
    check_action,
    project,
    projection_digest as _projection_digest_of,
)

#: Bounded, explicit, synthetic execution outcomes. MVP-alpha only — none of
#: these claims a real bank/payment side effect occurred.
ALLOWED_EXECUTION_RESULTS = frozenset({"NOT_EXECUTED", "SIMULATED_SUCCESS", "SIMULATED_FAILURE"})

#: The receipt's exact schema. An unknown field is refused, not dropped;
#: every one of these is mandatory (receipt_digest included — AC-019 B3
#: calls it "recommended if cleanly bounded"; it is cleanly bounded here,
#: so it is required like the rest). AC-020 C1/C3 add decision_time and
#: admission_digest.
RECEIPT_REQUIRED_KEYS = frozenset({
    "contract_digest",
    "activation_id",
    "projection_digest",
    "runtime_fact_set_digest",
    "exact_action_digest",
    "admission_digest",
    "decision",
    "execution_result",
    "decision_time",
    "receipt_digest",
})
#: The subset that receipt_digest itself is computed over — never including
#: receipt_digest, for the same reason contract_digest never includes
#: itself (R01).
_RECEIPT_PAYLOAD_KEYS = (
    "contract_digest",
    "activation_id",
    "projection_digest",
    "runtime_fact_set_digest",
    "exact_action_digest",
    "admission_digest",
    "decision",
    "execution_result",
    "decision_time",
)


class VeipRefusal(ValueError):
    """Base for refusals originating in this orchestration layer itself
    (as opposed to a propagated upstream gate refusal, which keeps its own
    original exception type/code)."""
    code = "VEIP_REFUSED"


class FactBundleIncomplete(VeipRefusal):
    """VEIP_FACT_BUNDLE_INCOMPLETE — a contract-declared required fact has
    no corresponding entry in the supplied facts/evidence bundle."""
    code = "VEIP_FACT_BUNDLE_INCOMPLETE"


class MalformedInput(VeipRefusal):
    """VEIP_MALFORMED_INPUT — the facts/evidence bundle, or a
    contract.required_facts declaration, is not shaped as expected."""
    code = "VEIP_MALFORMED_INPUT"


class MissingActivationId(VeipRefusal):
    """VEIP_MISSING_ACTIVATION_ID — projection succeeded but activation_id
    is None; a receipt cannot bind an identity that isn't there."""
    code = "VEIP_MISSING_ACTIVATION_ID"


class InvalidExecutionResult(VeipRefusal):
    """VEIP_INVALID_EXECUTION_RESULT — caller supplied an execution_result
    outside the bounded synthetic set."""
    code = "VEIP_INVALID_EXECUTION_RESULT"


class ReceiptMalformed(VeipRefusal):
    """VEIP_RECEIPT_MALFORMED — receipt is missing a required field, or
    carries a field outside the exact schema (fail closed; no silent drop)."""
    code = "VEIP_RECEIPT_MALFORMED"


class ReceiptMismatch(VeipRefusal):
    """VEIP_RECEIPT_MISMATCH — a receipt field does not match the value
    independently recomputed from the source artifact/action/facts."""
    code = "VEIP_RECEIPT_MISMATCH"


@dataclass(frozen=True)
class RunResult:
    decision: str  # "ALLOW" or "REFUSED"
    reason_code: str
    message: str | None
    receipt: dict[str, Any] | None  # only present when decision == "ALLOW"


@dataclass(frozen=True)
class VerifyResult:
    status: str  # "PASS" or "REFUSED"
    reason_code: str
    message: str | None


def _normalize_for_digest(value: Any) -> Any:
    """Decimal has no native JSON representation; every other value this
    orchestration ever handles (bool/int/str, from facts.admit()/
    check_action()'s own normalization) is already JSON-native."""
    if isinstance(value, Decimal):
        return str(value)
    return value


def _digest_payload(payload: dict[str, Any]) -> str:
    """`sha256:<hex>` over RFC 8785 JCS(payload) — identical discipline to
    digest.contract_digest and projection.projection_digest."""
    return "sha256:" + hashlib.sha256(rfc8785.dumps(payload)).hexdigest()


#: Closed runtime shape (AC-020 B3): unrecognised fields at any of these
#: three levels refuse rather than being silently dropped.
_BUNDLE_ALLOWED_KEYS = frozenset({"now", "facts"})
_FACT_ENTRY_ALLOWED_KEYS = frozenset({
    "fact_id", "raw_value", "wire_representation", "asserted_by", "asserted_at",
    "claimed_issuer", "claimed_trust_basis", "claimed_assertion_path",
    "claimed_corroborated_by", "evidence",
})
_EVIDENCE_ALLOWED_KEYS = frozenset({
    "fact_id", "value", "asserted_by", "asserted_at",
    "issuer", "trust_basis", "assertion_path", "corroborated_by",
})


def _build_fact_contract(declared: dict[str, Any]) -> FactContract:
    from datetime import timedelta

    if "corroboration_required" in declared:
        corroboration_required = declared["corroboration_required"]
        if not isinstance(corroboration_required, bool):
            # AC-020 B4: no truthiness coercion — bool("false") is True, and
            # a declaration that says "false" must never be read as True.
            raise ValueError(
                "corroboration_required must be a boolean, got "
                f"{corroboration_required!r}"
            )
    else:
        corroboration_required = False

    return FactContract(
        fact_id=declared["fact_id"],
        value_type=declared["value_type"],
        issuer=declared["issuer"],
        trust_basis=declared["trust_basis"],
        freshness=timedelta(seconds=declared["freshness_seconds"]),
        assertion_path=declared["assertion_path"],
        self_assertion_policy=declared["self_assertion_policy"],
        wire_representation=declared["wire_representation"],
        corroboration_required=corroboration_required,
    )


def _parse_fact_bundle(
    raw: Any,
) -> tuple[datetime | None, dict[str, tuple[AssertedFact, VerifiedEvidence]], str | None]:
    """Returns (now, {fact_id: (AssertedFact, VerifiedEvidence)}, None) on
    success, or (None, {}, error_message) on any malformation.

    AC-020 B1/B3: refuses a duplicate runtime fact_id (never silently
    overwrites by dict-insertion order) and any unrecognised field at the
    bundle/fact-entry/evidence level.
    """
    if not isinstance(raw, dict):
        return None, {}, "facts/evidence bundle must be a JSON object"

    unknown_top = set(raw) - _BUNDLE_ALLOWED_KEYS
    if unknown_top:
        return None, {}, f"facts/evidence bundle has unsupported field(s): {sorted(unknown_top)}"

    now_raw = raw.get("now")
    if not isinstance(now_raw, str):
        return None, {}, "facts/evidence bundle missing string field 'now'"
    try:
        now = datetime.fromisoformat(now_raw)
    except ValueError as exc:
        return None, {}, f"facts/evidence bundle 'now' is not a valid ISO 8601 datetime: {exc}"

    facts_raw = raw.get("facts")
    if not isinstance(facts_raw, list):
        return None, {}, "facts/evidence bundle missing list field 'facts'"

    entries: dict[str, tuple[AssertedFact, VerifiedEvidence]] = {}
    for i, item in enumerate(facts_raw):
        if not isinstance(item, dict):
            return None, {}, f"facts[{i}] must be an object"

        unknown_fact = set(item) - _FACT_ENTRY_ALLOWED_KEYS
        if unknown_fact:
            return None, {}, f"facts[{i}] has unsupported field(s): {sorted(unknown_fact)}"

        try:
            asserted_at = datetime.fromisoformat(item["asserted_at"])
            fact = AssertedFact(
                fact_id=item["fact_id"],
                raw_value=item["raw_value"],
                wire_representation=item["wire_representation"],
                issuer=item["claimed_issuer"],
                trust_basis=item["claimed_trust_basis"],
                asserted_by=item["asserted_by"],
                asserted_at=asserted_at,
                assertion_path=item["claimed_assertion_path"],
                corroborated_by=item.get("claimed_corroborated_by"),
            )
            ev_raw = item["evidence"]
            if not isinstance(ev_raw, dict):
                return None, {}, f"facts[{i}].evidence must be an object"

            unknown_ev = set(ev_raw) - _EVIDENCE_ALLOWED_KEYS
            if unknown_ev:
                return None, {}, f"facts[{i}].evidence has unsupported field(s): {sorted(unknown_ev)}"

            verified_asserted_at = datetime.fromisoformat(ev_raw["asserted_at"])
            evidence = VerifiedEvidence(
                fact_id=ev_raw["fact_id"],
                value=ev_raw["value"],
                asserted_by=ev_raw["asserted_by"],
                asserted_at=verified_asserted_at,
                issuer=ev_raw["issuer"],
                trust_basis=ev_raw["trust_basis"],
                assertion_path=ev_raw["assertion_path"],
                corroborated_by=ev_raw.get("corroborated_by"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            return None, {}, f"facts[{i}] is malformed: {exc}"

        if fact.fact_id in entries:
            return None, {}, f"duplicate runtime fact_id {fact.fact_id!r} in facts bundle"

        entries[fact.fact_id] = (fact, evidence)

    return now, entries, None


def run_specimen(
    artifact: dict[str, Any],
    action: dict[str, Any],
    fact_bundle: dict[str, Any],
    *,
    execution_result: str,
) -> RunResult:
    """The full bounded orchestration. Returns a RunResult; never raises for
    an ordinary refusal — only a genuinely unanticipated internal error
    would propagate, which callers should treat as fail-closed too.
    """
    if execution_result not in ALLOWED_EXECUTION_RESULTS:
        return RunResult(
            decision="REFUSED",
            reason_code=InvalidExecutionResult.code,
            message=(
                f"{InvalidExecutionResult.code}: execution_result {execution_result!r} "
                f"is not one of {sorted(ALLOWED_EXECUTION_RESULTS)}"
            ),
            receipt=None,
        )

    now, fact_entries, parse_error = _parse_fact_bundle(fact_bundle)
    if parse_error is not None:
        return RunResult(
            decision="REFUSED",
            reason_code=MalformedInput.code,
            message=f"{MalformedInput.code}: {parse_error}",
            receipt=None,
        )

    try:
        proj = project(artifact)
    except (DigestScopeError, ContractDigestMismatch, ProjectionDomainError) as exc:
        return RunResult(decision="REFUSED", reason_code=exc.code, message=str(exc), receipt=None)

    try:
        validated_params = check_action(proj, action)
    except (InactiveContract, UnclassifiedAction, ProjectionDomainError) as exc:
        return RunResult(decision="REFUSED", reason_code=exc.code, message=str(exc), receipt=None)

    contract = artifact["contract"]
    required_facts = contract.get("required_facts", [])
    if not isinstance(required_facts, list):
        return RunResult(
            decision="REFUSED",
            reason_code=MalformedInput.code,
            message=f"{MalformedInput.code}: contract.required_facts must be a list",
            receipt=None,
        )

    subject = contract.get("subject")
    governed_subject = subject.get("system") if isinstance(subject, dict) else None

    # AC-020 B2: duplicate required_facts declarations for the same fact_id
    # refuse — no composition rule is established for this specimen.
    seen_declared_fact_ids: set[str] = set()

    admitted_records: list[dict[str, Any]] = []
    for declared in required_facts:
        fact_id = declared.get("fact_id") if isinstance(declared, dict) else None

        if fact_id in seen_declared_fact_ids:
            return RunResult(
                decision="REFUSED",
                reason_code=MalformedInput.code,
                message=(
                    f"{MalformedInput.code}: contract.required_facts declares "
                    f"duplicate fact_id {fact_id!r}"
                ),
                receipt=None,
            )
        seen_declared_fact_ids.add(fact_id)

        entry = fact_entries.get(fact_id)
        if entry is None:
            return RunResult(
                decision="REFUSED",
                reason_code=FactBundleIncomplete.code,
                message=(
                    f"{FactBundleIncomplete.code}: no facts/evidence entry supplied "
                    f"for required fact {fact_id!r}"
                ),
                receipt=None,
            )
        try:
            fact_contract = _build_fact_contract(declared)
        except (KeyError, ValueError, TypeError) as exc:
            return RunResult(
                decision="REFUSED",
                reason_code=MalformedInput.code,
                message=(
                    f"{MalformedInput.code}: contract.required_facts entry for "
                    f"{fact_id!r} is malformed: {exc}"
                ),
                receipt=None,
            )

        asserted_fact, evidence = entry
        try:
            admitted_value = admit(
                fact_contract,
                asserted_fact,
                evidence=evidence,
                governed_subject=governed_subject,
                now=now,
            )
        except FactInadmissible as exc:
            return RunResult(decision="REFUSED", reason_code=exc.code, message=str(exc), receipt=None)

        # AC-020 C2: bind the VERIFIED asserting identity and VERIFIED
        # assertion time too, not just value/issuer/trust/path/corroborator
        # — a decision-relevant temporal/assertion mutation must now change
        # this digest.
        admitted_records.append({
            "fact_id": fact_contract.fact_id,
            "value_type": fact_contract.value_type,
            "value": _normalize_for_digest(admitted_value),
            "asserted_by": evidence.asserted_by,
            "asserted_at": evidence.asserted_at.isoformat(),
            "evidence": {
                "issuer": evidence.issuer,
                "trust_basis": evidence.trust_basis,
                "assertion_path": evidence.assertion_path,
                "corroborated_by": evidence.corroborated_by,
            },
        })

    if proj.activation_id is None:
        return RunResult(
            decision="REFUSED",
            reason_code=MissingActivationId.code,
            message=f"{MissingActivationId.code}: projection has no activation_id",
            receipt=None,
        )

    runtime_fact_set_digest = _digest_payload(
        {"facts": sorted(admitted_records, key=lambda r: r["fact_id"])}
    )
    exact_action_digest = _digest_payload({
        "action_type": action.get("action_type"),
        "parameters": {
            name: _normalize_for_digest(value) for name, value in validated_params.items()
        },
    })
    # AC-020 C3: bind the exact admission sibling context separately from
    # contract_digest — evidence continuity only, never a claim that
    # admission constitutes valid institutional authority. Missing/
    # malformed `admission` digests as the canonical empty object.
    admission = artifact.get("admission")
    admission_digest = _digest_payload(admission if isinstance(admission, dict) else {})

    payload = {
        "contract_digest": proj.contract_digest,
        "activation_id": proj.activation_id,
        "projection_digest": _projection_digest_of(proj),
        "runtime_fact_set_digest": runtime_fact_set_digest,
        "exact_action_digest": exact_action_digest,
        "admission_digest": admission_digest,
        "decision": "ALLOW",
        "execution_result": execution_result,
        # AC-020 C1: bind the exact decision/evaluation time freshness used.
        "decision_time": now.isoformat(),
    }
    receipt = dict(payload)
    receipt["receipt_digest"] = _digest_payload(payload)

    return RunResult(decision="ALLOW", reason_code="OK", message=None, receipt=receipt)


def _validate_receipt_schema(receipt: Any) -> str | None:
    if not isinstance(receipt, dict):
        return "receipt must be a JSON object"
    missing = RECEIPT_REQUIRED_KEYS - set(receipt)
    if missing:
        return f"receipt missing required field(s): {sorted(missing)}"
    unknown = set(receipt) - RECEIPT_REQUIRED_KEYS
    if unknown:
        return f"receipt has unsupported field(s): {sorted(unknown)}"
    return None


def verify_receipt(
    receipt: dict[str, Any],
    artifact: dict[str, Any],
    action: dict[str, Any],
    fact_bundle: dict[str, Any],
) -> VerifyResult:
    """Independently recompute every binding from the raw source inputs and
    compare against the supplied receipt field by field. Never trusts a
    digest string merely because it is present in `receipt` — the only use
    made of `receipt` before recomputation is reading `execution_result`
    (a caller-chosen label, not a digest) so the same execution_result is
    used to build the reference receipt for comparison.
    """
    schema_error = _validate_receipt_schema(receipt)
    if schema_error is not None:
        return VerifyResult(
            status="REFUSED",
            reason_code=ReceiptMalformed.code,
            message=f"{ReceiptMalformed.code}: {schema_error}",
        )

    execution_result = receipt["execution_result"]
    reference = run_specimen(artifact, action, fact_bundle, execution_result=execution_result)

    if reference.decision != "ALLOW" or reference.receipt is None:
        return VerifyResult(
            status="REFUSED",
            reason_code=reference.reason_code,
            message=(
                "receipt cannot be independently reconstructed from the supplied "
                f"artifact/action/facts: {reference.message}"
            ),
        )

    for key in _RECEIPT_PAYLOAD_KEYS + ("receipt_digest",):
        if receipt.get(key) != reference.receipt.get(key):
            return VerifyResult(
                status="REFUSED",
                reason_code=ReceiptMismatch.code,
                message=(
                    f"{ReceiptMismatch.code}: field {key!r} does not match the "
                    "independently recomputed value"
                ),
            )

    return VerifyResult(status="PASS", reason_code="OK", message=None)
