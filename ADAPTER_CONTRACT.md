# Minimal shared event / object adapter (PROPOSAL, not installed)

Envelope: `schema`, `event_id`, `source_project`, `source_ref`, `source_sha256`, `created_utc`, `subject_id`, `provenance_kind` (`observed|human_annotation|inference|simulation|correction`), `intent`, `input_refs`, `proposal`, `authorization`, `status` (`proposed|rejected|accepted|applied|failed`), `evidence_refs` and `parent_event_ids`.

- Consumers are read-only by default. Execution requires a separate explicit capability grant.
- A proposal never overwrites original input. A correction records original + corrected interpretation as linked events.
- Cross-project identifiers must remain stable; raw private source does not need to leave the owning program.
- Any remote/commercial AI response stays advisory until tested and approved.
- The schema needs security/design review before use in deployed project APIs.
