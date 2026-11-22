# FlowMesh Visual Lab M0.2 · four stages

**Open `visual_lab/index.html` in a browser.** On Windows use `START_VISUAL_LAB.cmd`. This is a local prototype, not a replacement for the native `RUN_WINDOWS.cmd` interface and not a finished application release.

1. THE BASE: faithfully reconstructed button / logs model of M0.1.
2. MAKE IT TALK: the same receipt sequence explained as What / Why / Proof / Next.
3. LIVING MAP: clickable recorded branches, actual shared excerpt links and three independent timeline lanes.
4. OPEN FLOW: all of the above plus a **labelled design simulation** of three cooperative stuck-path behaviors.

The included `demo_trace.js` is generated from **actual FlowMesh demo state** with validated local receipt-chain integrity. `NEXT RECEIPT` and the slider replay **real recorded events**. They do not execute a model, access the web, or mutate FlowMesh. All logic and assets are local; no third-party dependencies or network requests.

To view an actual personal session (LOCAL ONLY; may contain private excerpts), run from the extracted package root:

```powershell
py -3 visual_lab\export_trace.py --root C:\path\to\your\FLOWMESH_WORKSPACE --out C:\path\to\your\private_trace.json
```

Then open the Visual Lab and choose **LOAD LOCAL TRACE**. The browser reads the chosen file locally. Do NOT upload a personal trace to public GitHub. The export intentionally fails if integrity verification fails and refuses overwrite.

**Limitations:** replay is not live streaming; this lab does not implement new scheduler actions. Its adaptive "what if" buttons are purely UI simulations. Original FlowMesh and the separate VELA project remain untouched. The UTF-8 guard candidate was incorporated into this isolated source tree; test it before Windows rollout. No model cognition is claimed.
