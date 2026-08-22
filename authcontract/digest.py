"""Canonical digest over the `contract` object. Implements AC-I06 / R01.

The v0.1 specification placed `approvals[]` inside `payload` while defining
the digest over `payload`, and required each approval to carry
`reviewed_payload_digest`. Satisfying that requires a SHA-256 fixed point
over a structure containing its own digest, which is infeasible.

v0.2.1 repairs this structurally: the artifact is partitioned so that no
object contains a digest of bytes containing itself.

    contract      the hashed object. Contains no digest of itself.
    admission     binds contract_digest. Never inside contract.
    activation    binds contract_digest. Never inside contract.
    derivations   each projection binds contract_digest.
    proof         binds contract_digest. Outermost.
"""

from __future__ import annotations

import hashlib
from typing import Any

import rfc8785

#: Keys that must never appear inside `contract` — each binds contract_digest.
FORBIDDEN_IN_CONTRACT = frozenset(
    {"admission", "activation", "derivations", "proof", "contract_digest"}
)

#: Sibling objects required to carry contract_digest when present.
BINDING_SIBLINGS = ("admission", "activation", "derivations", "proof")


class DigestScopeError(ValueError):
    """AC_DIGEST_SCOPE — a field binds a digest of bytes containing itself."""

    code = "AC_DIGEST_SCOPE"


class ContractDigestMismatch(ValueError):
    """AC_DIGEST — a sibling object binds a different contract."""

    code = "AC_DIGEST"


def _assert_no_self_reference(contract: dict[str, Any]) -> None:
    """Reject any digest-bearing back-reference inside `contract`.

    Enforced recursively: a nested `approvals` list carrying
    `reviewed_payload_digest` is the exact v0.1 defect and must not pass.
    """
    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in FORBIDDEN_IN_CONTRACT:
                    raise DigestScopeError(
                        f"{DigestScopeError.code}: '{key}' at {path or '<root>'} "
                        "may not occur inside `contract` — it binds contract_digest"
                    )
                if key.endswith("_digest") and key != "source_digest" \
                        and key != "anchor_digest" and key != "artifact_digest":
                    raise DigestScopeError(
                        f"{DigestScopeError.code}: digest-bearing field '{key}' "
                        f"at {path or '<root>'} may not occur inside `contract`"
                    )
                walk(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]")

    walk(contract, "")


def canonical_bytes(contract: dict[str, Any]) -> bytes:
    """RFC 8785 JCS serialization of the contract object."""
    _assert_no_self_reference(contract)
    return rfc8785.dumps(contract)


def contract_digest(contract: dict[str, Any]) -> str:
    """`sha256:<hex>` over JCS(contract). Refuses self-referential structures."""
    return "sha256:" + hashlib.sha256(canonical_bytes(contract)).hexdigest()


def verify_artifact(artifact: dict[str, Any]) -> str:
    """Verify a full `.ac` artifact. Returns the computed contract_digest.

    Checks:
      1. `contract` is present and contains no digest-bearing back-reference.
      2. Every present sibling binds exactly the computed contract_digest.
    """
    if "contract" not in artifact:
        raise ValueError("artifact has no `contract` object")

    computed = contract_digest(artifact["contract"])

    for sibling in BINDING_SIBLINGS:
        obj = artifact.get(sibling)
        if obj is None:
            continue
        bound = obj.get("contract_digest")
        if bound is None:
            raise ContractDigestMismatch(
                f"{ContractDigestMismatch.code}: `{sibling}` does not bind contract_digest"
            )
        if bound != computed:
            raise ContractDigestMismatch(
                f"{ContractDigestMismatch.code}: `{sibling}` binds {bound}, "
                f"contract hashes to {computed}"
            )

    return computed
