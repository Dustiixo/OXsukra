# OX Funnel + HERMES v0.2 - verification record

Date: 2026-11-12. Tests run against freshly extracted v0.1 code extended in-place to v0.2 (no network credentials).

`python -m unittest discover -s tests -q`: **12 tests PASS** (the original 9 tests plus 3 new control-plane tests).

New gate checks:
- `GET /api/v1/integrations` and `/api/v1/disclosure` require authentication, label future/manual integrations honestly, and include current disclosure version.
- `POST /api/v1/automation/preview` returns a nonexecuting route. Invalid event types rejected; metadata preview never issues a webhook or creates a processing job.
- `POST /api/v1/automation/events` rejects missing/stale disclosure acknowledgement, unknown payload fields, and write attempts from the bot principal; approved test record remains `recorded_unexecuted` and creates no real processing job or outbound notification.
- Python package compiled successfully; static HTML dashboard contains route and policy controls.

**Not independently verified:** live Discord bot registration/interaction, external music playback or source licensing, real Google Drive storage, actual VPS, project-permission isolation, automatic deletion, and any remote computing. The router is intentionally **preview/record only**, not an execution engine. Do not deploy the unmodified private hub on the public Internet.

---

# OX Funnel v0.1 - verification record

Date: 2026-11-12

Command: `python -m unittest discover -s tests -v`

**Result:** 9 tests, all passed (Python 3.13, local temporary loopback server, no external credentials).

Covered:

1. HTTP liveness, rejecting missing/invalid bearer tokens, restricted bot permissions.
2. Creating upload sessions, interrupt/resume offsets, refusing offset conflicts, and end-to-end content download.
3. SHA-256 mismatch rejection before admitting a file.
4. Deduplicating identical blob content while keeping distinct artifact records.
5. Proposed knowledge notes, searchable records, single-note Markdown and all-notes Obsidian ZIP exports.
6. ZIP metadata indexing without extraction or executing user code.
7. Rejecting invalid project slugs, enforcing admin-only retries and bot size limits.
8. Real local client upload of a file above 4 MiB (multi-chunk), then local-model retrieval against a simulated localhost Ollama API. The local model invocation was **stubbed**, not a real LLM inference run.
9. Recovery from a crash between moving a file into hashed storage and committing its database record.
10. rclone Drive mirror command construction and visible failure handling using **mocked subprocess output**, not a live Drive connection.

Note: The test suite contains **9 test cases**; several cases cover multiple assertions and scenarios.

Not yet live-tested: Discord bot authorization and registration against a real guild, Google OAuth/rclone upload against an actual Google Drive, Docker build, actual four-machine LAN/VPN operation, a real local Ollama model, and restore from backup. Those are the next deployment gates, not claimed results.

Use `python -m unittest discover -s tests -v` on your own machine to reproduce core checks.
