# Underbyte Web v0.3 / Pulse Radar (RIPPLE candidate)

This is a reversible, standalone HTML Canvas gameplay change based on immutable Underbyte Pocket Adventure v0.2; NOT a Godot-native build, ROM, emulator or production release. No private source is published on GitHub.

- Open `UNDERBYTE_GBA_TOUCH_v0_3_RIPPLE.html` in a browser.
- R or tap **R · SCAN**: show an actual 4-second local radar of nearby unmined shards, living scraplings, Moss, the relay, and quest-unlocked Echo Key/gate.
- A jumps, B mines/fights, L dashes, D-pad moves, UP interacts. Select palette, Start pause.
- Target markers update immediately when a shard is mined or an enemy defeated. Scanning does not alter quests, inventory or save state.
- Previous localStorage save key `underbyte-pixel-v02` is preserved for compatibility, subject to browser storage support.

## Reproduce tests

On Linux with Chromium and Python Playwright installed: `python verification/browser_underbyte_pulse_v0_32.py`. The coordinator's stdlib-only tests run separately with `python -m unittest discover -s tests -p test_ripple.py -v`. The smoke tests call Playwright `page.set_content()` because local managed Chromium blocks file and localhost navigation; actual Android file-opening has NOT been verified.

Rollback: discard the candidate HTML and reopen the original v0.2 HTML from immutable `/UNDERBYTE_GBA_V02_PACKAGE.zip`. No conversion of existing save data occurs.
