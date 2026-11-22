# HERMES roadmap: concrete acceptance gates

**v0.4 update:** The first adaptive-purpose gate now exists: classify metadata, keep uncertain files in Dump Hub, emit human triage tickets, approve new purposes and teach bounded rules. A Java source client talks to the shared JSON API. This does not satisfy the later ACL, remote worker or live Discord gates.

## Gate 0 - Council / style / consent (NOW)

**Deliverables:** proposal, channel blueprint, filled disclosure, role assignments, selected hub operator and sample-file scope. **Exit:** group acknowledges purpose and data destinations. No live connection required.

## Gate 1 - One machine, one real file

**Exists in code, needs operator smoke test:** Windows BAT install; local hub; GUI/CLI upload; SHA-256, resume, queue, safe text/ZIP listing, dashboard search; export note. **Exit:** uploaded dummy file can be downloaded and byte-for-byte verified; no accidental transmission.

## Gate 2 - Four computers, one private hub

**Needs infrastructure:** private network, tokens per person, independent clients, backup, capacity limits, failed-transfer recovery. **Exit:** 4 authorized clients each submit a test artifact; nonmembers cannot access; admin responsibilities proven.

## Gate 3 - Discord signal layer

**Needs app registration and live testing:** HERMES bot in a test guild; `/funnel_status`, `/funnel_find`, `/funnel_note`, `/funnel_ingest`, `/funnel_route` preview. Optional music/event bot remains independent. **Exit:** bot respects user allowlist and channel permissions; regular chat is not archived.

## Gate 4 - Knowledge and co-reasoning

**Partial now:** local Ollama can annotate selected text; Obsidian export and notes/search already exist. **Still needed:** per-project authorization, consent flags, citations/provenance, revision history, deduped knowledge linking, independent verification gates, deliberative decision records. **Exit:** a discovery links input + outputs + reviewer + test evidence, not just an AI summary.

## Gate 5 - Secure dispatch / voluntary computing

**NOT IMPLEMENTED:** each machine advertises allowlisted capabilities (e.g. tests, rendering, audio processing), worker asks for scoped jobs, operator approves, sandbox limits resources, result gets cryptographic hashes and receipts. **Exit:** nobody gains arbitrary shell access and each worker can leave without affecting the others. Audit workloads for legal and security risks.

## Gate 6 - Business Intentions with actual privacy separation

**NOT SAFE YET:** project-level ACLs, encrypted sensitive storage, contributor license/ownership terms, review of financial/business workflows, deletion, DLP and export approval. **Exit:** confidential work cannot be read or inferred with ordinary shared member credentials.

## Gate 7 - Operations and federation

**Future prospect:** multiple hubs or private VPSs, shared IDs, backup/restore drill, policy-driven replication, adaptive scheduling and permissions-based cross-project intelligence. Keep human controls and evidence attached to each promotion.

## Selected integrations after Gate 2

| Integration | Reason | Now | Next requirement |
|---|---|---|---|
| Discord music/player bot | Social listening | Separate app | Approve source licensing and bot permissions |
| GitHub | Source code/reviews | Concept | Webhook/API tokens with repository scope |
| Google Drive | Asset mirror | Optional rclone adapter | Storage account, shared folder, backup and permissions |
| Obsidian | Knowledge graph | One-way Markdown export | Conflict-safe sync, provenance, ACL |
| Ollama | Local selected annotation/RAG | Optional | Local model and resource budget |
| Intelligence Alchemy | Compare reasoning with evidence | Proposed notes/preview | Reviewer attribution, tests, approval policy |
| Business Intentions | Commercial opportunity review | Channel idea only | Actual access separation and contractual approval |
| VPS | Always-on hub | Docker files | Network/TLS/backup/monitoring/cost approval |
| Agent compute | Distributed tasks | Not implemented | Per-worker approvals, sandbox, durable job lease |

**Design principle:** converge on existing code; new adapters must pass a deliberately small verification gate before promotion.
