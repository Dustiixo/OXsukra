# FrameShift v0.5 — Asymmetric Bilateral Abduction

## Research question
Can two unequal reasoning paths discover a linguistic construction more reliably than unranked transformation enumeration?

## Implemented hypothesis
- **Path A / Construct:** enumerate candidate interpretations and transformations.
- **Path B / Attack:** require explicit clue support, compare a control transformation, and check optional external constraints. B is not a second vote.
- **Bilateral ambiguity:** retain multiple readings (currently a deliberately tiny `I scream` / `ice cream` boundary demonstration) until evidence differentiates them.
- **Asymmetry:** clue support can promote a candidate; unsupported transformations incur a penalty. A target match without a clue is explicitly labelled as possible benchmark leakage, not a discovery.
- **Recursive fold-back:** intentionally bounded to one proposal/attack cycle. A later pass is justified only by a new falsifiable constraint, not by wanting more iterations.

## Reproduce
From this folder:

```bash
python -m pytest -q
python -m frameshift asymmetric --text $'Find\nEvery\nClue' --clue 'Take the first letter of each line' --expected FEC
```

## Initial test protocol
The included tests cover a clue-grounded line acrostic, word initials, a phonetic-boundary ambiguity, an unconstrained negative control, a target-only trap, and unsupported Caesar enumeration. The benchmark `expected` field is evaluator-only information; it must never be passed to the proposal path in a future model-backed evaluation.

## Known limits
This is a deterministic mechanism probe, not a semantic model. The score is a transparent heuristic, not a probability. Phonetic ambiguity is a tiny hand-coded example, not general phonology. Tests establish behavior of the code, not a general intelligence gain. A proper next experiment needs a frozen held-out set with adversarially matched controls and blind scoring.
