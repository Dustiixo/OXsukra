# Linux M0.7 acceptance checklist (Firefox first)

1. Install Firefox 115+ with a clean, **non-private** profile. Keep existing Zen/Firefox user profile untouched.
2. Run `tests/run_tests.sh` with Node 20+, Python3, pytest, and cryptography; verify passing tests.
3. To install the encrypted host, run `bash host/install-linux.sh`, read the prompt and approve it. It creates a user-level Python venv; no `sudo`.
4. In Firefox open `about:debugging#/runtime/this-firefox`, click **Load Temporary Add-on**, select `extension/manifest.json`.
5. Show sidebar: open Firefox View > Sidebar > PARALLAX, or toolbar extension button / `Ctrl+Shift+Y` if shortcut is available. If the button is hidden, select it from the Extensions toolbar menu.
6. Browse to a **public HTTPS site you own or have permission to inspect**. Click `ARM + RELOAD`, inspect the Firefox permission prompt, approve this origin only.
7. Observe actual REQUEST/RESPONSE/REDIRECT records. Check link declarations are visually different from network evidence. Open an internal SPA route and verify navigation/mutation records.
8. Use the optional demo by hosting all files from `demo/` on your own HTTPS server. Exercise **SPA transition**, **Generate resource loads**, and **Open intentional popup**. A browser popup blocker can suppress the last event.
9. Enter a 12+ character test passphrase and click `BEGIN ENCRYPTED SAVE`. Verify new `.oxcap` exists in `~/.local/share/oxsukra/parallax/vault` and contains no site text/URLs in plaintext.
10. Click `STOP`, list captures and attempt to open with an incorrect and then correct passphrase. Confirm original website still works unmodified.
11. Optional: grant separate cookie permission and inspect attributes. Check **no cookie values** are displayed or saved.
12. Optional: start your own local Ollama on port 11434, enter model name, select node, click explain. Check no analysis occurs before explicit click. Never connect to a hosted model using this feature.
13. Verify navigation to an unapproved origin stops capture; also test tab close, disconnected host, and an overloaded resource burst with visible overflow.

**Not yet accepted:** Zen-specific host path and UI behavior; Wayland compositor integration; visual tab-island/fracture window control; permanent signed update lifecycle; Jev autonomous worker; actual screenshot/HTML/JS source-body archives; 8K display host performance; real Firefox host execution.
