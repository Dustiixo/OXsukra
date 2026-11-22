# HERMES Windows live-Discord addon v0.7 — evidence

**2026-11-13 (Toronto local evening), sandbox/CI only.** Derived directly from the existing v0.6 Windows two-BAT source (retained intact in a separate archive); added two optional BAT launchers, a local Discord bridge wrapper, a native operator-attach entry point, a tiny persistent non-secret server/user-ID configuration and tests. Existing `%LOCALAPPDATA%\OX_HERMES` data model and original INSTALL/OPEN commands are not changed.

## Executed

- `python3 -m unittest discover -s tests -q`: **38 tests passed** (the 35 existing v0.6 tests plus three Discord setup/bridge tests).
- The tests include authenticated real localhost HTTP interactions, private queue/notes/purpose checks, idempotent installer logic and privacy checks.
- The additional tests cover numeric server/user ID validation, duplicate/invalid ID rejection, no bot token field in the persisted Discord IDs file, and a mocked whole-process bridge smoke verifying scoped environment values, loopback port and teardown without leaking the token after exit.
- Python source compilation: must be confirmed using the same `INSTALL_HERMES.bat` on Windows; the sandbox test runner imported and exercised new helper code successfully.

## Not verified

- Actual Windows double-click on Shane's ASUS and native display.
- Optional `discord.py` install on Windows (no live service credentials were used in the sandbox).
- Discord Developer Portal application/bot creation, guild installation, slash sync, real attachment ingest, and gateway reconnection.
- Four-person remote deployment, cloud sync, Discord channel/folder auto-creation, or direct Obsidian vault writes.

## Safety

- The token is entered with `getpass`, is passed to the bot in this process only and is not written into the config file.
- Guild ID and allowlisted user IDs are stored locally under `%LOCALAPPDATA%\OX_HERMES\discord_connection.json`; editing IDs requires a user prompt.
- Bot action scope stays guild-specific and allowlisted; no message-content intent or broad passive message watcher.
- Initial bot access to the local hub uses the existing local member token (not admin); this is an **owner-only pilot**, not complete per-user identity separation.
- The bot and local hub stop when the `03_CONNECT_DISCORD` process ends. This prototype is not an always-on service.
