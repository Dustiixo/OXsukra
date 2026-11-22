# PARALLAX // Session Atlas M0.1

**Working prototype and Chromium capture bridge, not a replacement for the existing native PARALLAX browser.**

This increment implements the user's requested opening screen with saved research sessions, tab islands, a navigable archipelago and explicit AI digest. It can save *real* Chromium/Edge tabs when loaded as an extension. `home.html` can also be opened standalone as a demonstration, but **standalone cannot read or reopen browser tabs or run local AI**.

## Run immediately (visual demo)
Open `home.html` in any modern browser. The **300-tab / 10-island** default example is clearly tagged **DEMO / SYNTHETIC**. It does not imply browsing data was collected.

## Connect to real browser tabs (Chromium / Chrome / Edge)
1. Extract this folder from the zip.
2. In Chrome open `chrome://extensions`, or Edge open `edge://extensions`; enable Developer Mode.
3. Click **Load unpacked** and select this folder (the one with `manifest.json`).
4. Open a new tab to see PARALLAX Session Atlas. Click **SAVE CURRENT TABS**. Only HTTP(S) URLs/titles in the current window are saved. Existing Chrome tab groups become islands; other tabs group by domain.
5. Switch between sessions; select an island; use **OPEN SELECTED ISLAND** or **RESTORE ALL**. Restoring groups explicitly creates live browser tabs. Large all-session restores are warned about.
6. The **ARCHIVE & CLOSE** action closes only matching, unpinned source tabs after confirmation. It does not close unrelated tabs, and it cannot preserve unsaved form/page state.
7. **EXPORT** session to JSON. **IMPORT** restores saved research records without opening pages.

## Local AI (optional)
- Run Ollama on the same machine with its normal API at `http://127.0.0.1:11434` and install a model you have resources to run.
- In **Local AI / Settings**, enter your *installed* model name; click **CHECK LOCAL MODELS** to verify.
- Select a saved session. Click **GENERATE LOCAL AI DIGEST** and confirm. Only then is session metadata (and any explicitly captured excerpts) sent to **localhost**, never to a cloud AI service by this extension.
- The normal first display is a **metadata overview**, not an AI result. The synthetic demo's narrative is explicitly illustrative.
- Optional **CAPTURE PAGE EVIDENCE** operates only against up to 8 currently open tabs in the selected island per click, after your permission and origin grants. It reads headings, descriptions and some article text, limited to 2,400 characters per tab. New imports / closed tabs cannot be scraped in the background.
- Summaries are **not fact checked**. Session content is untrusted and may contain adversarial instructions. Verify against cited source tabs.

## Existing native PARALLAX integration path
Earlier PARALLAX was a native WPF/.NET + WebView2 browser, with a local browser-state v3 JSON journal, bookmark/history/download tools, and restore capped to 16 URL records. This M0.1 is a separately packaged **Session Atlas experiment**, not a claim to have upgraded that original executable.

For integration, make `PARALLAX session-atlas.v1` a dedicated storage subsystem alongside, not inside, browser-state.v3.json. A native adapter should:
- collect `TabDescriptor` (URL/title/group/island/source evidence), never raw cookies;
- atomically persist snapshots + integrity receipt; maintain original journal unchanged until migration is proven;
- materialize only the focused island's tabs (or a small subset) as WebView2 controls;
- retain URL/title metadata for hundreds of hibernated tabs without allocating hundreds of WebView2 processes;
- show the home screen using the same HTML/CSS design loaded from local app resources, exposing **only** a strictly validated and origin-restricted message API;
- return verified navigation results and create traceable evidence records, never assuming clicking meant success;
- use local inference only on explicit user request.

Microsoft recommends using a shared WebView2 environment for tabbed apps and avoiding unnecessary controls. Current browser runtime/profile data should not be assumed equivalent to a saved URL index.

## Privacy / limitations
No telemetry or cloud AI API is intentionally included. Metadata and captured snippets live in Chrome's extension local storage; **they are not encrypted**. Export JSON can contain private URLs and captured page text. The optional localhost Ollama endpoint is accessed only when you press AI or Check Models. Page capture requests per-site access before injection.

Saved sessions persist across browser restarts. A snapshot is **not** a complete browsing state: tab back-forward history, cookies, passwords, forms, scroll, media playback, and live app state are not serialized. The demo shows 300 *saved records*, not 300 running tabs. A full restore can be expensive.

## Verification
Run `node --test tests/logic.test.js`. JavaScript syntax: `node --check logic.js`, `node --check app.js`, `node --check background.js`. No claim of Windows native integration, Chrome Web Store review, or runtime validation on your specific machine. Browser policy may prevent execution on protected/internal pages.

## Status
M0.1: session snapshot/read/export/import, existing tab group preservation, per-island restore, optional localhost digest and permissioned evidence capture, interactive visual design. Next M0.2: native WebView2 adapter integration, SQLite+atomic persistence, selective tab activation and real-host recovery tests.
