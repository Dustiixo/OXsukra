OX PARALLAX / LINUX M0.7 / LIVE CAPTURE
=======================================

STATUS: Prototype source; offline contract/crypto tests executed; Firefox/Zen Linux GUI host NOT tested.

PRIVACY: Site-by-site explicit arming; no webpage body/cookie values saved; local AES-GCM vault only after user passphrase. No automatic AI.

HOW TO TRY (Firefox Linux):
1. Read README.md and docs/HOST_ACCEPTANCE.md.
2. Optionally run tests/run_tests.sh (needs Node, Python3, cryptography, pytest).
3. bash host/install-linux.sh   [asks before user-local dependency install]
4. Firefox > about:debugging#/runtime/this-firefox > Load Temporary Add-on > extension/manifest.json
5. Open PARALLAX in Firefox sidebar. Open an authorized HTTPS site; click ARM + RELOAD.
6. Click CONNECT VAULT and BEGIN ENCRYPTED SAVE if you want encrypted local evidence.

LIMITATIONS: Firefox unsigned add-on is temporary; stable install/signing/updater not implemented. This proof captures dynamic relationship METADATA, not entire websites, full HTML or restricted content. Prior Windows PARALLAX remains separate/unmodified.
