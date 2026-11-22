# OX Funnel + HERMES Bridge v0.4: Purpose-first adapter gate

The original v0.2 upload/queue/router system and v0.3 onboarding package are preserved. **New in v0.4:** deterministic per-artifact purpose suggestions; unknown-item triage; admin-reviewed new categories, file requests and keyword corrections; a separate, dependency-free Java client compatible with Syntra, IXO or APC/Odin. The schema lives in `contracts/hermes-purpose.v1.json`; the full demo is in `PURPOSE_FIRST_ARCHITECTURE.md`. No automatic Discord category creation or file execution is implemented.

The included HERMES bot source also adds `/funnel_purpose`, a metadata-only preview command. It requires the same optional Discord registration and live testing as the existing slash commands; no guild installation happened during this build.

This is a human-reviewed, explainable adaptive router—**not** trained intelligence or a private business vault. Do not submit confidential materials. After starting the hub, scroll to the **Adaptive Purpose Funnel** card in the dashboard to try its previews and request forms.

---

## Previous v0.2 core documentation

**New in v0.2:** A Home-Assistant-inspired *capability catalogue*, safe route preview, explicit metadata-only event ledger, web UI controls, and practical member disclosure + per-upload IP/permissions templates. The v0.1 resumable uploader, safe indexer, shared knowledge API, optional Discord bot and optional rclone mirror remain intact.

**Read before live team use:** [`GROUP_DISCLOSURE_TEMPLATE.md`](GROUP_DISCLOSURE_TEMPLATE.md), [`BOT_AND_AUTOMATION_CATALOG.md`](BOT_AND_AUTOMATION_CATALOG.md), and [`HERMES_ROUTER_CONTRACT.md`](HERMES_ROUTER_CONTRACT.md). The templates must be completed by actual operators; **the shared hub still has no per-project permission isolation or automatic deletion**. Do not use it for sensitive business or personal content yet.

**New HERMES optional slash commands:** `/funnel_integrations`, `/funnel_disclosure`, `/funnel_route` (read-only preview). These require the existing bot setup and allowlisted users; they have **not** been tested in a real Discord guild.

### Try the new click-through API

Run the existing hub startup steps, open `http://127.0.0.1:8787/`, and enter your member token. Under **HERMES ROUTER** choose an event and click **Preview routing**. It shows a dry-run action plan, including which external adapters are only proposed. If you read and acknowledge disclosure, **Record event** writes one minimal metadata entry to SQLite (no music played, no other bots commanded, no external automation run). Browse **Integration Registry** and **Disclosure** from the same dashboard.

From the command line with a configured token, the corresponding endpoints are `/api/v1/integrations`, `/api/v1/disclosure`, `/api/v1/automation/types`, `/api/v1/automation/preview`, and `/api/v1/automation/events`.

---

# Core v0.1 engine (retained in v0.2)

A **working, self-hosted four-developer intake prototype**: local file sender + optional local Ollama annotations -> authenticated hub -> durable processing queue -> shared search/knowledge -> optional Google Drive mirror -> Discord notifications and an optional slash-command bot.

No existing IXO/Syntra/APC/Odin project code is assumed. This is a standalone bridge with stable JSON interfaces. **Not a production-hardened multi-tenant file platform.**

## What exists

- **Local app:** file picker desktop GUI (optional drag-and-drop via tkinterdnd2), CLI uploads, and a watched-folder autopiper. SHA-256, chunked/resumable transfer, upload receipts. Source files are never changed.
- **Local LLM (opt-in):** optional short text classification through the local Ollama HTTP API, plus `ask` retrieval over the same shared knowledge/asset index. Nothing is sent to a hosted model. LLM annotations remain unverified labels.
- **Hub:** built-in HTTP API, interactive browser dashboard (`/`), access tokens for four developers plus a restricted Discord-bot identity, SQLite registry, resumable upload sessions, immutable hash-addressed blobs, job queue and search.
- **Processing:** safe text preview indexing and ZIP *listing* only. Uploaded scripts and ZIP content are **never executed or extracted**. Processing runs under the hub's queue worker.
- **Knowledge:** manually created proposed notes (`POST /api/v1/notes`) with optional artifact links, search, and a bundled Obsidian-compatible Markdown ZIP export.
- **Google Drive:** optional **rclone** mirror, executed from the hub when configured. The hub remains the system of record for queue metadata; mirroring failure is visible, not hidden.
- **Discord:** optional outbound webhook notifications; optional `discord.py` bot with `/funnel_status`, `/funnel_queue`, `/funnel_find` `/funnel_note`, and explicit `/funnel_ingest` attachment capture commands. Commands are allowlisted by Discord user ID and return ephemeral responses. No message-content scraping. Explicit `/funnel_ingest` accepts selected Discord attachments up to 25 MiB, while larger files use the local sender.

