# HERMES / OX FUNNEL — WINDOWS v0.8 PILOT

**WINDOWS INSTALLER REPAIR:** If v0.6 reported `FAILED (failures=2, errors=1)` on Python 3.14, read `WINDOWS_REPAIR_v0.8.md`. This revision fixes the test/installer blockers without requiring you to delete `.venv` or `%LOCALAPPDATA%\OX_HERMES`. Start with the two original BATs. Once the local app works, optionally follow `START_TONIGHT.md` for the Discord bridge.

**NEW FOR v0.7:** Start with [`START_TONIGHT.md`](START_TONIGHT.md). The two original BATs below are **unchanged** for the local HERMES app. The extra `03_CONNECT_DISCORD.bat` and `04_OPERATOR_DASHBOARD.bat` are optional live Discord-pilot controls and require an authorized Discord bot/application. This new step does not silently install bots or change server settings. The remainder of this file documents the retained v0.6 local baseline.

**This ZIP is purpose-built for Shane's Windows ASUS.** Discord, Obsidian, Java and existing LLM runners are already installed. The HERMES installer does **not** download, reinstall, modify, automatically connect to or control any of them.

## Two files. In this order.

### 1. `INSTALL_HERMES.bat` — RUN ONCE

1. Unzip the project into a **permanent folder**, not a temporary folder that will be deleted or moved after installation.
2. Double-click `INSTALL_HERMES.bat`.
3. It checks the installed Python version (3.10+), creates a local `.venv` using the already-installed Python, compiles source, runs automated tests and initializes the persistent private HERMES hub.
4. The terminal reports success or a concrete failure. **It does not start the app.**

There is **no pip download, cloud login, Discord operation, Obsidian import, Java install, model download or external upload** in this installer. No administrator privileges are required.

### 2. `OPEN_HERMES.bat` — RUN WHENEVER YOU WANT TO USE HERMES

Double-click it. The native HERMES file-funnel application opens, and its private localhost hub runs while the window is open.

Inside the app:

- **Select files** for explicit, checksum-verified uploads into your persistent local vault. The source file is not moved or deleted.
- **Select folder** only if you deliberately want to submit its files recursively. This can include many files; review the folder first.
- Set an optional **Project** and optional locally supported **Ollama model**. Leave the model blank to skip model processing. The app does not inspect other installed LLM holders automatically.
- **Open Dashboard + Copy Member Token** opens the local browser dashboard and puts your own access token on the clipboard. Paste it into the ACCESS field. Use the dashboard to inspect queue, search, purposes and share settings.
- **Operator Review** asks permission before copying the separate local-admin token to the clipboard; this is for note and category approvals.

Closing the native window stops the localhost hub. **All archived files, notes and records persist** between launches.

## Where HERMES stores things

| What | Location |
| --- | --- |
| Editable source and Windows launchers | The folder where you extracted this ZIP |
| Local Python environment | `.venv/` inside the extracted folder |
| Persistent HERMES vault, database and private owner profile | `%LOCALAPPDATA%\OX_HERMES\` |

Never share your `%LOCALAPPDATA%\OX_HERMES\` directory, authentication tokens, `.venv` or a ZIP made from an active vault. The release builder includes source only and excludes credential/runtime folders.

The installer is **idempotent**: running it again checks your environment and keeps your existing vault and tokens. If installation is partial or corrupted, it stops; it will **not** silently wipe or reset the archive.

## What is implemented now

- Native local file picker (Tkinter) plus clickable localhost dashboard.
- Chunked/resumable sender; SHA-256 integrity checks and duplicate-aware blob storage.
- SQLite processing queue, recovery, searchable file/metadata registry.
- Explainable adaptive purpose classification, category requests and admin review.
- Files private by default; explicit owner-approved team visibility.
- Proposed notes, author submission, admin review and approved-only Obsidian Markdown export.
- Audit records, documented HTTP APIs, optional Java 17+ `HermesBridge.java` reference adapter.
- Temporary demo mode (via `python -m funnel demo`) retained for developers, but not required for ordinary use.

## Existing programs — left alone

| Already installed | What HERMES currently does |
| --- | --- |
| Discord | Nothing automatically. The optional bot source remains for future authorized integration. |
| Obsidian | Produces approved Markdown exports that you can import manually. No automatic vault modification. |
| Java | Optional adapter source for developers; it is not installed or invoked by the two BATs. |
| Multiple local LLM holders | No automatic discovery or model launch. Optional local Ollama-specific annotation is present; other adapters are future work. |

## Boundaries that still matter

This is a **developer pilot**, not a hardened team production server. The operator can access all local private records. Confidential-business isolation, per-project ACLs, deletion/retention, rotation of credentials, production backups and remote TLS/VPN deployment are not finished. Use synthetic files until the team approves a secure hosted configuration.

Only **two root-level BATs** are distributed in this edition. Historical v0.5 launcher references in older reference documents are preserved as project history, not as setup instructions for this release.

## Where to go next

1. Test both BATs on the ASUS and report the exact result. This build was tested in Linux and via real localhost HTTP tests; it has **not** been executed on the ASUS's Windows installation.
2. After the local app works, configure a private team hub with individual credentials and agree on data consent.
3. Then connect HERMES to Discord notifications, Obsidian export destinations and approved Syntra/IXO/APC adapters one at a time.

For source architecture and APIs, see `PILOT_V0.5.md`, `ARCHITECTURE.md`, `PURPOSE_FIRST_ARCHITECTURE.md`, `GROUP_DISCLOSURE_TEMPLATE.md`, `VERIFICATION_v0.6.md` and `contracts/hermes-purpose.v1.json`.
