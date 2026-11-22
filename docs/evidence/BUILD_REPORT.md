# UNDERBYTE native game engineering report — 2026-11-03

## Scope and source

Isolated new Godot 4.7.2 GDScript project authored at `/mnt/data/UNDERBYTE_NATIVE_GODOT`. Prior UNDERBYTE HTML experiments from earlier turns remain intact. No existing user repository was modified. This project has original procedural pixel sprites, original PCM theme, game source, deterministic world/recipe/dialogue data, source validation and an optional user-consent launcher for the official Godot engine.

## Work executed

- Inspected earlier delivered HTML files and master implementation contract.
- Discovered native Godot was **not** installed in this execution container (`which godot`, `which godot4` returned no executable).
- Built source: 16 linked 300-unit segments (4 cardinal and 12 connector segments), 50 resource objects, 15 simple enemies, 4 depth caches, original player atlas (12 states × 4 palettes), HUD, crafting, interaction, movement/collision, mouse pickup/drop, defensive saves, NPC dialogue, quest sequence and one device pulse mechanic.
- Implemented foreground-only simulation. No OS/desktop access, no browser/game wrapper, no real file scans.
- Ran **10 content/data/art/audio/source tests**, all passed (log `PYTHON_CONTENT_CHECKS.log`).
- Godot runtime engine import, GDScript compile, graphical first-frame test, actual Windows run, Android APK/export and physical touch checks: **NOT_RUN**. There is a Godot runtime test at `tests/test_godot.gd`, but it has **not** been executed. Do not infer native playable success from the content checks.

## Formal exit

- **PHASE:** 00 SOURCE AUDIT / 01 NATIVE PROJECT SOURCE / 02–14 FEATURE IMPLEMENTATION CANDIDATE (source only, not phase-complete)
- **SOURCE:** isolated folder, local Git repo, implementation commit recorded in `docs/evidence/SOURCE_HEAD.txt`; current HEAD is obtainable from `git rev-parse HEAD`
- **CHANGED FILES:** `project.godot`, `scenes/game.tscn`, `scripts/game.gd`, `data/*.json`, `assets/*`, `tests/*`, docs and Windows scripts
- **REAL USER-OBSERVABLE RESULT:** unverified on real Godot engine; asset atlas can be independently inspected
- **TESTS:** `python tests/test_content.py` PASS 10/10; Godot import and native graphical smoke NOT_RUN
- **REAL-HOST EVIDENCE:** NOT_RUN Windows/Android
- **SAVES / MIGRATIONS:** schema 1 implemented; actual save/restore runtime NOT_RUN
- **UNRESOLVED:** install native engine, fix any import errors, graphical validation, packaging/export templates, Android and future desktop boundaries, full story content and release work
- **NEXT PHASE UNLOCKED?:** NO. Requires successful Godot native import + gameplay test; don't advance release promotion on source tests alone.

## Launch/test sequence on Windows

1. Extract to a separate folder; run `RUN_UNDERBYTE_WINDOWS.cmd` and approve official engine download if needed. Launcher verifies pinned SHA512 before opening the archive.
2. If import fails, capture terminal output and do not advance.
3. Run `TEST_UNDERBYTE_WINDOWS.cmd` for engine smoke. It uses isolated test save names.
4. Manually confirm first-frame sprite visible, actual movement, jump, mine/strike, craft, relay, device, death/recovery, perspectives, cursor grab/drop, pause/save/restart.
5. Only after a complete real-host PASS should it be called first playable native release.
