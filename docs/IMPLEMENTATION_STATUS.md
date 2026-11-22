# Implementation status — IXO uv foundation v0.1

## VERIFIED against this archive, not just a design document

- `uv lock --offline --python 3.13` and `uv sync --offline --python 3.13` complete in the test environment (uv 0.10.0; CPython 3.13.5). The `.python-version` pin is 3.11 for ordinary users; the pinned Python was not available offline in the test container.
- `uv run --offline --python 3.13 python -m unittest discover -s tests -v`: **103 passing** tests, including original IXO tests, inherited FrameShift unittest suite, and new integration checks.
- `ixo_foundation` CLI creates actual files on disk (`ixo.sqlite3`, `aixo.sqlite3`) and survives independent process invocations.
- Case command produces four committed IXO events, one pending Hermes proposal, one AIXO experiment, four captured events, and zero new durable facts.
- AIXO evaluates an operator-supplied expectation against an IXO snapshot. No LLM or self-scoring agent.
- Bridge rejects a second IXO source, changed/replayed event content, and legacy unbound capture state; capture is idempotent.

## Partial / deliberately restricted

- Hermes proposal overlap policy is conservative and fails closed on ambiguous overlap; original Mark 12 classifier/constitutional rules still require a direct code migration.
- Moon2 is a staged text ledger; **not** an agent or automatic interpreter. The case hypothesis comes from the human operator.
- AIXO course consists of eleven lessons inherited from the v0.4 package; broader roadmap/course content is not represented as completed learning.
- FrameShift is kept as a research-only standalone Python module; its judgment heuristic has transparent tests, not independent proof of intelligence.
- Optional `ixo.server` and `web/` are legacy carry-overs. The primary product entry point is Python CLI, not HTML.
- Schema v1 is preserved with additive settings; no generalized migration system exists.

## Missing, not disguised as implemented

- Spatial/VR/3D compositor; OS application lifecycle; native Windows desktop integration.
- Any autonomous model or independent evaluator; model calls, self-modifying code, learned weights.
- Full historical Hermes Mark 12 semantics and all original source-backed invariants.
- Multi-database distributed transaction; multi-source AIXO evidence; API/plugin integration to AegisLo0m, Kova, Haven or the physical rig.

## Next proper engineering milestones

1. Compare archived Hermes Mark 12 *source* and contracts against the current conservative Hermes implementation; migrate one tested invariant at a time without breaking the write gate.
2. Introduce explicit typed ports to remove component `__getattr__` delegation to the entire runtime.
3. Link case records to source-event spans and experimental outcomes, with recovery for cross-database partial failures.
4. Add a read-only spatial projection adapter only after authoritative state/commands are stable; the viewer must never own fact writes.
5. Establish held-out tasks, independent outcome labels, and rollback rules before FrameShift heuristics can influence decisions.

**Release policy:** a capability only moves from proposed to implemented when its source path, test, and observed runtime behavior are recorded.
