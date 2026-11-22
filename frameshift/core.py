"""Deterministic state contracts for FrameShift Lab."""
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID_STATUSES = {"hypothesis", "canon", "disputed", "rejected"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class Ledger:
    def __init__(self, path: str | Path | None = None):
        home = Path(os.environ.get("FRAMESHIFT_HOME", "./data"))
        self.path = Path(path) if path else home / "events.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.events: list[dict[str, Any]] = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.events.append(json.loads(line))

    def append(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        event = {"event_id": new_id("evt"), "timestamp": now(), "kind": kind, "payload": payload}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        self.events.append(event)
        return event

    def latest_claims(self) -> dict[str, dict[str, Any]]:
        claims: dict[str, dict[str, Any]] = {}
        for e in self.events:
            p = e["payload"]
            if e["kind"] == "claim_created":
                claims[p["claim_id"]] = dict(p)
            elif e["kind"] == "claim_status_changed" and p["claim_id"] in claims:
                claims[p["claim_id"]]["status"] = p["status"]
                claims[p["claim_id"]]["status_reason"] = p.get("reason", "")
                if p.get("evidence"):
                    claims[p["claim_id"]].setdefault("evidence", []).append(p["evidence"])
        return claims


class FrameShift:
    # Stable character identity is deliberately separate from mutable story state.
    WIZARD_IDENTITY = {
        "name": "The Wizard",
        "role": "keeper of the simulated world and its internal continuity",
        "invariant": "Never present fictional world-state as verified real-world fact.",
    }
    BAZZA_BOUNDARY = "Voice only: no authority to establish facts or alter canon."
    JUNKrat_BOUNDARY = "Exploration only: hypotheses require independent evidence before promotion."

    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        if not self.ledger.events:
            self.ledger.append("world_initialized", {
                "world_state": {"scene": "The Workshop", "active_question": None},
                "wizard_identity": self.WIZARD_IDENTITY,
                "contracts": {"bazza": self.BAZZA_BOUNDARY, "junkrat": self.JUNKrat_BOUNDARY},
            })

    def say(self, text: str) -> str:
        # Deterministic sample voice; deliberately no state writes except an audit event.
        reply = f"Righto, cuz. That's a thought, not a fact. What's the bit we can actually test? — Bazza"
        self.ledger.append("persona_commentary", {"persona": "Bazza", "input": text, "output": reply})
        return reply

    def hypothesis(self, text: str, origin: str = "Junkrat") -> str:
        claim_id = new_id("claim")
        payload = {"claim_id": claim_id, "text": text, "status": "hypothesis", "origin": origin,
                   "evidence": [], "created_at": now()}
        self.ledger.append("claim_created", payload)
        return claim_id

    def commit(self, claim_id: str, evidence: str, confirm: bool) -> None:
        claims = self.ledger.latest_claims()
        if claim_id not in claims:
            raise KeyError(f"Unknown claim: {claim_id}")
        claim = claims[claim_id]
        if claim["status"] == "disputed":
            raise ValueError("A disputed claim cannot be promoted. Resolve the dispute first by creating a new tested claim.")
        if claim["status"] != "hypothesis":
            raise ValueError(f"Only hypotheses can be promoted; current status is {claim['status']}.")
        if not evidence or not evidence.strip():
            raise ValueError("Evidence is required.")
        if not confirm:
            raise PermissionError("Explicit --confirm is required; no silent canon writes.")
        self.ledger.append("claim_status_changed", {"claim_id": claim_id, "status": "canon", "evidence": evidence.strip(),
                                                        "reason": "Explicit user confirmation with recorded evidence"})

    def dispute(self, claim_id: str, reason: str) -> None:
        claims = self.ledger.latest_claims()
        if claim_id not in claims:
            raise KeyError(f"Unknown claim: {claim_id}")
        if claims[claim_id]["status"] == "rejected":
            raise ValueError("Rejected claims cannot be disputed; create a new claim if needed.")
        if not reason.strip():
            raise ValueError("A reason is required.")
        self.ledger.append("claim_status_changed", {"claim_id": claim_id, "status": "disputed", "reason": reason.strip()})

    def reject(self, claim_id: str, reason: str) -> None:
        claims = self.ledger.latest_claims()
        if claim_id not in claims:
            raise KeyError(f"Unknown claim: {claim_id}")
        if not reason.strip():
            raise ValueError("A reason is required.")
        self.ledger.append("claim_status_changed", {"claim_id": claim_id, "status": "rejected", "reason": reason.strip()})

    def inspect(self) -> dict[str, Any]:
        claims = self.ledger.latest_claims()
        world = next((e["payload"] for e in reversed(self.ledger.events) if e["kind"] == "world_initialized"), {})
        return {"wizard_identity": self.WIZARD_IDENTITY, "world_state": world.get("world_state", {}),
                "claims": list(claims.values()), "event_count": len(self.ledger.events), "ledger_path": str(self.ledger.path)}
