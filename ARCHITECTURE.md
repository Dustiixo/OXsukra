# OX Funnel: system contract and development gates

## Design intent

Discord remains the normal social/hangout interface. Four developers run a common local intake program that can send files (including large ones) to one shared authenticated hub. The hub owns the durable manifest, processing queue and searchable knowledge index. An optional bot named HERMES publishes status and receives explicit Discord commands. Optional rclone mirrors verified blobs into the team's Google Drive. Each developer's local model can *read the same approved/indexed sources* through the API instead of each model maintaining an unrelated memory copy.

**Ownership boundary:** IXO, Syntra and APC/Odin remain independent systems. The funnel coordinates **artifacts, records, permissions and jobs**, not their internals. A plug-in/adapter may be added without allowing raw uploaded code to execute.

## Authority and data path

```
 FOUR PEOPLE (each retains local originals)
    | local GUI / watched folder / CLI / localhost Ollama annotation
    v
 HTTPS or private VPN    Discord manual upload -> /funnel_ingest [explicit, <= 25 MiB]
    |                                   |
    +-----------------------------------+
                     v
             HUB :8787 (REST)
              bearer identity
                     v
     RESUMABLE SESSION / SHA-256 CHECK
                     v
      CONTENT-ADDRESSED LOCAL BLOBS
                     v
         SQLITE MANIFEST + JOBS <----> DASHBOARD / HERMES
                     |
        safe text/ZIP-name indexing
                     |
        +------------+-------------+
        |            |             |
        v            v             v
     SEARCH      KNOWLEDGE      rclone copyto
     /items      /notes         Google Drive
        |            |
        +------+-----+
               |
          local Ollama `ask`        (read-only model retrieval)
          Obsidian markdown export (explicit download)
```

The processing queue executes an allowlisted **metadata indexer** and optionally the administrator-configured `rclone` binary. It never executes scripts found in uploaded projects or asks an LLM to run them.

## Standardized record

Artifacts include `id`, `name`, `project`, `actor`, `size`, `sha256`, `created`, `annotation`, `preview`. Jobs include `id`, `item_id`, `status`, `error`, `mirror`, and timestamps. Upload sessions include `id`, `actor`, `size`, `sha256`, `offset`, `state`. Notes include `id`, `author`, `title`, `body`, `project`, `item_id`, `state=proposed`.

Public IDs are random 96-bit hex strings. Files are immutable SHA-256-addressed objects. Multiple source filenames may reference the same blob without duplicating bytes. Project names are slugs, **not access boundaries** in v0.1.

## State transitions

```
UPLOAD     open -> complete (or remains open on mismatch)
JOB        queued -> processing -> done
                              \-> failed -> queued (admin retry)
KNOWLEDGE  proposed (no autonomous promotion in this gate)
```

Upload chunks are 4 MiB maximum. The server writes + fsyncs each accepted chunk before acknowledging the new byte offset. A dropped connection can use the previously issued session ID to resume. On finalization, the hub recomputes SHA-256. If a crash occurs between moving a blob and committing its artifact row, the completion operation can recover from the existing verified blob. The server requeues jobs left in `processing` after restart.

**Not yet addressed:** expiry/garbage collection for abandoned partial uploads, rotating revoked keys, distributed-worker leasing, multi-instance hub concurrency, large user counts, public-facing DDoS protection, direct-to-Google-Drive streaming, resumable read downloads and sophisticated conflict resolution.

## Security requirements before real team onboarding

1. Keep hub private. For remote machines prefer Tailscale/Headscale or a correctly configured HTTPS reverse proxy. Never put the raw HTTP port on the public internet.
2. Hand each member their own member token. Use a separate HERMES bot token. Do not put secrets in GitHub, Discord channels, screenshots or project files.
3. Keep `vault/` and the rclone credential store private. Backup the database *and* content-addressed `blobs/`; a Drive mirror alone does not back up all metadata.
4. First team deployment should use harmless test files and verify checksum match, queue completion, archive retrieval, power-failure recovery, multi-member access and backup restore.
5. If private business files ever coexist with general development files, implement real project-level authorization before using the same hub; slugs alone do not isolate access.
6. LLM annotations and proposed notes are untrusted outputs; record source IDs and require explicit human verification before promoting them into project specifications or business decisions.
7. Discord bot commands are restricted by guild ID and individual allowlisted Discord user IDs. The bot uses application commands, not user-account tokens or chat scraping.

## Future adapters and acceptance gates

- **Google Drive:** real rclone copy, compare remote size/checksum where supported, apply service-account access controls, test Drive outages/retries. Current prototype tests the local queue and adapter boundary, not a live Google account.
- **Obsidian:** extract `obsidian-export` ZIP into a designated vault; later add one-way git/sync with conflict handling and explicit edit ownership.
- **Alchemy:** models may submit *proposals* backed by source IDs; independent validators and human reviewers determine promotion. Avoid cyclic agent self-approval.
- **Business Intentions:** separate permissions and workflow states (`idea -> reviewed -> active -> retired`) with owners and evidence; not yet implemented.
- **VPS dashboard:** better rate limits, proper reverse proxy, quotas, access audit log, configurable retention, restore drills and monitored health checks before internet use.

## Integration boundary for independent systems

An adapter should authenticate with a scoped service identity (not yet implemented), query `/api/v1/search`, resolve source IDs, fetch metadata from `/api/v1/items/{id}`, and create `proposed` notes via `/api/v1/notes`. No program receives arbitrary remote shell access by default. For v0.1 all member tokens have shared workspace access. Each team member can independently assess the ZIP without changing their existing projects.


## v0.2 HERMES automations and disclosure

The v0.1 intake/queue is unchanged. New module `funnel/automation.py` publishes an *honest* provider capability catalog (states distinguish actual code from ideas, manual third-party bots and unconnected adapters) and a small allowlisted event router. The route preview enumerates planned steps without executing them; explicit event recording requires current `HERMES-DISCLOSURE-0.2` acknowledgement and stores up to 300 characters of human-supplied summary in SQLite as `recorded_unexecuted`. There are no arbitrary shell, remote execution, music playback or cross-bot APIs. Bot service identity can PREVIEW routes but cannot write events or enumerate private event logs.

The dashboard provides interactive preview and event-record controls, and a read-only integration catalogue. For user-facing and per-upload policy see `GROUP_DISCLOSURE_TEMPLATE.md`. For future execution engine boundaries see `HERMES_ROUTER_CONTRACT.md`. Rights and permissions for music and third-party apps are separate from our hub and must be reviewed at install time.
