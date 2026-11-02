"""Risk-aware *recommendations* and evidence-bounded improvement proposals.

This module cannot authorize, execute, bypass human oversight, or update its own
rules. It measures workflow outcomes, not the worth or knowledge of a person.
It does not modify another owner's data or read anything from the network.
"""
from __future__ import annotations

import math
import statistics
from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .core import GovernanceError, _nonempty, scope_digest

ADAPTIVE_SCHEMA = "ox.governance.adaptive.v0"
OBSERVATION_SCHEMA = "ox.governance.observation.v0"

# Flags are declared by an owning application or trusted classifier. Unknown
# material risk is conservative: request full deliberation, never downgrade.
HIGH_IMPACT_FLAGS = frozenset({
    "safety", "financial", "irreversible", "permission_change",
    "release", "policy_change", "cross_owner", "external_publication",
    "personal_data", "legal", "unknown",
})
LOW_IMPACT_FLAGS = frozenset({"routine", "read_only", "reversible"})
MAX_OBSERVATIONS = 5000
MIN_EVIDENCE = 5


def recommend_route(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Recommend review scope; not a permission or an execution decision.

    Default unknown risk is FULL_FOUR_LENS. Only an owner-declared, same-owner,
    explicitly reversible routine/read-only action may follow existing policy.
    The existing owner *still* must make its own authorization decision.
    """
    digest = scope_digest(packet)
    flags = packet.get("impact_flags")
    if not isinstance(flags, list) or not flags or any(not _nonempty(x) for x in flags):
        return _route(packet, digest, "FULL_FOUR_LENS", ["MISSING_IMPACT_CLASSIFICATION"])
    if len(flags) != len(set(flags)):
        raise GovernanceError("duplicate impact flags")
    declared = set(flags)
    if declared - HIGH_IMPACT_FLAGS - LOW_IMPACT_FLAGS:
        return _route(packet, digest, "FULL_FOUR_LENS", ["UNKNOWN_IMPACT_FLAG"])
    reasons = []
    if packet["origin_owner"] != packet["target_owner"]:
        reasons.append("DIFFERENT_OWNERS")
    for flag in sorted(declared & HIGH_IMPACT_FLAGS):
        reasons.append("HIGH_IMPACT_" + flag.upper())
    if reasons:
        return _route(packet, digest, "FULL_FOUR_LENS", reasons)
    if ("routine" in declared or "read_only" in declared) and "reversible" in declared:
        return _route(packet, digest, "OWNER_POLICY_ONLY", ["LOW_IMPACT_SAME_OWNER"])
    return _route(packet, digest, "FULL_FOUR_LENS", ["INSUFFICIENT_LOW_RISK_EVIDENCE"])


def _route(packet: Mapping[str, Any], digest: str, route: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "schema": ADAPTIVE_SCHEMA,
        "decision_id": packet["decision_id"],
        "scope_digest": digest,
        "recommended_review": route,
        "reason_codes": reasons,
        "execution_status": "NOT_AUTHORIZED",
        "must_follow_owner_policy": True,
        "policy_changed": False,
    }


def suggest_improvements(
    observations: Sequence[Mapping[str, Any]],
    *,
    verify_receipt: Callable[[Mapping[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    """Build human-review-only improvement suggestions from verified receipts.

    An observation captures workflow facts: elapsed minutes, re-opened decisions,
    missing evidence, and whether a review needed clarification. No scores about
    participants or automated adjustment of democratic rights.

    Observations without independent receipt verification are ignored. Even with
    sufficient samples no causal improvement claim is made: use a frozen baseline
    and controlled replay before accepting a policy change.
    """
    if not isinstance(observations, (list, tuple)):
        raise GovernanceError("observations must be a list or tuple")
    if len(observations) > MAX_OBSERVATIONS:
        raise GovernanceError("observation limit exceeded")
    verified: list[Mapping[str, Any]] = []
    rejected = 0
    seen: set[tuple[str, str]] = set()
    for item in observations:
        if not isinstance(item, Mapping) or item.get("schema") != OBSERVATION_SCHEMA:
            raise GovernanceError("invalid observation schema")
        if not _nonempty(item.get("workflow_id")) or not _nonempty(item.get("decision_ref")):
            raise GovernanceError("observation missing workflow or decision ref")
        # A field inside the record is never proof: verify it independently.
        if not callable(verify_receipt) or not _nonempty(item.get("receipt_ref")) or verify_receipt(item) is not True:
            rejected += 1
            continue
        key = (item["workflow_id"], item["decision_ref"])
        if key in seen:
            raise GovernanceError("duplicate verified decision observation")
        seen.add(key)
        minutes = item.get("review_minutes")
        if isinstance(minutes, bool) or not isinstance(minutes, (float, int)) or not math.isfinite(minutes) or minutes < 0 or minutes > 100000:
            raise GovernanceError("invalid review_minutes")
        for key in ("reopened", "missing_evidence", "clarification_needed"):
            if not isinstance(item.get(key), bool):
                raise GovernanceError(f"{key} must be boolean")
        verified.append(item)
    groups: dict[str, list[Mapping[str, Any]]] = {}
    for item in verified:
        groups.setdefault(item["workflow_id"], []).append(item)
    workflows = []
    for name in sorted(groups):
        data = groups[name]
        count = len(data)
        med = statistics.median(item["review_minutes"] for item in data)
        def ratio(field: str) -> float:
            return round(sum(bool(item[field]) for item in data) / count, 4)
        reopened = ratio("reopened")
        missing = ratio("missing_evidence")
        clarification = ratio("clarification_needed")
        suggestions = []
        if count >= MIN_EVIDENCE:
            if missing >= .2:
                suggestions.append("TRIAL_EVIDENCE_PREFLIGHT")
            if reopened >= .2:
                suggestions.append("TRIAL_INDEPENDENT_SECOND_REVIEW")
            if med >= 20:
                suggestions.append("TRIAL_READ_ONLY_CONTEXT_PREFILL")
            if clarification >= .3:
                suggestions.append("TRIAL_CLEARER_QUESTION_TEMPLATE")
        workflows.append({
            "workflow_id": name,
            "verified_count": count,
            "evidence_gate": "ENOUGH_FOR_PROPOSAL_ONLY" if count >= MIN_EVIDENCE else "INSUFFICIENT_EVIDENCE",
            "median_review_minutes": med,
            "reopen_rate": reopened,
            "missing_evidence_rate": missing,
            "clarification_rate": clarification,
            "suggested_experiments": suggestions,
            "automatic_policy_change": False,
        })
    return {
        "schema": ADAPTIVE_SCHEMA,
        "verified_observations": len(verified),
        "receipt_verification_required": True,
        "unverified_rejected": rejected,
        "workflows": workflows,
        "evaluation": "DESCRIPTIVE_ONLY_NO_CAUSAL_CLAIM",
        "requires_frozen_baseline_and_held_out_replay": True,
        "human_signoff_required": True,
        "rights_and_voting_weights_changed": False,
        "execution_status": "NOT_AUTHORIZED",
    }
