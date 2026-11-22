# UNDERBYTE — native Godot source (first playable campaign slice)

**This is new original source**, not a repackaged HTML experiment or an emulator. It is a Godot 4.7.2 GDScript game project. **Native graphical launch is NOT YET VERIFIED** in the build environment because the Godot executable/export templates are unavailable there. The Python content/asset checks passed; those checks do not prove that the game launches or plays correctly. Do not describe this as a fully released game.

## On Windows

1. Extract this folder to a location you control (not inside IXO/OXsukra).
2. Double-click `RUN_UNDERBYTE_WINDOWS.cmd`. If Godot 4.7.2 is not installed, the script asks permission before downloading the official engine into **this project's `engine/` folder only**. It does not modify your system PATH.
3. The launcher imports assets then starts the native engine with this project. It does **not** launch a browser, run a fake GBA emulator or request access to other programs.
4. If the project fails to import, read the terminal error rather than treating that as success. Run `TEST_UNDERBYTE_WINDOWS.cmd` for the isolated engine smoke test.

You can also install Godot yourself from https://godotengine.org/download/windows/ and use **Import → this folder's `project.godot` → Run Project (F6/F5)**.

## Controls — Windows foreground game

| Input | Effect |
|---|---|
| A/D or arrows | Walk |
| Space | Jump |
| J | Strike enemy or mine an actual nearby resource |
| E | Talk, activate real relay, collect device, enter portal, discover 2.5D cache |
| C | Craft recipes (must stand beside workbench) |
| I | View inventory and exact quantities |
| K | Pick actual playable palette (4 pixel variations) |
| V | Toggle 2D / visually skewed layered 2.5D view; up/down shift layer |
| U | Use recovered device's enemy-stun pulse |
| L | Place a crafted persistent lamp |
| M | Region map |
| Click-hold on sprite | Pick up and levitate; release to drop; ESC to cancel |
| F5 | Save; the game also autosaves |
| R | Return to your checkpoint |
| N | Toggle original soundtrack |
| ESC / P | Pause and save |
| F1 | Controls |

**First journey**: find the nearby wanderer, mine shards and fiber, use the workbench to craft a signal key, cross the linked zones to repair a relay, find the awakened device, then reach the outer passage. The game remains open afterward. You can fight, collect, find special layer secrets, collect coins, customize, build lamps and recover your saved state. The character's unexplained personal mission is NOT resolved by this small quest.

## Android source path

Godot supports Android exports, but this packet **does not include a verified APK** or an Android SDK. Touch-to-action bindings exist and reuse the same gameplay logic. An actual Android export, touchscreen test, safe-area and performance validation are separate gates. Do not call this a released phone game.

## What is not implemented

No Windows desktop overlay, autonomous background mode, program/file adapters, OS interception, native Android APK, full 2.5D collision/navigation overhaul, multiplayer, adaptive AI narrative or complete canon campaign. No access to real personal files or applications is requested. The HUD is compact and intentionally not a fake dashboard. Artwork/music are generated original assets in this project.

## Verification commands

```bash
python tests/test_content.py
# When Godot 4.7.2 is installed:
godot --headless --path . --editor --import --quit
godot --headless --path . --script res://tests/test_godot.gd -- --isolated-test
# To play:
godot --path . --rendering-method gl_compatibility
```

The headless test uses dedicated `underbyte_isolated_test.*` save names and cleans them; it does not alter the player's normal save.

## Source data and boundaries

`data/world.json` defines deterministic topology, resources, enemies, interactables and depth caches. `data/recipes.json` defines real material consumption and outputs; `data/dialogue.json` holds provisional dialogue and journal notes. `scripts/game.gd` implements simulation, rendering and continuity. Save data resides in Godot's `user://` app data, never in your real files/folders.

Documentation: `docs/UNDERBYTE_CANON.md`, `docs/BOUNDARIES.md`, `docs/ACCEPTANCE.md`, `docs/DECISION_LOG.md`, and `docs/evidence/BUILD_REPORT.md`.