## Quick run (local smoke test)

Prerequisite: Python 3.10+ (no pip installs needed for hub or client).

```bash
python -m funnel init --data ./vault
python -m funnel hub --data ./vault
```

`init` prints **six fresh one-time tokens** (4 members + bot + admin), and stores only their hashes in `vault/auth.json`. Save these securely. On a separate terminal or another machine:

```bash
python -m funnel client-config --url http://127.0.0.1:8787  # prompts for member token securely
python -m funnel desktop
# OR
python -m funnel upload /path/to/file.zip --project shared
# OR for continuous local intake
python -m funnel watch /path/to/DropFolder --project shared
```

Open `http://127.0.0.1:8787/` in a browser. The dashboard asks for your bearer token; the token stays in that tab's session storage. **Never paste a member token into Discord.**

Use an appropriate URL for the private hub on other computers. Never include tokens in command histories or Discord messages.

`watch` waits for files to stabilize, ignores symlinks, and records successful `(path, size, mtime)` transfers in a local state file. It does not delete or move originals. Restarting the watcher skips previously uploaded unchanged versions.

### Remote team access

The hub defaults to **127.0.0.1** and is *not* exposed to the internet. On a private LAN or Tailscale/Headscale VPN, bind to the VPN/LAN interface with `--host ADDRESS` and use `http://VPN_IP:8787` within that trusted network. For public VPS deployment, place it behind TLS, firewall/rate limiting, backups, and ideally a VPN. **Do not expose the plain-HTTP server publicly.**

