# IXO FlowMesh Atlas M0.6 candidate

Parent immutable M0.5 archive SHA-256: `598f923e1a5bcfce7e62980a1cba8f9fa9aef545d9d9a33e1a7d2f228ec8bc74`.

Run `START_DUAL_SURFACE.cmd` after extracting to a separate folder. FIELD depicts a recorded research trace, not live AI reasoning. Tap a branch to see its question and evidence count. Open Evidence shows the latest matching recorded receipt in full-screen DECK, with the timeline cursor unchanged. Use Close Deck to return; close the contextual lens separately. Source satellites indicate recorded excerpt receipts (visual count capped at 10 per branch). Segmented armor, materials, and moving ornaments are visual metaphors, not extra discoveries. The FlowMesh engine is byte-identical to M0.5. No source updates or network actions are authorized by the renderer.

## Validation
- `python -m unittest discover -s tests -v`: 47 passed.
- `python -m unittest discover -s visual_lab/tests -v`: 4 passed.
- `python -m unittest discover -s spatial_lab -p tests_spatial.py -v`: 6 passed.
- `node --check gpu_field/render_gl.js` and `node --check gpu_field/field.js`: passed.
- `xvfb-run -a python gpu_field/browser_test_m06.py`: passed in Chromium WebGL2 (container graphics, physical GPU not independently confirmed). Real branch label click, 13 evidence receipts, receipt #047, full-screen DECK, preserved cursor, rewind and restore. Logs retain initial headless timeout and an early overlay visibility assertion failure; retry waits for the transition and pauses playback during proof inspection. Exporter discovery was corrected to the actual test directory.
- Screenshots in evidence/M0_6_ATLAS_*.png are captured from the tested renderer. Historical screenshot and log files are not M0.6 evidence.

## Remaining gates
ASUS Windows, physical touchscreen, uninstructed usability, WebGL1 fallback for M0.6, graphics performance and live model acceptance: NOT_RUN. No GitHub promotion. No integration into other projects.

## Rollback
Use the unchanged M0.5 archive in a separate folder; no data migration or changes to existing sessions.

## Prior details (historical)

# IXO FlowMesh M0.5: full-screen DECK experiment

Run `START_DUAL_SURFACE.cmd` on Windows and toggle between **FIELD** (3D world) and **DECK** (full-screen pause menu). DECK provides Paths / What Happened / Replay History / World Settings. Return using Escape, Tab, CLOSE DECK, or FIELD. This is a candidate demo, not an installed release. Recorded activity is not live AI reasoning. Original M0.4 source is preserved separately.

See `CANDIDATE_README.md` and `docs/CHANGELOG_M0_5.md` for tests, limitations and rollback.

# IXO / FlowMesh M0.4: DUAL SURFACE GPU FIELD

**Experimental offline prototype. Not a release or a deployed game engine.**

## Run on a Windows ASUS Flow

Extract this ZIP into a **new folder**, then double-click `START_DUAL_SURFACE.cmd`.
It opens `gpu_field/index.html` in your default browser, using no internet, paid services, installations, or API keys.

The two views operate on **one and the same recorded research trace**:

- **FIELD**: low-chrome interactive 3D environment. One finger or mouse drag orbits, two-finger pinch zooms, two-finger motion pans, tap selects an object, and holding on a branch opens a context wheel. Wheel zoom works with a mouse. Nodes remain meaningful even without reading a legend.
- **DECK**: the exact same event cursor and selected branch, now exposing branches, explanation, proofs, quality options, and private local JSON import.

Use ←/→ to move through receipts, Space to play/pause, R to recenter, and Tab to toggle views. The bottom rail offers accessible buttons for the same actions.

## What is actually rendered

This version uses GPU-accelerated WebGL2, with an offline WebGL1 fallback. It has actual 3D vertex meshes with camera perspective, normals, lighting, depth tests, GPU point sprites, source-linked geometric bridges, and branch status colors. Verified source excerpt receipts generate green peripheral vessels, while parked branches are red. These are visual metaphors of recorded data. Rotation and floating motion are **ambient art**, never indications of hidden AI work.

The bundled sample has 72 verified exporter receipts. Its evidence sequence and branching data are inherited from M0.3, not synthetic generated claims. Independent branch identities are preserved. No unrelated project code is merged.

## Privacy / operation

The viewer is read-only. It never writes research sessions. It can load a private local trace JSON through DECK; client-side schema checking alone does **not** independently verify the SHA of a user-imported trace. Use `spatial_lab/export_trace.py` to export verified traces. The old loopback bridge and M0.3 spatial chamber are retained alongside this experimental GPU view for rollback and independent review.

No third-party rendering library was bundled. This is an **experimental renderer**, not a mature Godot/Babylon/Three integration. Its own Xvfb + Chromium WebGL browser verification is recorded in `evidence/M0_4_GPU_BROWSER.log`, along with preserved source and adapter test results. Browser user-experience acceptance and your ASUS M0.4 device acceptance have **not** been performed.

## Rollback

Delete only the extracted M0.4 candidate directory. The original `IXO_FlowMesh_M0_1.zip` and M0.3 candidate remain separate and unchanged; do not delete research workspaces or other project files. See `docs/ROLLBACK_M0_4.md`.

## Verification

From the extracted directory: `py -3 VERIFY_PACKAGE.py` (Windows) or `python3 VERIFY_PACKAGE.py` (Linux). Original core tests: `py -3 -m unittest discover -s tests -v`. Browser tests require Playwright, Chromium, and a working virtual/software GPU; they are **not required to launch** the demo. Run them where supported via `python gpu_field/browser_test.py`.
