# HERMES / OX Funnel v0.5 — verification record

**Date:** 2026-11-13. Built by extending the previously released v0.4 source ZIP, leaving the earlier Library checkpoint intact.

## Executed evidence

| Gate | Observed result |
| --- | --- |
| Full Python stdlib HTTP/SQLite suite | **PASS — 31 tests**, `python3 -m unittest discover -s tests -q`, Python 3.12 on Linux |
| Purpose/Java reference adapter | **PASS — Java JSON self-test**, `java adapters/java/HermesBridge.java selftest` |
| Actual localhost Java ↔ Python route preview | **PASS** as part of the existing `test_java_interop_over_real_http` suite test |
| Combined browser dashboard JS | **PASS syntax**, extract inline scripts from `funnel.ui` + `funnel.purpose_ui`, check with Node 24 `node --check` |
| Ephemeral demo lifecycle | **PASS**, spawned `python3 -m funnel demo`, detected temporary URL/tokens, sent SIGINT, process exited 0 without stderr |
| Private file isolation | **PASS**, HTTP member/bot read denial across list, item detail, download, search, queue and status |
| Explicit share and audit | **PASS**, owner acknowledge → team visibility → revoke, admin-only audit |
| Notes review/export | **PASS**, private proposal → author submit → admin approve → team export; withdraw hides from team |
| Remote mirror opt-in | **PASS**, mocked configured rclone does not run for private files and no webhook emits; separate owner authorization enforced |
| Schema migration | **PASS**, sample pre-v0.5 rows preserved and assigned private defaults, reinitialization idempotent |

## Did not pass / not claimed

- **Chromium browser click-through not executed**: attempted optional Playwright test; local Chromium failed to create its process socket inside this sandbox (`Operation not permitted`). Permission escalation was disallowed. This is an environment blocker, **not** a successful UI test. The optional source test is included for a permitted workstation (`python -m tools.browser_smoke_optional`).
- **Windows BAT execution not tested on Windows.** Batch files were inspected; the new BAT was normalized to CRLF. Real Windows acceptance remains required.
- No live Discord server/app token, Google Drive, Dropbox, remote VPS, rclone service account, Syntra, Astra-Lang, IXO or APC/Odin runtime connected. No cross-machine agent execution tested.
- No production security audit. The admin can read all members' private records; `team` shares all members rather than per-project ACLs. No quotas, retention/deletion workflow, external-copy recall, expiring tokens, secret rotation, or recoverable production backups.
- `MEETING_OVERVIEW.html` retains historical v0.3 explanations in some panels; the v0.5 banner and `PILOT_V0.5.md` supersede those details.

## Recommended acceptance gate

On an actual Windows PC, run `00_INSTALL_AND_CHECK_WINDOWS.bat`, then `13_TRY_PRIVATE_DEMO_WINDOWS.bat`, connect with the printed member token, submit a harmless test file, verify private receipt, share it, create a knowledge note, and approve with the separate admin token. Record the observed UI behavior and errors. **Do not add confidential project data to the shared hub yet.**

## Reproducible packaging

Use `python -m tools.build_share_zip` from the unpacked source root. The builder allowlists code/docs, excludes credentials and vaults, generates `MANIFEST_SHA256.txt`, and validates each ZIP payload against its SHA-256 line before reporting success.
