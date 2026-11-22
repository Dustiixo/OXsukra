# OX Spatial Fabric v0.1.1: Independent Retest

Retest date: 2026-11-21. This package is a patched copy of OX Spatial Fabric v0.1; the original ZIP was not modified.

## Results

- Python 3.13.5 `python -m unittest discover -s tests -v`: **23/23 passed**.
- Node.js 22.16.0 `node tests/test_splice_core.mjs`: **8/8 groups passed** (original 7 + silence regression).
- Python bytecode compilation and `node --check` for app and test JavaScript: **passed**.
- Actual local HTTP server/API test: **passed** in Python integration tests; static routes and four individually revision-checked object-slot commits were verified.
- Separate deterministic signal test: repeated analysis of the same synthetic PCM produced identical fingerprint payloads; 3D geometries sampled were finite.
- Chromium focused DOM regression: selecting target object B, refreshing the object list and checking selection B remained selected **passed** after patch.
- Full Chromium browser navigation to `http://127.0.0.1:18865/splice`: **blocked by this execution environment** with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. A separate isolated full-UI test did not complete. Therefore, the *full interactive browser UI is not end-to-end verified* here.
- Native original SELF language VM/Morphic runtime: **not installed, launched, linked or tested**. `self/oxSpliceObject.self` is a handoff candidate only.

## Observed defects and changes

1. **Silent audio was misrepresented:** 1,000 silent windows were assigned chromatic class C and a nonzero bitnote (`0x0001`) because a default timbre bucket remained nonzero. Silence is now explicitly annotated `silent: true`, the bitnote becomes zero, and the UI shows `REST`. This does not solve musical pitch inference in weak or noisy signals; it just avoids false claims of pitched silence.
2. **Selected object was lost on reload:** `refreshWorld()` regenerated the target-object `<select>` options without restoring the chosen ID, so `LOAD OBJECT PRESET` could load the first object. It now retains the existing selected ID when still present. Verified with isolated Chromium DOM test.

## Remaining limitations

- `.self` source has not been parsed or run in the actual SELF VM, so native runtime compatibility is unverified.
- No protected IXO, VELA, DeepBrew, Opris or ECHOFOLD integration exists in this package.
- No complete musical semantics: 16-bit words record derived energy/chroma/onset/timbre approximations, not intent or musical theory causality.
- User-controlled 3D rendering, upload/decode, audio playback, file export and actual server-connected DOM controls require a real browser end-to-end smoke test on the target machine.
- Saving the four RCLL slot controls is four separate writes, not an atomic transaction; a failure can leave a partially committed preset.

## How to run

Start with `start-windows.bat` or `bash start-linux.sh` and open `http://127.0.0.1:8765/splice`. `README.md` contains the full usage notes.
