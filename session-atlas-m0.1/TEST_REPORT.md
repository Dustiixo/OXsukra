# PARALLAX Session Atlas M0.1 — test report

Date: 2026-11-22 (America/Toronto)

## Verified in this tool environment
- `node --test tests/logic.test.js`: **7/7 pass**.
- `node --check logic.js app.js background.js`: **pass**.
- In Chromium automation using inlined local source, preview rendered with **300 demo tabs across 10 islands**; navigation to map rendered **10 SVG nodes**, Settings view visible, and **zero page JS exceptions**.
- Mocked Chromium-extension APIs: saving **300 live-like tab descriptors** across 10 tab groups persisted to the in-memory `chrome.storage.local` test double; opening the selected island requested exactly **30 tabs** and **1 tab group**, zero page exceptions. This is a **mocked** integration test, NOT proof of a real browser extension install or actual website loading.
- Preview screenshot `preview.png` is from the actual HTML/CSS/JS app rendered headlessly after inlining local source, not an AI mockup.

## Not yet verified
- Loading the unpacked extension on the user's own Chrome, Opera, Edge, or a Windows native PARALLAX host.
- Native PARALLAX WebView2/Qt integration or 300-tab crash recovery on real hardware.
- Connection to an Ollama model, actual page-text permission prompts, cross-browser tab group behavior, 300-tab live restore performance.
- Full security audit, threat model, accessibility audit, or live-site capture reliability.
