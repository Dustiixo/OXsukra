# FrameShift v0.4 — Linguistic Construct Workbench

The primary domain is **linguistics, algebra, cryptanalysis, and reconstructing the construction of a solution**. It is inspired by fictional clue-solving and hacker-style reverse engineering, but it does not assume ordinary text contains a hidden message.

## Tools

```bash
python -m frameshift lingua "Find every clue"
python -m frameshift construct $'Find\nEvery\nClue'
python -m frameshift equation '2*(x+3)=14'
python -m frameshift caesar 'Khoor, Zruog'
python -m unittest discover -s tests -v
```

- `lingua`: tokenization, line initials, word initials, word lengths, repetition patterns, A1Z26 sums.
- `construct`: produces a transparent list of candidate transformations, including line-initial shifts and reversal.
- `equation`: solves one-variable linear equations using a restricted Python AST parser. It does not use `eval`; nonlinear expressions are rejected.
- `caesar`: enumerates every non-zero Caesar shift rather than asserting a single decode is correct.

## Method: clue → representation → constraints → candidate → verification

1. Preserve the original text and line structure.
2. Produce several possible representations (words, initials, lengths, letter values, algebraic forms).
3. State the clue/constraint that makes a transformation relevant.
4. Generate candidate solutions without silently ranking coincidence as proof.
5. Verify against independent constraints, known context, a control text, or a held-out clue.
6. Record false leads and why they failed; don't silently promote them to facts.

## Current limits

This is a deterministic starter toolkit, not a general natural-language parser, theorem prover, or LLM. A1Z26 and Caesar are examples of conventions, not universal interpretations. A transformation matching a short string may be coincidence. The next serious additions are a typed symbolic-expression graph, grammar/dependency parsing, constraint solving, substitution-cipher scoring with a transparent corpus, and a benchmark suite with answer keys and adversarial decoys.
