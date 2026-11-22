# OX PARALLAX — LINUX M0.7 / LIVING WEB

A real **Firefox-compatible WebExtension + encrypted Linux local native messaging bridge** with an orbital network/DOM event viewer. This is a focused Linux proof for PARALLAX, not a finished fork of Zen or a replacement for the Windows U1 application. No cloud dependencies for capture; no telemetry.

## What is actually built

1. Explicitly arm one approved public HTTPS tab and reload it. No background surveillance of unarmed sites.
2. Capture **browser-visible events**: network metadata, redirects, navigation/History API, popup/new-target events, declared links/assets, DOM addition/removal counts, resource timing hints. It is not a full website scraper or TLS decrypter.
3. Display an evidence-labelled 3D-projected orbital graph in Firefox's built-in sidebar. Pointer drag rotates XYZ, mouse wheel zooms, arrow keys orbit; selecting a node reveals actual supporting event types.
4. Use the optional native Linux host to save bounded event frames encrypted with AES-256-GCM + scrypt, **only after you enter a passphrase and choose BEGIN ENCRYPTED SAVE**.
5. Optionally inspect cookie **names and attributes only** after an additional Firefox permission. Cookie values are never saved.
6. Optionally ask for an AI explanation of one selected node via your *own* localhost Ollama instance. There is no automated AI background operation.

The existing site stays fully interactive in Firefox/Zen. The orbital layer is a Firefox sidebar, not yet the standalone 8K native spatial compositor. The SVG graphics scale to high-resolution displays; no 8K raster assets are included.

## Quick Linux development proof

Requires Firefox on Linux, Python3 + venv, Node.js for tests, and internet only for optional Python dependency installation. The host depends on `cryptography`.

```bash
# From this extracted directory; optional verification:
python3 -m pip install --user pytest cryptography
bash tests/run_tests.sh

# One-time user-local encrypted vault bridge:
bash host/install-linux.sh
```

**Load extension as a temporary development add-on:**

Open Firefox `about:debugging#/runtime/this-firefox` → **Load Temporary Add-on** → choose `extension/manifest.json`. Open PARALLAX from the Firefox sidebar. Browse to an approved public HTTPS page, click **ARM + RELOAD**, grant site permission, and watch actual events appear. Click CONNECT VAULT, then enter a session passphrase and begin encrypted saving. The command `Ctrl+Shift+Y` may open the sidebar if Firefox allows that binding.

For a real permanent install, Firefox typically requires a signed extension. A temporary add-on is removed after browser restart. No silent auto-update channel is enabled; the native host installer is a one-time bootstrap, not a signed release manager yet.

## Development and acceptance state

- Cross-platform pure JavaScript unit tests and the native host cryptographic/stdio tests run in this environment.
- **No actual Linux graphical Firefox or Zen host acceptance was possible here**, and native installer hasn't been executed on a user's Linux computer.
- Previous Windows PARALLAX/JEv features are not automatically migrated. The Linux prototype demonstrates the observation and privacy layer first.

Read `docs/HOST_ACCEPTANCE.md`, `docs/ARCHITECTURE.md`, and `docs/SECURITY.md` before installing.

## Explicitly *not* built yet

- Whole-site traversal, captured server code, raw response bodies, full HTML/CSS/JS archive, bypassing paywalls, deep TLS decryption, browser-side global MITM, or hidden page automation.
- Hardware-accelerated native 3D browser surfaces, fracturing into multiple live Linux application windows, signed one-time product installation/updates, Jev delegated autonomous execution, or 8K asset pack.

Those are later, gated architectural work. This milestone makes the high-influx event capture pipeline real and testable first.
