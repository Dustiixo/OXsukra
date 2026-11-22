"""Recursive multi-pass review scaffold with explicit provenance and stop rules.

The bundled backend is intentionally deterministic and transparent. It exercises
orchestration contracts; it is NOT an LLM and does not claim semantic intelligence.
An LLM backend can later implement the same protocol without changing the ledger.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Protocol, Any
import hashlib
import re

PROFILES = {
    "Junkrat": {
        "purpose": "divergent exploration",
        "questions": ["What alternative explanation exists?", "What assumption could be inverted?", "What experiment would surprise us?"]
    },
    "Bazza": {
        "purpose": "practical grounding",
        "questions": ["What is actually supported?", "What is hand-waving?", "What is the smallest useful next step?"]
    },
    "Wizard": {
        "purpose": "system and world modelling",
        "questions": ["What components and feedback loops exist?", "What state must persist?", "What would make the model internally inconsistent?"]
    },
}

@dataclass
class Assessment:
    pass_number: int
    profile: str
    role: str
    question: str
    observation: str
    evidence_status: str
    source_hash: str
    parent_ids: list[str]
    assessment_id: str

@dataclass
class ReviewResult:
    input_hash: str
    assessments: list[Assessment]
    disagreements: list[dict[str, str]]
    synthesis: dict[str, Any]
    stop_reason: str
    limitations: list[str]

class Backend(Protocol):
    def assess(self, text: str, profile: str, pass_number: int, prior: list[Assessment]) -> list[tuple[str, str, str]]: ...

class TransparentDemoBackend:
    """Rule-based orchestration test backend. Never presents generated text as fact."""
    def assess(self, text: str, profile: str, pass_number: int, prior: list[Assessment]) -> list[tuple[str, str, str]]:
        low = text.lower()
        questions = PROFILES[profile]["questions"]
        if pass_number == 1:
            if profile == "Junkrat":
                observations = [
                    "Alternative hypothesis: the key variable may be the orchestration process, not the named personas.",
                    "Assumption to challenge: repeated passes do not automatically improve accuracy.",
                    "Discriminating test: compare single-pass and multi-pass outputs on held-out tasks."
                ]
            elif profile == "Bazza":
                observations = [
                    "Supported only as a design proposal; no performance evidence has been shown yet.",
                    "Potential hand-wave: calling the process self-improving without measured improvement.",
                    "Smallest useful step: implement a traceable prototype and run baseline tests."
                ]
            else:
                observations = [
                    "Model: profiles generate candidate interpretations; an evaluator compares and gates them.",
                    "Persistent state should include claims, provenance, versions, failures and test outcomes.",
                    "Consistency risk: the evaluator may share the generator's blind spots."
                ]
        elif pass_number == 2:
            observations = [
                f"Challenge from pass 1: {profile} output must be treated as a candidate, not a verdict.",
                "Cross-check: independent agreement is weaker if branches share prompts, context or model biases.",
                "Require an external test or explicit human decision before changing persistent state."
            ]
        else:
            observations = [
                "Meta-review: distinguish useful orchestration from demonstrated reasoning improvement.",
                "Remaining uncertainty: this demo backend is rule-based and cannot judge semantic correctness.",
                "Next experiment: plug in a model backend, freeze a benchmark, score blind and compare ablations."
            ]
        # Keep the original text relevant in the trace without pretending to interpret it deeply.
        if not text.strip():
            return [(questions[0], "Empty input: no meaningful assessment possible.", "insufficient_input")]
        return [(q, obs, "design_hypothesis" if "hypothesis" in obs.lower() or "risk" in obs.lower() or "uncertainty" in obs.lower() else "unverified_assessment") for q, obs in zip(questions, observations)]

class RecursiveReview:
    def __init__(self, backend: Backend | None = None):
        self.backend = backend or TransparentDemoBackend()

    @staticmethod
    def _id(*parts: str) -> str:
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:14]

    def run(self, text: str) -> ReviewResult:
        source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assessments: list[Assessment] = []
        # Three passes over the same three profiles: 3 x 3 evaluations.
        for pass_number in (1, 2, 3):
            for profile, spec in PROFILES.items():
                prior = list(assessments)
                rows = self.backend.assess(text, profile, pass_number, prior)
                parents = [a.assessment_id for a in prior[-3:]] if pass_number > 1 else []
                for index, (question, observation, status) in enumerate(rows):
                    aid = self._id(source_hash, str(pass_number), profile, str(index), observation)
                    assessments.append(Assessment(pass_number, profile, spec["purpose"], question, observation, status, source_hash, parents, aid))
        # This is a disagreement ledger, not a semantic contradiction detector.
        disagreement = [{"topic": "agreement_vs_independence", "finding": "Nine evaluations share one source and the same demo backend; their agreement is not independent evidence."},
                        {"topic": "self_evaluation", "finding": "A system evaluating its own output can reproduce its own blind spots; external benchmarks are required."}]
        synthesis = {
            "central_result": "The architecture can be tested as an orchestration process, but this demo does not prove improved reasoning.",
            "candidate_invariants": ["No hypothesis becomes fact by repetition.", "Every assessment keeps source and parent lineage.", "Persistent changes require external evidence or explicit human approval."],
            "next_experiment": "Run the same held-out task set with one pass, three passes, and three passes plus an independent evaluator; compare blind-scored accuracy, calibration, cost and latency.",
            "auto_mutation": False,
            "pass_count": 3,
            "profile_count": len(PROFILES),
            "assessment_count": len(assessments),
        }
        return ReviewResult(source_hash, assessments, disagreement, synthesis,
                            "Stopped after three passes: further iteration is not justified without measured value.",
                            ["The bundled backend is deterministic and rule-based, not an LLM.", "No claim of model self-modification, sentience, or proven accuracy gain.", "The disagreement list is a predefined risk register, not automatic semantic detection."])

def to_dict(result: ReviewResult) -> dict[str, Any]:
    return {"input_hash": result.input_hash, "assessments": [asdict(a) for a in result.assessments],
            "disagreements": result.disagreements, "synthesis": result.synthesis,
            "stop_reason": result.stop_reason, "limitations": result.limitations}
