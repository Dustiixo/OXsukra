# FlowMesh Visual Lab M0.2 · evidence-first candidate tests

Test context: Python 3.13 Linux, Chromium headless browser running HTML/CSS/JS injected as a self-contained page due container navigation restrictions. **Not a Windows/ASUS acceptance run.**

| Gate | Observed | Evidence |
|---|---|---|
| Source provenance | Original M0.1 hash preserved | `CANDIDATE_README.md` |
| Existing FlowMesh engine | 47 / 47 passed | `docs/visual_lab_core_tests.log` |
| Local trace exporter | 4 / 4 passed | `docs/visual_lab_export_tests.log` |
| Browser DOM/UI smoke | PASS | `visual_lab/browser_smoke.py`, `docs/visual_lab_browser_smoke.log` |
| Four stage navigation | PASS | `docs/visual_lab_preview/01_base.png` ... `04_open_flow.png` |
| Actual receipt replay | PASS for 72 demo events | Browser assertion |
| Branch selection + real edge links | PASS in demo | Browser assertion |
| No-evidence adaptive behavior | UI simulation tested, NOT engine behavior | Stage 04 buttons |
| Actual live model / native app / external projects | NOT TESTED | Explicit blocker |

Original project source/code was not promoted. Demo data contains only the shipped example source texts; personal trace export may contain private source excerpts and should remain local.
