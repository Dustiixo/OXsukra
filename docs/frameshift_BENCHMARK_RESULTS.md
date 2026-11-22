# v0.5 smoke-test results

Environment: Python 3.13, deterministic local execution, no external model or network calls.

- `python -m pytest -q`: **33 passed**.
- `python -m unittest discover -s tests -v`: also run as a second test entry point.
- Positive clue case: `Find / Every / Clue` + “Take the first letter of each line” supports `line-initials → FEC`.
- Target-only trap: providing `FEC` without a clue does **not** promote line initials to supported; it is labelled `target_match_without_clue`.
- Negative control: unconstrained ordinary text remains `underdetermined`.
- Phonetic boundary test: preserves `I scream` and `ice cream` as competing readings when the clue explicitly asks for sound-alike / word-boundary reasoning.
- Unsupported Caesar enumeration: candidates are generated but none becomes supported without a shift clue.

Interpretation: tests verify the specified mechanism and its guardrails. They do **not** establish a general accuracy gain over a single reasoner. That requires a frozen, held-out benchmark and comparison against a baseline; this deterministic prototype is not a substitute for a language model.
