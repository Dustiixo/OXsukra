# Verification for team-starter v0.3

**Preserved baseline checkpoint.** The next version's new adaptive-purpose tests and Java integration are documented in `VERIFICATION_v0.4.md`. This file refers only to v0.3 and its 16-test result.

## Baseline inheritance

The package is based on `OX_Funnel_HERMES_Bridge_v0.2_preview_verified.zip`, whose underlying Python core was first run in this session with 12 passing tests (hashes, queue, resume, Ollama mock, rclone mock, safe ZIP inspection, automation preview and consent ledger).

## v0.3 additions

- Windows BAT installer and opt-in launchers. Python environment with `venv` requires preinstalled Python 3.10+. No automatic pip install for the standard-library hub/client. The bot has a separately approved pip step.
- Operator helper for environment diagnosis and hidden bot credential setup.
- JSON reference-only channel blueprint, meeting overview, group proposal, roadmap and decision template.
- Self-contained clean-room zip inspection and additional validation of onboarding assets.

## Boundaries

- Windows BAT scripts cannot be fully executed in this Linux build environment. They have been statically checked and need a real Windows 10/11 smoke test.
- No Discord guild, VPS, Google Drive tenant, Discord music bot or third-party model has been connected during packaging.
- The v0.2 engine is not a production-grade permissioning platform: all member roles share project visibility; there is no automatic purge, project ACL, quota policy, or worker execution sandbox.
- Third-party bots remain independent services unless deliberately integrated through supported APIs.
- Local tests do not constitute a security audit or guarantee of deployment safety.

The final build record and command output are appended when the ZIP is generated.

## Packaging checks

- 16 Python unittest cases passed on the build host.
- Offline presentation JavaScript checked with Node.js v22.
- 12 Windows BAT launchers statically inspected and normalized to CRLF.
- Zip excludes runtime vault, local Python environment, credentials and generated caches.
- A fresh ZIP extraction is run through all tests before delivery.
