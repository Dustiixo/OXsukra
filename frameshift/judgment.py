"""Evidence-grounded self-distillation for decision quality.

This module does not let an agent declare itself smart. It scores a decision from
observable outcomes and explicit evidence, then distils reusable heuristics only
when repeated examples and held-out validation support them.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import mean
from typing import Iterable, Optional
import json
from pathlib import Path


@dataclass(frozen=True)
class Episode:
    task_id: str
    strategy: str
    context: str
    outcome_verified: bool
    evidence_strength: float  # 0..1, ideally assigned by independent verifier
    confidence: float         # 0..1, recorded before outcome is known
    cost: float = 0.0         # normalized 0..1
    reversible: bool = True
    failure_mode: str = ""
    note: str = ""

    def validate(self) -> None:
        for name in ("evidence_strength", "confidence", "cost"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not self.task_id.strip() or not self.strategy.strip():
            raise ValueError("task_id and strategy must be non-empty")


@dataclass(frozen=True)
class Judgment:
    task_id: str
    strategy: str
    smartness_score: float
    outcome_component: float
    evidence_component: float
    calibration_component: float
    efficiency_component: float
    risk_penalty: float
    rationale: tuple[str, ...]


@dataclass
class DistilledRule:
    rule_id: str
    condition: str
    recommendation: str
    support_count: int
    train_success_rate: float
    heldout_success_rate: float
    status: str = "candidate"
    limitations: list[str] = field(default_factory=list)


class JudgmentEngine:
    """Evaluate decisions and distil strategies from verified experience."""

    def judge(self, episode: Episode) -> Judgment:
        episode.validate()
        outcome = 1.0 if episode.outcome_verified else 0.0
        evidence = episode.evidence_strength
        # Brier-like calibration: confident failures and under-confident successes cost more.
        calibration = 1.0 - (episode.confidence - outcome) ** 2
        efficiency = 1.0 - episode.cost
        risk_penalty = 0.15 if (not episode.reversible and not episode.outcome_verified) else 0.0
        score = max(0.0, min(1.0,
            0.45 * outcome + 0.25 * evidence + 0.20 * calibration
            + 0.10 * efficiency - risk_penalty))
        rationale = []
        rationale.append("outcome verified" if outcome else "outcome not verified")
        rationale.append(f"evidence strength={evidence:.2f}")
        rationale.append(f"confidence calibration={calibration:.2f}")
        rationale.append(f"efficiency={efficiency:.2f}")
        if risk_penalty:
            rationale.append("penalty: irreversible action lacked verified success")
        if episode.failure_mode:
            rationale.append(f"recorded failure mode: {episode.failure_mode}")
        return Judgment(episode.task_id, episode.strategy, round(score, 4), outcome,
                        evidence, round(calibration, 4), efficiency, risk_penalty,
                        tuple(rationale))

    def compare(self, episodes: Iterable[Episode]) -> dict[str, dict[str, float]]:
        groups: dict[str, list[Judgment]] = {}
        for episode in episodes:
            groups.setdefault(episode.strategy, []).append(self.judge(episode))
        return {
            strategy: {
                "n": len(items),
                "mean_smartness": round(mean(x.smartness_score for x in items), 4),
                "verified_success_rate": round(mean(x.outcome_component for x in items), 4),
                "mean_evidence": round(mean(x.evidence_component for x in items), 4),
                "mean_calibration": round(mean(x.calibration_component for x in items), 4),
                "mean_efficiency": round(mean(x.efficiency_component for x in items), 4),
            }
            for strategy, items in sorted(groups.items())
        }

    def distil_rule(
        self,
        *,
        rule_id: str,
        condition: str,
        recommendation: str,
        supporting: Iterable[Episode],
        heldout: Iterable[Episode],
        min_support: int = 3,
        min_train_rate: float = 0.8,
        min_heldout_rate: float = 0.75,
    ) -> DistilledRule:
        train = list(supporting)
        test = list(heldout)
        if not train:
            raise ValueError("at least one supporting episode is required")
        for ep in train + test:
            ep.validate()
        train_rate = mean(1.0 if ep.outcome_verified else 0.0 for ep in train)
        heldout_rate = mean(1.0 if ep.outcome_verified else 0.0 for ep in test) if test else 0.0
        limitations = []
        if len(train) < min_support:
            limitations.append(f"insufficient support: {len(train)} < {min_support}")
        if train_rate < min_train_rate:
            limitations.append(f"training success rate below threshold: {train_rate:.2f}")
        if not test:
            limitations.append("no held-out validation examples")
        elif heldout_rate < min_heldout_rate:
            limitations.append(f"held-out success rate below threshold: {heldout_rate:.2f}")
        status = "promoted" if not limitations else "candidate"
        return DistilledRule(rule_id, condition, recommendation, len(train),
                             round(train_rate, 4), round(heldout_rate, 4),
                             status, limitations)


class EpisodeLedger:
    """Append-only JSONL ledger; each episode remains inspectable."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, episode: Episode) -> None:
        episode.validate()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(episode), ensure_ascii=False) + "\n")

    def read_all(self) -> list[Episode]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(Episode(**json.loads(line)))
        return out
