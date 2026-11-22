# Test evidence / IXO Spatial Chamber M0.3

Development environment: isolated Linux container, Python 3.13, Node.js 22, Chromium + Playwright. This is **not Windows ASUS acceptance**.

| Test | Command | Observed result |
|---|---|---|
| FlowMesh core | `python -m unittest discover -s tests -v` | 47 tests, 47 passed |
| Read-only exporter | `python -m unittest discover -s visual_lab/tests -v` | 4 tests, 4 passed |
| Local privacy bridge | `python -m unittest spatial_lab.tests_spatial -v` | 6 tests, 6 passed |
| Browser interaction | `python spatial_lab/browser_smoke.py` | PASS (72 real receipts; 4 branches; rewind; source proof; orbit; zoom; focus; 3 timeline lanes; playback; local import; mobile; no JS errors) |
| JS syntax | `node --check spatial_lab/chamber.js` | exit 0 |
| Source original integrity | SHA256 of `IXO_FlowMesh_M0_1.zip` | `cb336bc46cf5c2d9e797a7b84e60f9ef8e2ab2df7debe98bee0576f71a6762ae` |

The browser test used Playwright `page.set_content` with local assets inlined because container Chromium navigation to both `file:` and `localhost` was blocked by an administrative policy. This limitation does not indicate the UI was run through an external host or that the live bridge's browser behavior was tested end to end. The live bridge's HTTP access-control, file handling and read-only behavior were tested with Python urllib.

**Blocked:** Windows M0.3 execution, independent project adapter integration, actual model cognition, final release acceptance, GitHub source promotion.

Screenshot evidence: `evidence/SPATIAL_CHAMBER_DESKTOP.png`, `evidence/SPATIAL_CHAMBER_MOBILE.png`, `evidence/SPATIAL_CHAMBER_MOBILE_LENS.png`.
