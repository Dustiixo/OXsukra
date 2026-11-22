# HERMES router contract: automation as safe home-automation-style control plane

**v0.4 addition:** An independent metadata-purpose contract now exists in `contracts/hermes-purpose.v1.json`. Its Java client and human-approved taxonomy are documented in `PURPOSE_FIRST_ARCHITECTURE.md`. This does not enable any of the external workflow executions described below.

**Implemented in v0.2:** descriptive capability registry, authenticated safe preview, explicit metadata-only event records, disclosure version check, web dashboard preview and integration review. **Not implemented:** executing workflows, playing music, controlling third-party bots, cron schedules, private business ACLs, AI autonomy, VPS deployment.

## Event path

```
Discord / local program / human
          |
          v
   Intent / event type
          |
   disclosure + auth check
          |
          v
   HERMES route PREVIEW ----> shows every intended adapter and permission gate
          |
     explicit record
          |
          v
  append-only event record in SQLite (recorded_unexecuted)

 FUTURE GATES (NOT BUILT):
 Signed source -> permissioned rule -> durable job -> leased worker
     -> result + evidence -> audit receipt -> Discord notice
```

API (all except `/health` require a Bearer token):

```
GET  /api/v1/integrations           # manifest, with states / restrictions
GET  /api/v1/disclosure            # machine-readable transparency notice
GET  /api/v1/automation/types      # allowlisted event types
POST /api/v1/automation/preview    {"event_type":"music.requested"}
GET  /api/v1/automation/events     # recorded event metadata; member/admin only
POST /api/v1/automation/events     # requires v0.2 acknowledgement
```

Example recording payload (no action is executed):

```json
{
  "event_type": "experiment.proposed",
  "project": "ixo",
  "summary": "Compare two locally generated test results",
  "disclosure_version": "HERMES-DISCLOSURE-0.2",
  "acknowledged": true
}
```

### Module-state vocabulary

- `implemented`: functionality exercised in local tests, not a production service guarantee.
- `adapter_included_not_live`: code provided; live third-party credentials and end-to-end test pending.
- `optional_adapter_included`: optional adapter code provided; needs configuration.
- `export_implemented`: an export API exists, not two-way sync.
- `external_manual`: third-party feature is standalone; no HERMES remote control.
- `proposed`: researched/planned, NOT implemented.
- `proposed_private`: should not receive confidential material until scoped authorization exists.

### Future worker isolation before enabling automation

- Signed event origin and short-lived scoped adapter credentials.
- Separate queues for low-trust uploads, approved knowledge extraction and trusted code CI.
- Files remain inert by default. Untrusted archive inspection needs strict resource limits.
- Command allowlists and human approval for outbound copies, irreversible changes, publication and spending.
- Rate limits, quotas, retention, deletion, project ACLs, backups and tested restores.
- Idempotency keys for cross-system events, retry state machine and dead-letter queue.
- No bot impersonation or broad Administrator permission solely for convenience.
- Opt-in and disclosure for recordings, voice/transcripts, personal data and new model destinations.
- AI generated notes use traceable sources and independent validation; models never silently promote their own output.

### Relation to local-first architecture

Each collaborator can keep local machines, models, and code repos independent. The shared hub brokers *permissioned artifacts and events*, not hidden access to every local filesystem. A future consented local node may volunteer computing capabilities with its own job budgets. Remote execution is not part of this version.
