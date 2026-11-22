# DSOE v0.2 protocol — implemented contract

## 1. State machines

Task: `DRAFT` -> (operator `approve`) -> `APPROVED` -> (`ACCEPTED` all three jobs) -> `COMPLETE`. A rejected job -> `BLOCKED`.

Each job (fixed order): `PENDING` -> (`dispatch`) -> `DISPATCHED` -> (`report`) -> `REPORTED` -> (`review`) -> `ACCEPTED` or `REJECTED`.

`dispatch` is a **file export**. It does **not** execute an external tool. `report` imports an untrusted JSON document and rejects wrong provider/job/request hash; `review` requires a human-provided reason. `evidence` records operator-accepted output in AIXO without Hermes fact promotion.

## 2. Schemas and folder layout

- IXO facts and Moon2: `<home>/ixo.sqlite3`
- AIXO lessons/evaluations/captured external results: `<home>/aixo.sqlite3`
- DSOE tasks/jobs/provenance/trail: `<home>/dsoe/dsoe.sqlite3`
- Handoff envelopes: `<home>/dsoe/outbox/<provider>/<job_id>.json`

Handoff sample:

```json
{
  "request": {
    "protocol": "dsoe-json-file-v1",
    "task_id": "<uuid-hex>",
    "job_id": "<uuid-hex>",
    "ixo_source_id": "<persistent-instance-uuid>",
    "workspace": "main",
    "objective": "Build a reproducible research plan",
    "provider": "pantheonos",
    "stage": "plan",
    "instruction": "Agent-team planning; propose candidate execution structure",
    "constraints": { "no_ixo_fact_writes": true, "no_automatic_tool_execution": true, "untrusted_result_requires_operator_review": true }
  },
  "request_sha256": "<sha256-hex>",
  "accepted_predecessors": [],
  "handoff": "external runtime must implement this protocol; not a native Pantheon API"
}
```

Provider-specific result required fields:

- `pantheonos`: `team_plan`: 1-20 objects with nonblank `title`.
- `odysseus_pantheon`: `workflow`: 1-20 objects with nonblank `title`.
- `duskript_pantheon`: `assessment`: `{verdict: accept|revise|reject, rationale: <text>}`.

All results also require `protocol`, `job_id`, `provider`, `request_sha256`, nonblank `summary` and bounded bytes. Source-match here is **integrity/correlation, not cryptographic authentication**. A malicious actor who can write to the local result file can fabricate responses; external agent credentials and signature support are deliberately **not** included.

## 3. Gating rules

- DSOE can only plan in an active Habitat set; use the existing `set` CLI to activate another set.
- A job cannot dispatch before operator approves task.
- Next stage cannot dispatch before previous result is accepted.
- Accepted result cannot enter AIXO if its source ID is not the active IXO instance.
- AIXO deduplicates evidence by `job_id`, rejects contradictory replays.
- No DSOE/AIXO code calls `Hermes.resolve` or writes IXO's facts table.
- Results are explicitly *operator-accepted evidence*, not verified facts or objectively correct conclusions. Evidence carries `evidence_origin` to distinguish `fixture` from real external records.

## 4. Known limitations / failure handling

- No native upstream agents: handoff protocol must be translated by future adapters.
- Cross-database IXO/DSOE/AIXO atomic commit is not implemented. An interrupted AIXO evidence write can be retried idempotently.
- An outbox file is written before dispatch state is marked; on interruption it may exist while DB job remains PENDING; retrying dispatch checks identical bytes and resumes. Concurrent callers need additional interprocess dispatch locking before production.
- No multiuser ACLs or permission scopes yet; current operator CLI grants ability to approve all task actions.
- Upstream results are only size/type/correlation checked. Model output itself is not independently verified; review is operator judgment.
- Generated fixture reports are clearly marked simulated. Test counts do not establish live AI reasoning performance.

## 5. Component acceptance gates

1. Re-run all prior 103 IXO v0.1 tests unchanged.
2. Test three-pantheon order and provider identity.
3. Test Habitat binding, source ID binding, result hash mismatch, replay and rejection.
4. Restart SQLite and verify task/state survives.
5. Test AIXO evidence deduplication, false source rejection and Hermes fact isolation.
6. Test CLI subprocess entry points and fixture-only full sequence.
