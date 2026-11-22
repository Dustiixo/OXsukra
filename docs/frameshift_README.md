# FrameShift Lab v0.4 — Recursive Linguistic Construct Workbench

FrameShift is an experiment in **recursive, inspectable reasoning orchestration**. It is not a claim of sentience or self-modification.

## What changed in v0.4

- Refocuses the workbench on linguistics, algebra, cryptanalysis, and reconstructing how a solution is constructed.
- Adds transparent text probes: tokenization, line/word initials, word lengths, repetition, and A1Z26 letter sums.
- Adds exhaustive Caesar-shift enumeration and candidate transformation generation.
- Adds a safe, restricted linear-equation solver using Python AST parsing (no `eval`; nonlinear expressions rejected).
- Adds tests for false certainty warnings, equation verification, and rejecting code execution.

## What changed in v0.2

- Applies a three-pass process to the same three profiles: **Junkrat** (divergence), **Bazza** (grounding), **Wizard** (system modelling).
- Records 27 assessment artefacts (3 questions × 3 profiles × 3 passes), with source hashes and parent lineage.
- Produces a synthesis, explicit uncertainty/limitations, and a stopping reason.
- Adds prompt contracts for a future LLM backend and an independent evaluator.
- Includes a written self-application report that critiques the previous architecture proposal.
- Preserves v0.1's event ledger and explicit evidence gate.

**Important:** the included backend is deterministic and rule-based. It tests orchestration, lineage, and guardrails. It is not a language model and does not prove improved reasoning. No network calls, cloud dependencies, or third-party packages are required.

## Run

Requires Python 3.10+.

```bash
python -m frameshift review "How could recursive reasoning improve its own methods?"
python -m frameshift lingua "Find every clue"
python -m frameshift construct $'Find\nEvery\nClue'
python -m frameshift equation '2*(x+3)=14'
python -m frameshift caesar 'Khoor, Zruog'
python -m frameshift inspect
python -m unittest discover -s tests -v
```

State defaults to `./data/events.jsonl`; set `FRAMESHIFT_HOME=/path/to/folder` to change the ledger location.

## v0.3 — Junkrat recursive attack lab

`python -m frameshift junkrat --rounds 3 --out JUNKRAT_AUDIT.md` runs 10 adversarial attack patterns across three fold-back rounds (30 audit records). It probes consensus laundering, lineage loss, evaluator mirroring, runaway recursion, state poisoning, correlated votes, metric gaming, profile collapse, unreviewed patches and recursive blind spots. Later rounds attack the assumptions behind earlier findings.

This is deliberately bounded static red-teaming, not arbitrary code execution or autonomous source mutation. A “resisted” result means a source-level guard indicator was found, not that the system is proven safe. Candidate patches require reproducible tests and human review.

## Architecture

1. **Pass 1 — independent proposals:** each profile evaluates the original input.
2. **Pass 2 — cross-challenge:** profiles challenge assumptions and review prior artefacts.
3. **Pass 3 — meta-review:** the process examines its own evaluation risks, evidence gaps and stopping condition.
4. **Synthesis:** emits candidate invariants and the next experiment; does not mutate persistent canon.
5. **Evidence gate:** existing state claims remain hypotheses until explicit, evidence-bearing confirmation.

## Next serious experiment

Replace `TransparentDemoBackend` with an LLM adapter implementing the `Backend` protocol. Keep first-pass responses hidden from other profiles until recorded. Then evaluate against a frozen held-out task set with answer keys or external outcomes. Compare:

- A: one-pass baseline
- B: three profile passes
- C: three profile passes + independent blind evaluator

Pre-register scoring for accuracy, calibration, counterexample handling, latency and cost. Do not treat consensus or verbosity as correctness. Adopt a new method only if it beats the baseline on held-out tasks and passes regression tests.

## Linguistic construct focus

See `LINGUISTIC_CONSTRUCT.md` for the domain method and current limits. The current tools generate candidates; they do not establish that a text contains a hidden message. A transformation must be justified by a clue or constraint and checked against competing explanations.

## Project boundaries

- This program cannot change ChatGPT's underlying model weights or inspect hidden internal reasoning.
- A future backend can orchestrate model calls; that is different from a model autonomously rewriting itself.
- Keep this experiment separate from IXO core until repeatable evidence justifies integration.
- Review third-party licences before reusing any external repository code. This prototype does not copy their implementations.

See `SELF_APPLICATION.md`, `RESEARCH_NOTES.md`, and `frameshift/prompts.py`.

## v0.5 — Asymmetric bilateral abduction

Adds `frameshift.asymmetric`: a bounded research probe in which **Construct** generates competing transformations and **Attack** applies unequal evidence standards. Explicit clues can support an operation; a matching expected answer without a clue is labelled `target_match_without_clue`, not promoted. The tiny phonetic-boundary probe preserves the competing readings “I scream” / “ice cream” when the clue explicitly points toward sound and segmentation.

```bash
python -m frameshift asymmetric --text $'Find\nEvery\nClue' --clue 'Take the first letter of each line'
python -m pytest -q
```

See `ASYMMETRIC_ABDUCTION.md` and `BENCHMARK_RESULTS.md`. Scores are heuristic, not probabilities. The implementation is deterministic and does not establish a general reasoning improvement.

## Self-distillation into judgment (v0.6 prototype)

`frameshift.judgment` adds an evidence-grounded judgment layer. It scores recorded decisions using verified outcomes, evidence, confidence calibration, efficiency, and a reversibility penalty; compares strategies across episodes; and promotes candidate rules only when held-out validation passes. See `SELF_DISTILLATION.md` and run `PYTHONPATH=. python examples_self_distill.py`.

This is inspectable policy/method distillation, not model-weight training. Scores are provisional heuristics and require independent outcome verification; passing tests does not establish general intelligence or real-world improvement.
