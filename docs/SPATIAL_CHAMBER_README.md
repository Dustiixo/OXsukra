# IXO / Spatial Chamber M0.3 · Experimental candidate

A spatial alternative to the M0.2 four-panel Visual Lab. Reuses the **same unchanged FlowMesh source, ledger, tests, and read-only trace exporter**. It is not an AI model and cannot modify the engine or workspaces.

## Open immediately (no installation)

On Windows, extract the ZIP into a **new folder** and double-click `START_SPATIAL_CHAMBER.cmd`. Or open `spatial_lab/index.html` locally in a Chromium-based browser. Works fully offline, using a **72-receipt actual verified sample trace** included as a local file.

The chamber has 3D projected branch objects, family links, actual shared-source edges, 3 timeline lanes (engine / prompt / evidence), a readable current-event explanation, SHA-256/source references, local trace loading, a camera you can orbit with the mouse, zoom, pick branches, focus, rewind, scrub, and play. Keyboard: left/right to step receipts, Space to pause/play, R to recenter.

**No model-thinking animations:** ambience is abstract decoration, not intelligence activity; proof pulses only when replaying a recorded event. The sample source was verified by the FlowMesh exporter, but the browser alone cannot prove a privately loaded JSON's provenance. It checks schema and event order, while source verification remains the exporter's responsibility.

## Inspect your own verified workspace without copying its contents

On Windows: `START_SPATIAL_LIVE.cmd` and paste the absolute folder path of a FlowMesh **session**, not the extracted source-code folder. The server prints a private URL and serves on **127.0.0.1 only**, using a per-launch random access key. Open that URL in a browser. The read-only bridge periodically calls the existing FlowMesh verifier; any integrity failure produces HTTP 409 and refuses to serve the trace. No public API or network service is required.

Or export an immutable local JSON first:

```powershell
py -3 spatial_lab\export_trace.py --root "C:\path\to\your\FlowMesh_session" --out "C:\path\to\private_trace.json"
```

Then open the Chamber and click **LOAD TRACE**. This leaves the workspace untouched. Never upload or commit a personal trace to a public repository: it may include confidential excerpts. The server does not store or modify the session. There are no POST endpoints.

## Why the appearance is different

The old GUI showed tabs and debugging counters. The Chamber maps **existing real branch and evidence relationships** into an orbital field with pencil-thin wireframes and contextual interfaces. Its 3D world is a navigable spatial metaphor, not a literal display of hidden model reasoning. Evidence paths appear only where the underlying trace contains matching source IDs. A parked research branch changes its visual status without being erased.

The idle graphical effects, lens distortions, orbital geometry and background stars are **aesthetic only**. No false generated work, discovery or source connection is represented.

## Known limits / release gates

- No autonomous work or model inference is added by the viewer.
- Full source-level Windows acceptance of M0.3 not run; prior device acceptance applies to original M0.1 baseline only.
- A private local JSON export can contain sensitive research. Keep it private. Loopback access keys must not be shared.
- The package's SHA-256 manifest protects source-package integrity but is not a digital signature.
- Live bridge data is a verified **snapshot** polled every 4.5 seconds, not a stream of internal model thoughts.
- No GitHub writes, production integration, source-owner promotion, or release.

## Rollback

Delete only the extracted M0.3 candidate folder. Reopen untouched `IXO_FlowMesh_M0_1.zip` or `FlowMesh_Visual_Lab_M0_2_Candidate.zip`. Never delete workspace or session directories when removing this candidate. The source ZIP hashes are recorded in `docs/SPATIAL_SOURCE_PROVENANCE.json`.
