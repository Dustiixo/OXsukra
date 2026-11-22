# HERMES Windows Two-BAT v0.6 — verification

**Date:** 2026-11-13. Source derived from v0.5, retaining v0.5 as a separate checkpoint.

## Intent of this release

Exactly two Windows launchers appear at the top level of the ZIP:

- `INSTALL_HERMES.bat`: Python 3.10+ check, local `.venv` creation, source compilation, test suite, idempotent owner-profile/vault installation, local smoke. Does not start application or install third-party programs.
- `OPEN_HERMES.bat`: starts the native Tkinter Funnel and the authenticated hub on localhost; the local user can open the browser dashboard from the app. Closing the app stops the hub, while the SQLite vault stays in `%LOCALAPPDATA%\OX_HERMES\`.

No Discord, Obsidian, Java, Docker, VPS, LLM or music bot is installed, launched or reconfigured by either BAT. Java interop and optional local Ollama model annotations remain available through source and user-initiated controls.

## Evidence actually run

| Check | Result |
| --- | --- |
| Python stdlib tests (including real localhost hub requests) | **35 passed** on Linux / Python 3.12 |
| Local installer idempotence with temporary AppData | **PASS**: second install retains same vault/tokens |
| Partial-install safe stop | **PASS**: does not wipe profile or regenerate credentials |
| Missing-install safe stop | **PASS**: launcher does not implicitly create a vault |
| Local app lifecycle without a GUI display | **PASS**: mocked Tk callback drove a real authenticated localhost hub and shut it down |
| Java JSON adapter source self-test | **PASS** |
| Embedded dashboard JavaScript syntax | **PASS** using Node 24 |
| File intake privacy, sharing, notes, classification and remote mirror gating | **PASS** within HTTP integration tests |

## Not verified

- **Actual Windows double-click execution has not been performed on Shane's ASUS.** The BAT files were inspected and normalized to CRLF, but Windows startup, Tkinter availability and Obsidian/Discord coexistence must be checked on the target machine.
- A real native Tkinter window has not been visually smoke-tested here; the backend launch lifecycle uses a mocked UI entry point.
- Earlier optional Playwright browser interaction tests were blocked by the execution environment's Chromium process-socket permission. Dashboard JS syntax and HTTP behavior were tested, but human click-through remains a Windows acceptance gate.
- The local profile stores bearer credentials in a private user-profile file, not Windows DPAPI. No confidential data should be added until a security review and credential hardening.
- No live Discord, Obsidian vault write, external cloud drive, real Syntra/IXO/APC adapter or cross-machine processing was installed/tested. This release provides the local core and optional interface contracts, not all future integrations.

## Acceptance test for Shane

1. Extract ZIP into a stable folder on the ASUS.
2. Double-click `INSTALL_HERMES.bat` and read the terminal's result.
3. Double-click `OPEN_HERMES.bat` and confirm the native application opens.
4. Submit one synthetic file and inspect its private record using the dashboard button.
5. Close, reopen and verify the file is still indexed. Nothing should be downloaded into or modified inside existing Discord, Obsidian, Java or LLM installations.

Source can be modified locally. To rebuild the source ZIP without vaults or credentials, run `python -m tools.build_share_zip` from the extracted source directory.
