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
