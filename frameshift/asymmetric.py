"""Asymmetric bilateral abductive reasoning prototype.

A proposes constructions; B attacks their justification. B is not a second vote:
unsupported transformations are penalized, controls are compared, and explicit
constraints dominate aesthetic/semantic plausibility. All outputs are inspectable.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import re
from .construct import analyze_text, caesar, words

CLUE_RULES = {
    "line-initials": (r"\b(first|initial|beginning|starts?|opening)\b.*\b(line|row|sentence)s?\b|\b(line|row)s?\b.*\b(first|initial|beginning|starts?)\b", "explicit line-initial clue"),
    "word-initials": (r"\b(first|initial|beginning|starts?|opening)\b.*\b(word|each word)s?\b|\b(acrostic|initials)\b", "explicit word-initial clue"),
    "word-finals": (r"\b(last|final|ending|ends?)\b.*\b(word|letter|each)\b|\b(last letters?)\b", "explicit ending clue"),
    "reverse-letters": (r"\b(reverse|backwards|backward|upside down|mirror)\b", "explicit reversal clue"),
    "caesar": (r"\b(shift|caesar|rotate|rot\s*\d+)\b", "explicit shift clue"),
    "word-lengths": (r"\b(length|lengths|number of letters|count the letters)\b", "explicit length clue"),
    "phonetic-boundary": (r"\b(sound alike|sounds like|homophone|hear|spoken|phonetic|say it aloud|word boundary)\b", "explicit phonetic clue"),
}

@dataclass
class Hypothesis:
    operation: str
    result: Any
    clue_support: float
    constraint_fit: float
    control_distinctiveness: float
    attack_penalty: float
    score: float
    explanation: str
    status: str

    def as_dict(self): return asdict(self)


def _compact_letters(s: str) -> str:
    return ''.join(c.upper() for c in s if c.isalpha())


def _candidate_map(text: str) -> list[tuple[str, Any]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    toks = words(text)
    compact = _compact_letters(text)
    candidates: list[tuple[str, Any]] = []
    if len(lines) >= 2:
        candidates.append(("line-initials", ''.join(next((c.upper() for c in line if c.isalpha()), '') for line in lines)))
        candidates.append(("line-finals", ''.join(next((c.upper() for c in line[::-1] if c.isalpha()), '') for line in lines)))
    if len(toks) >= 2:
        candidates.append(("word-initials", ''.join(w[0].upper() for w in toks)))
        candidates.append(("word-finals", ''.join(w[-1].upper() for w in toks)))
        candidates.append(("word-lengths", [len(re.sub(r'[^A-Za-z]', '', w)) for w in toks]))
    if compact:
        candidates.append(("reverse-letters", compact[::-1]))
        candidates.extend(("caesar", {"shift": s, "text": caesar(compact, s)}) for s in range(1, 26))
    # Deliberately tiny explicit pronunciation/boundary probe, not a phonetic model.
    low = re.sub(r'[^a-z ]', '', text.lower())
    if "i scream" in low or "ice cream" in low:
        candidates.append(("phonetic-boundary", {"reading_a": "I scream", "reading_b": "ice cream", "shared_sound_approximation": "aisk्रीम".replace("्रीम", "ream")}))
    return candidates


def _control_signature(text: str, operation: str) -> Any:
    """Run same operation on a simple control; exposes transformations that always fit."""
    control = "Ordinary words carry no secret\nNothing here is a clue"
    lines = [line.strip() for line in control.splitlines() if line.strip()]
    toks = words(control)
    compact = _compact_letters(control)
    if operation == "line-initials": return ''.join(next((c.upper() for c in x if c.isalpha()), '') for x in lines)
    if operation == "line-finals": return ''.join(next((c.upper() for c in x[::-1] if c.isalpha()), '') for x in lines)
    if operation == "word-initials": return ''.join(w[0].upper() for w in toks)
    if operation == "word-finals": return ''.join(w[-1].upper() for w in toks)
    if operation == "word-lengths": return [len(re.sub(r'[^A-Za-z]', '', w)) for w in toks]
    if operation == "reverse-letters": return compact[::-1]
    if operation == "caesar": return {"shift": 1, "text": caesar(compact, 1)}
    return None


def solve(text: str, *, clue: str = "", expected: str | None = None, max_results: int = 12) -> dict[str, Any]:
    """Run one proposal pass and one asymmetric attack pass; no model calls required.

    `expected` is an optional benchmark/constraint target, not inferred truth.
    Scores are transparent heuristics and should not be interpreted as probabilities.
    """
    if not text.strip():
        return {"input": text, "status": "insufficient_input", "hypotheses": [], "stop_reason": "No text to analyze."}
    combined = f"{clue}\n{text}".strip()
    clue_support_by_op = {}
    for op, (pattern, _) in CLUE_RULES.items():
        if re.search(pattern, clue.lower()): clue_support_by_op[op] = 1.0
    rows = []
    for op, result in _candidate_map(text):
        # A (construct): produce an interpretation and measure explicit clue/target fit.
        clue_support = clue_support_by_op.get(op, 0.0)
        if op == "caesar" and re.search(CLUE_RULES["caesar"][0], clue.lower()): clue_support = 1.0
        result_text = str(result)
        target_fit = 0.0
        if expected is not None:
            target_norm = re.sub(r'[^A-Z0-9]', '', expected.upper())
            result_norm = re.sub(r'[^A-Z0-9]', '', result_text.upper())
            target_fit = 1.0 if target_norm and target_norm in result_norm else 0.0
        # B (attack): penalize unsupported transformation; control always produces output,
        # so it cannot count as positive evidence. A target match without clue remains weak.
        penalty = 0.0 if clue_support else 0.35
        if expected is not None and target_fit and not clue_support:
            penalty += 0.25  # guards against reverse-engineering the expected answer
        control_result = _control_signature(text, op)
        distinctiveness = 0.0 if control_result is None else (0.5 if str(control_result) != str(result) else 0.0)
        score = 0.55 * clue_support + 0.35 * target_fit + 0.10 * distinctiveness - penalty
        if clue_support and (expected is None or target_fit): status = "supported_candidate"
        elif target_fit and not clue_support: status = "target_match_without_clue"
        else: status = "unjustified_candidate"
        explain = ("Clue explicitly supports this operation." if clue_support else "No explicit clue supports this operation; treat as exploratory only.")
        if expected is not None: explain += " Benchmark target was used as a constraint, not as discovered evidence."
        rows.append(Hypothesis(op, result, clue_support, target_fit, distinctiveness, penalty, round(score, 4), explain, status))
    rows.sort(key=lambda h: (h.score, h.clue_support, h.constraint_fit), reverse=True)
    # Keep the full attack trace; rank only affects display order.
    rows = rows[:max_results]
    accepted = [h for h in rows if h.status == "supported_candidate"]
    return {
        "input": text, "clue": clue, "status": "candidate_found" if accepted else "underdetermined",
        "reasoning_model": "asymmetric-bilateral-abduction-v0.5",
        "paths": {
            "A_construct": "Generate competing linguistic/algebraic constructions from the same source.",
            "B_attack": "Challenge unsupported operations, compare a control, and check explicit constraints.",
            "asymmetry": "A proposes; B can penalize or reject. Agreement is not a vote and repetition is not evidence."
        },
        "hypotheses": [h.as_dict() for h in rows],
        "supported": [h.as_dict() for h in accepted],
        "stop_reason": "Stop after one bounded proposal/attack cycle; recurse only when a surviving hypothesis yields a new testable constraint.",
        "limitations": ["Deterministic prototype; no LLM semantics or general phonetic engine.", "Scores are heuristic rankings, not calibrated probabilities.", "A clue can be misread; absence of a candidate does not prove absence of a solution."]
    }
