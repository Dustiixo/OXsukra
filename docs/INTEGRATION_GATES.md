# FlowMesh integration gates | from isolated proof toward IXO

No stage is complete unless its acceptance evidence exists. Source tree may not be the current authoritative IXO repository.

| Gate | Build | Measurable acceptance | Status |
|---|---|---|---|
| F00 | Independent FlowMesh proof and portable package | Fresh ZIP extraction, automated tests, demo, ledger/source hash verification, GUI smoke | **Container-tested** |
| F01 | Verify owner's Windows/Ubuntu hosts | Read-only inventory of Python, Ollama, model memory, local IXO repo path, branch/commit, backups | **Host pending** |
| F02 | Real local LLM orchestration | Use existing Ollama model; verify 2 concurrent prompts, timeouts, model miss, instruction revisions during inference and visible agent output | **Adapter implemented / live host unverified** |
| F03 | Evidence adapters | Search only approved local corpus first; add optional external research source with provenance and request budgets, without automatic action authority | **Not built** |
| F04 | FocusGate shared event contract | Versioned typed envelopes with expected actor, event timestamp, work item, source id, capability permission, replay and rollback handling | **Proposed; not integrated** |
| F05 | Temporal UI integration | Generation branches presented as tabs attached to one parent; prompt revisions and actual work events remain on separate timelines | **Local preview tested; actual IXO integration pending** |
| F06 | Bounded real action broker | Human-reviewed capabilities with testing and independent readback; no tool may execute from raw research text | **Not built** |
| F07 | WITNESS / Foundry receipts | Independent source hash retention, external timestamp anchor if required, reproducible restores | **Not built** |
| F08 | STRAY optional reader | Read-only exported evidence fed to independent STRAY; Moon2 reflects inside STRAY; no agent permissions inherited | **Not built** |

## Rules for integration

1. First identify and preserve the existing canonical repos and backups. Do not `git reset`, clean, force-push, format a drive or mutate existing source based on this ZIP.
2. Keep one **owner** for each source of truth. FlowMesh owns its scheduling session, FocusGate owns its existing capability/event ledger, VELA owns media/MIDI state, and STRAY remains separate.
3. A proposed operation cannot execute until the destination broker validates *actor*, *capability*, *scope*, *context version*, *permission*, *timeout*, and *rollback/compensation*.
4. An unverified LLM conclusion can request research but cannot certify the correctness of a source, raise execution privileges, or access a tool.
5. Measure actual cost/latency. Only then consider GPU residency, agent concurrency, SIMD/compiled scheduling, or kernel-adjacent work.
6. A promoted capability must be independently verifiable and reversible where possible. External side effects require different compensation rules.
