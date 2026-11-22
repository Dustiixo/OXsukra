# ECHOFOLD Ocean G0.1 — local verification record

**Date:** 17 November 2026. **Source:** the already inspected native `IXO_Convergence_G0_4_Native.zip`, with a separately constructed disposable data directory. No source mutations to G0.4's existing `engine.py` and no changes to the owner's ASUS or authoritative Git worktree.

## Evidence class: LOCAL PASS

1. **Actual G0.4 engine demonstration:** `bridge/seed_demo.py` used the original `IXO` class to create two projects and five source-linked entries in a fresh data directory. Original G0.4 `IXO.verify()` returned `ok=true` after nine journal events, including a human-reviewed relationship and a blocked entry.
2. **Read-only projection:** `bridge/export_ixo_snapshot.py` exported those original IDs, states, source hashes and approved links after validating the IXO hash-linked journal and every selected Workbench blob. A separate export reported 2 projects, 5 entries and 9 verified journal events. SHA-256 values of `ixo.sqlite3` and `workbench.sqlite3` matched before and after exporting.
3. **Python proof:** `python3 -m unittest discover -s tests -q` returned `Ran 5 tests ... OK`. Tests cover valid identities, stable geometry, private-by-default excerpts, refusal of tampered original bytes, refusal of modified journal events and refusing destination overwrite unless explicitly requested.
4. **Native Godot parse/run:** `godot --headless --path godot --quit-after 10` in Godot `4.6.3.stable` returned exit code 0 and logged `OCEAN_READY projects=2 entries=5`, with a stable state ID.
5. **Native scene behavioral proof:** `godot --headless --path godot --script res://tests/ocean_smoke.gd` returned exit code 0 and `OCEAN_SMOKE_PASS native_objects=7 selected_original_hash=true breadcrumb_return=true sonar=true resume=true`. It instantiated the real scene, aimed the camera to select an exported original record ID, entered it, confirmed its source SHA appeared, returned to the exact prior transform, exposed a real approved source link and verified God's Eye View return and a saved breadcrumb file.
6. **Alternative private projection:** Ran the Godot scene against a separately exported snapshot *without original excerpts*, confirming it loaded the same stable seven objects.

## Important boundaries

- **NOT TESTED:** ASUS ROG Flow Z13 Windows graphical runtime, actual Xbox 360 USB/receiver detection, live controller axes/dead zones, OS focus or Steam/Epic interference, FPS or motion comfort, second 7-inch display, real user source data, simultaneous IXO Tk-to-Godot editing, model orchestration or hardware execution.
- **No privileged action:** Godot only reads JSON and saves its own navigation breadcrumbs. It never opens an external program, modifies IXO data, sends network traffic or requests the unfinished protected R11RF6 broker.
- **Not live subscription:** This is an exported read model and can become stale. Refresh the projection manually when the authoritative data changes.
- **Not full Opris:** A bounded local camera/breadcrumb stack is an Opris-style navigation continuation, not the separate fully integrated memory-card engine.
- **Not a Windows installer:** The ZIP is an editable native Godot source project plus standard-library exporter. Godot 4.6.x is required to open it.

## Next acceptance ticket: OX-OCEAN-HOST-001

On the owner's ASUS, extract into a **new folder** (do not overwrite G0.4 or the Spine). First run the bundled sample with a normal keyboard/mouse, visually confirm readable labels, free navigation, target selection, source excerpt and exact return. Connect the Xbox 360 controller, test left/right sticks, trigger movement, bumpers roll, Start standby and focus loss. Then test whether Steam/Epic also receives input, without making any global controller hooks. Record the actual USB identity and input evidence. Finally, run the read-only exporter over a backed-up G0.4 dataset (not the unreconciled `IXO-work` host) and verify that opening a user-owned entry displays the same exact ID/source SHA seen by IXO.

Only after that host proof should the project be considered for integration into ECHOFOLD's authoritative native visual layer.
