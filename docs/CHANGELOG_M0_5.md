# M0.5 full-screen DECK candidate

Parent M0.4 archive SHA256: `93b08e1a5b14d9a73fb97cdc8266d9782bcdf2ee53a8a960d60d35a759fb0ceb`.

## Change
- Replaced a right-hand evidence drawer with a full-screen DECK pause/control surface.
- Kept the same GPU FIELD scene, renderer, evidence trace, branch selection and temporal cursor.
- Added four large full-page DECK sections and new close/Escape behavior.
- Preserved old commands: Tab toggles; FIELD/DECK toolbar; event replay; private JSON trace import; quality presets.
- Kept all external file/source interactions read-only. No project source promotion or engine changes.

## Tests
- `python -m unittest discover -s tests -v` : 47/47 PASS.
- `python -m unittest discover -s visual_lab/tests -v` : 4/4 PASS.
- `python -m unittest discover -s spatial_lab -p tests_spatial.py -v` : 6/6 PASS.
- `xvfb-run -a python gpu_field/browser_test_m05.py` : PASS in Chromium WebGL2 (full-screen dimensions 1600×900, four menu sections, Escape/Tab, history, display quality, 450×850 mobile, no JS page errors). See `evidence/M0_5_BROWSER.log`.

## Blocks
- Patched M0.5 Windows ASUS device acceptance: NOT_RUN.
- Uninstructed usability study: NOT_RUN.
- Graphics performance, battery and end-to-end model integration: NOT_RUN / BLOCKED.
- Public GitHub promotion: NOT_RUN.

## Rollback
Unpack the original immutable M0.4 candidate ZIP. No data migrations occur and all modified files here are confined to this candidate.
