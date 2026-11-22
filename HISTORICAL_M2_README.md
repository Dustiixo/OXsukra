# DEEPBREW × VELA — The Water's Edge M2

**Native Windows-first experimental audio-object workstation.** It is not a website, browser loopback, Self VM, or Syntra runtime. This package is a preserved, isolated extension of VELA M1.1. The original sources and prior source ZIP have not been overwritten.

## QUICK START (Windows 10/11 x64)

1. Extract the entire ZIP to a normal folder. Do **not** run the launcher from inside a compressed ZIP preview.
2. Double-click **START DEEPBREW.bat**. The starter checks compatible Python and Tk, creates an isolated environment, and installs required native-audio packages when needed. If Python isn't found, it downloads the official Python 3.13.17 Windows installer, verifies its Authenticode signature, and installs it only for your Windows user. **First launch requires internet** if dependencies are absent. The program itself works locally thereafter.
3. Press **LOAD DEMO**, **PLAY**. Alternatively, use **OPEN .FID** to open `demo/DeepBrew_Trial_Seed.fid`.
4. Click **04 DEEPBREW OBJECT**. **Drag** the 3D audio structure to rotate, **scroll** to zoom, and **click** a point to select a measured time slice. Use INSPECT A / INSPECT B to choose which sound object is visible.
5. Type a musical intention, click **PROPOSE · LOCAL REASONER**. The decision is stored as a proposal, not executed. Click **ACCEPT + BREW** to generate a real audio response queued for the next bar, or **REJECT** to preserve the source without changes. Keep playback running; the audio never needs to wait for thinking.
6. With a point selected, use **SLICE SELECTED BAR → DECK B**. This copies the containing bar into Deck B without altering its source. Record a note with **PIN MOMENT**; the annotation attaches to the chosen time slice.
7. **SAVE .FID**, close and reopen it; use **A/B ORIGINAL**, **REVERT**, and **EXPORT PLAYABLE .WAV** or export separate WAV layers / MIDI for DAW work.

If the startup fails, please send the final error line from the console. `VELA_STARTUP_LOG.txt` contains local paths and should be reviewed before sharing.

## WHAT IS BUILT

- Native Tkinter desktop interface; PortAudio/audio-device playback, two decks, crossfade, generated layer, bar-quantized response queues.
- FOUR synchronized perspectives: Water's Edge, Black Hole, Thought Spine, DeepBrew Object.
- A truly saved audio **object** with a content SHA-256 identity, a feature descriptor (96 time slices × 9 frequency bands by default), source path, permitted behaviours, links, revisions and annotations.
- Interactive projected 3D acoustic skeleton. Axis/time, radial bands, RMS and spectral flux are mapped from actual measurements. Perspective changes do not mutate audio or identity.
- A **replaceable proposal boundary** (`deepbrew.proposal/0.1`) with the local rule adapter (`local_rules/0.2`) standing in for the future Syntra integration. It is explicitly NOT Syntra, nor a trained music model.
- Acceptance/rejection as separate inspectable human events. Accepted proposals create genuinely synthesized audio layers. Source and response remain different content objects.
- Non-destructive edits: selected source bar to another deck, A/B audition and one-response revert. Preserves separate audio layers and source->response links.
- Experimental `.fid` ZIP package with all normalized WAV media, original imported bytes (WAV/FLAC/MP3/OGG/AIFF), object graph, time-slice features, annotations, proposals, decisions, response versions and history. Checksums are checked during import.
- In-memory import migration of older M1 `.fid` archives. Added reconstructed relationships are marked as **inferred**; prior raw archive bytes aren't modified.
- Local-only optional Ollama planner for the older VELA response mode (requires already-running Ollama). DeepBrew substitute does not require it.

## WHAT IT DOES NOT CLAIM

- It is **not a Windows precompiled .exe**, but a double-click Windows setup-and-launch package. We ran the native GUI on a virtual Linux display, not on your Windows audio driver.
- It does **not** contain the real `Self` language runtime, Alex's `Syntra Kernel`, `SyntraLang`, a self-training model, or sophisticated semantic music understanding.
- The acoustic skeleton is a **visual projection of measured features**, not reversible decompression of the waveform, true stem separation, or evidence that the audio intrinsically contains semantic intent. The WAV + original source bytes carry the actual playable sound.
- An MP3 is preserved verbatim when imported, alongside normalized WAV for processing. It is not modified in-place to become a new codec. The `.fid` is a container with a ZIP structure, not an audio-playable MP3.
- The project currently has ordinary local process boundaries, not a hardened multi-process security broker or signed identity system. SHA-256 detects corruption against its stored manifest; it does not authenticate a maliciously replaced manifest.
- Long source files are analyzed in blocks and the current transport loops a configured duration (8 bars initially); it is not an arrangement/DAW and does not automatically tempo-stretch.

## Verification

From the project root, install dependencies and run `python -m pytest -q`. **15 tests passed in the build container**, including original WAV data integrity, scheduled audio response, proposal acceptance/rejection, tamper detection, object graph / FID round trip, and old M1 compatibility. A native Tkinter GUI was opened and interacted with under Xvfb. Screenshot: `demo/deepbrew_actual_native_view.png`. Windows audio devices and the first-run PowerShell installer remain unverified on the target device.

## Related documents

- `DEEPBREW_CONTRACT.md`: object identity and proposed adapter contract.
- `DEEPBREW_RESEARCH_MAP.md`: the deep architecture vision and research boundary.
- `TRIAL_PROTOCOL.md`: explicit device verification steps and pass/fail criteria.
- `CONCEPT_SPEC.md`: earlier VELA M1 concept baseline, preserved for continuity.
- `demo/DeepBrew_Trial_Seed.fid`: re-openable generated sample project.
- `demo/DeepBrew_Trial_Mix.wav`: actual offline-rendered audio example.
