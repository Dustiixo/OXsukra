# Self-distillation into judgment (prototype)

## The objective

Hermes should learn to decide whether a *decision process* was smart, rather than awarding itself points for fluent answers. This prototype records an episode, judges it using observable outcome/evidence/calibration/cost/risk signals, compares strategies, and only promotes a distilled rule when repeated support and held-out validation pass thresholds.

## What counts as smart here?

The initial transparent heuristic is:

- 45% verified outcome
- 25% evidence strength
- 20% confidence calibration (Brier-style: `1 - (confidence - outcome)^2`)
- 10% efficiency
- a 0.15 penalty for an irreversible action whose success is unverified

These weights are a testable starting hypothesis, not universal truth or learned weights. `outcome_verified` should come from an independent test/tool/result where possible, not the same generator that proposed the answer. A later version should use task-specific utility, uncertainty intervals, opportunity cost, and multi-objective comparisons rather than one universal score.

## Distillation lifecycle

1. Log an episode with the strategy, confidence recorded before the outcome, evidence strength, cost, reversibility, and failure mode.
2. Compare strategies over multiple episodes.
3. Draft a candidate rule from repeated successes/failures.
4. Test the rule on held-out episodes not used to invent it.
5. Promote only when minimum support, training success, and held-out success thresholds pass.
6. Keep the old policy and record provenance so the change can be rolled back.

The current module implements steps 1, 2, 4, and 5 as deterministic infrastructure. Candidate rule synthesis and automatic policy editing remain deliberately outside this prototype; they should be added only with explicit provenance and regression tests.

## Important limitation

This is **not** model-weight self-training and does not prove general intelligence or autonomous improvement. It is a small, inspectable policy/method distillation layer around an existing model. It can still be gamed by bad labels, correlated evaluators, biased benchmarks, or a metric that rewards the wrong objective. The evaluation source and held-out set are therefore part of the system's trust boundary.

## Run

From this directory:

```bash
PYTHONPATH=. python -m pytest -q
```

The `frameshift.judgment` module provides `Episode`, `JudgmentEngine`, `DistilledRule`, and `EpisodeLedger`.
