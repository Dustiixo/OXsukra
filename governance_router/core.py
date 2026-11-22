"""Reference-only governance router: verifies review completeness and scopes handoffs.

Does NOT collect votes, decide policies, verify evidence, or execute a target action.
An owner-controlled authority verifier must validate real human approval receipts.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Collection, Mapping
from typing import Any

LENSES = ("direct", "deliberative", "liquid", "participatory")
SCHEMA = "ox.governance.decision.v0"
HANDOFF_SCHEMA = "ox.governance.handoff.v0"


class GovernanceError(ValueError):
    """Invalid decision packet, insufficient review, or missing authority."""


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GovernanceError(message)


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(_nonempty(x) for x in value)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise GovernanceError("packet must contain JSON-serializable data") from exc


def scope_digest(packet: Mapping[str, Any]) -> str:
    """Hash the precise intended effect; edits require a fresh approval receipt."""
    _require(isinstance(packet, Mapping), "decision packet must be an object")
    keys = ("schema", "decision_id", "origin_owner", "target_owner", "action_ref", "impact")
    for key in keys:
        _require(_nonempty(packet.get(key)), f"missing {key}")
    _require(packet["schema"] == SCHEMA, "unknown decision schema")
    # Bind the proposal AND its deliberation record; changing either needs new approval.
    return hashlib.sha256(_canonical(packet)).hexdigest()


def review(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Validate four distinct review lenses; never aggregate them into a winner."""
    digest = scope_digest(packet)
    _require(_nonempty(packet.get("question")), "missing decision question")
    lenses = packet.get("lenses")
    _require(isinstance(lenses, dict), "lenses must be an object")
    _require(set(lenses) == set(LENSES), "exactly four named lenses are required")
    _require(_strings(packet.get("affected_owner_refs")), "affected_owner_refs must be a list")
    pending: list[str] = []
    omitted: list[str] = []
    dissent: dict[str, list[str]] = {}
    for name in LENSES:
        item = lenses[name]
        _require(isinstance(item, dict), f"{name} must be an object")
        state = item.get("state")
        _require(state in ("pending", "reported", "not_applicable"), f"invalid {name} state")
        if state == "pending":
            pending.append(name)
        elif state == "not_applicable":
            _require(_nonempty(item.get("reason")), f"{name} requires waiver reason")
            omitted.append(name)
        else:
            _require(_nonempty(item.get("method")), f"{name} requires method")
            _require(_nonempty(item.get("summary")), f"{name} requires summary")
            _require(_strings(item.get("evidence_refs")) and item["evidence_refs"],
                     f"{name} requires at least one evidence reference")
            _require(_strings(item.get("dissent_refs")), f"{name} dissent_refs must be a list")
            if item["dissent_refs"]:
                dissent[name] = list(item["dissent_refs"])
    return {
        "schema": "ox.governance.review.v0",
        "decision_id": packet["decision_id"],
        "scope_digest": digest,
        "status": "NEEDS_REVIEW" if pending else (
            "CONTESTED_HUMAN_REVIEW" if dissent else "AWAITING_HUMAN_AUTHORITY"),
        "pending_lenses": pending,
        "waived_lenses": omitted,
        "dissent_by_lens": dissent,
        "automatic_winner": None,
        "authorized": False,
    }


def prepare_handoff(
    packet: Mapping[str, Any],
    approval: Mapping[str, Any],
    *,
    registered_owners: Collection[str],
    verify_human_approval: Callable[[Mapping[str, Any], str], bool],
) -> dict[str, Any]:
    """Issue a *non-executing* scoped handoff for a separately authorized owner.

    The caller must provide a real receipt verifier (not a model assertion). The
    destination adapter must independently verify that approval before effects.
    """
    result = review(packet)
    _require(not result["pending_lenses"], "all four lenses must be considered")
    _require(packet["target_owner"] in registered_owners, "unregistered owner")
    _require(isinstance(approval, Mapping), "approval must be an object")
    _require(_nonempty(approval.get("receipt_ref")), "missing approval receipt")
    _require(approval.get("scope_digest") == result["scope_digest"],
             "approval does not cover exact decision scope")
    _require(callable(verify_human_approval), "trusted approval verifier required")
    _require(verify_human_approval(approval, result["scope_digest"]) is True,
             "human approval not independently verified")
    return {
        "schema": HANDOFF_SCHEMA,
        "decision_id": packet["decision_id"],
        "origin_owner": packet["origin_owner"],
        "target_owner": packet["target_owner"],
        "action_ref": packet["action_ref"],
        "scope_digest": result["scope_digest"],
        "review_status": result["status"],
        "waived_lenses": result["waived_lenses"],
        "dissent_by_lens": result["dissent_by_lens"],
        "approval_receipt_ref": approval["receipt_ref"],
        "execution_status": "NOT_EXECUTED",
    }