Docker example (binds the host's loopback only):

```bash
docker compose up --build -d
```

If initialization hasn't happened yet, run `python -m funnel init --data ./vault` on the host first. Docker is optional. For the Drive-enabled Docker override, configure `RCLONE_CONFIG_DIR` and run `docker compose -f compose.yaml -f compose.drive.yaml up --build -d`. A reverse proxy (Caddy/nginx) and a domain are deployment-specific; there is no claim of zero-config internet exposure.

### Optional Google Drive mirror

Install `rclone` **on the machine running the hub**, configure a Google Drive remote with your own Google credentials/client ID per current rclone guidance, and verify it can access a designated shared folder:

```bash
rclone config
rclone lsd teamdrive:
```

Run the hub with `FUNNEL_RCLONE_REMOTE=teamdrive:OX_Funnel` in its environment. After a verified local upload, the queue worker calls `rclone copyto` without shell interpolation. Optional service credentials must be readable only by the hub user. Mirroring is a **copy**, not a destructive sync.

If the Drive mirror is configured but `rclone` is missing or authentication is invalid, jobs become `failed`; retry them with `POST /api/v1/jobs/{id}/retry` using an admin token. The local blob remains accessible.

**Capacity caveat:** For this first gate, files transit through and remain on the hub's disk. A storage-light VPS with direct-to-cloud multipart uploads, retention/GC, replication, and quotas is a later engineering gate. Do not deploy this version to a VPS with insufficient disk space for incoming large files.

### Optional local Ollama

Use `--ollama MODEL` on an upload. The client reads only a capped excerpt from a known text-file type and sends it to a *local* Ollama server at `http://127.0.0.1:11434/api/generate`. This step is optional and does not execute or trust the returned model text.

```bash
python -m funnel upload README.md --project shared --ollama llama3.2
```

### Ask a local LLM about shared knowledge

If you have Ollama running locally, query the exact same hub records the Discord bot and dashboard read:

```bash
python -m funnel ask "What evidence exists for the IXO / Syntra adapter?" --model llama3.2
# Narrow to one project:
python -m funnel ask "Which implementation risks were found?" --model llama3.2 --project ixo
# Export proposed team knowledge for import into an Obsidian vault:
python -m funnel export-obsidian team-notes.zip
```

This performs a hub text search, fetches a bounded selection of previews and proposed notes, and sends them to **your local** Ollama model. Results show record IDs, remain read-only, and distinguish proposed notes from confirmed facts. This is bounded retrieval, not a full tool-calling agent, and the machine needs a local Ollama installation/model. The Ollama endpoint is restricted to localhost by default and cannot be set to a remote host. It does not cause the hub to execute programs.

### Optional Discord notifications

Give the hub an environment variable `FUNNEL_DISCORD_WEBHOOK_URL` containing an incoming webhook URL for a designated notification channel. Upload and processing events will be posted automatically, with mentions disabled. This webhook is separate from the interactive bot.

### Optional HERMES Discord bot

```bash
python -m pip install -r requirements-bot.txt
```

Set `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`, `DISCORD_ALLOWED_IDS` (comma-separated four user IDs), `FUNNEL_BOT_API_TOKEN` (the hermes-bot token printed by init), and `FUNNEL_HUB_URL`. Start `python -m funnel bot`. The bot uses Discord's **official slash-command** mechanism; it does not access normal chats. `/funnel_ingest` only fetches the attachment the user explicitly selects and routes it through the same checksum/queue/Drive-mirror process. Invite it to your server with `bot` and `applications.commands` scopes, without unnecessary privileged intents.

### API (Bearer authorization)

| Route | Method | Description |
|---|---|---|
| `/health` | GET | Public liveness |
| `/api/v1/status` | GET | Counts and configuration status |
| `/api/v1/uploads` | POST | Create upload session: `{name, size, sha256, project, annotation}` |
| `/api/v1/uploads/{id}` | GET | Resume offset |
| `/api/v1/uploads/{id}/chunk?offset=N` | PATCH | Send next raw chunk, 4 MiB max |
| `/api/v1/uploads/{id}/complete` | POST | Hash-check and enqueue |
| `/api/v1/items` | GET | List artifacts |
| `/api/v1/items/{id}` | GET | Artifact metadata and safe text preview |
| `/api/v1/items/{id}/download` | GET | Download authorized blob |
| `/api/v1/jobs` | GET | Queue and results |
| `/api/v1/jobs/{id}/retry` | POST | Retry failed job, admin only |
| `/api/v1/search?q=term` | GET | Text and metadata search |
| `/api/v1/notes` | GET/POST | Shared knowledge entries |
| `/api/v1/notes/{id}/markdown` | GET | Export single note as Markdown |
| `/api/v1/obsidian-export` | GET | Export the latest 1000 notes as a ZIP of Markdown files |

Only explicitly authorized users can reach protected endpoints. All v0.1 identities share **one workspace**; fine-grained project ACLs, SSO, malware scanners, malware sandboxing, per-user quotas, audit signatures, and high-availability storage **are not implemented**.

## Data layout

```
vault/
  auth.json            # hashed credentials, admin-owned
  funnel.sqlite3       # jobs, sessions, items, knowledge
  partials/             # resumable uploads
  blobs/ab/<sha256>     # immutable local objects
```

## Tests

```bash
python -m unittest discover -s tests -v
```

Integration tests run a real localhost HTTP server with temp SQLite/blob storage and test token authorization, interrupted/resumed upload, checksum verification, deduplication, note search, zip indexing, and job completion. The bot, a real Ollama runtime, and Google Drive mirroring require externally supplied credentials/models and are not claimed end-to-end verified.

## Engineering gates

- **G0 (this ZIP):** local team flow, read/write API, queue, useful bot, cloud-mirror adapter, automated local tests.
- **G1:** authenticated VPN/LAN deployment with 4 actual machines, Discord bot live smoke, Drive mirroring, encrypted restic backup and restore test.
- **G2:** targeted worker assignment to the developers' local models, rights-aware project sharing, batch uploads/direct-to-cloud, storage retention and alerting.
- **G3:** IXO/Syntra/APC/Odin adapters built against the shared item/knowledge API, business-intention stages and explicit human review gates.

No uploads or Discord/GDrive configuration from your real accounts have been performed by this prototype.
