# DeepBrew M2: end-to-end Windows device trial

## Setup

Unzip the complete package and double-click `START DEEPBREW.bat`. Allow first-run dependencies if required. Do not open it from within the ZIP. The Windows launcher/driver is not yet verified; retain the startup log if it fails.

## Test 1 — real sound

Press LOAD DEMO, PLAY. Expect a continuous eight-bar demo. Move CROSSFADE; check that both decks sound different. No browser tab should be necessary.

## Test 2 — an object, not a decorative graphic

Click 04 DEEPBREW OBJECT. Drag to rotate and scroll to zoom. The `OBJECT aud_*` label and hash must remain the same. Click a point: a measured timestamp, RMS and frequency centroid appear. Type an annotation and PIN MOMENT. Double-click the event in history to inspect source ID and timestamp. Switch to Water's Edge and Black Hole and back: the same audio plays, independent of view.

## Test 3 — substitute reasoner: controlled boundary

Choose INSPECT A or B and enter a prompt. Click PROPOSE · LOCAL REASONER. Confirm no audio change yet. Inspect the logged proposal from the history. Reject one proposal and verify the recording is unchanged. Propose again and ACCEPT + BREW. Expect a new generated layer to enter at the next bar (only while playing). Compare with A/B ORIGINAL and REVERT. The generator is procedural and no local model download is needed.

## Test 4 — manipulation and evidence

Click a point in the object view, then SLICE SELECTED BAR → DECK B. Check Deck B becomes the chosen bar and the original source in Deck A is unchanged. Save `.fid`, close and reopen. Confirm sources, generated audio, proposal status, revision chain, annotations, time-linked events and selected source hashes survive. Export a WAV and optionally import it into FL Studio or REAPER.

## Test 5 — original file and legacy compatibility

Import a legal-to-use MP3 or WAV. Save `.fid`, inspect archive using any ZIP tool: `originals/` should hold the exact source bytes and `media/` the normalized WAV. `manifest.json` should hold object graph. Open `demo/VELA_Trial_Seed.fid` from the previous version and verify migration is marked as reconstructed evidence, not invented original trace.

## What to record

- Windows build and audio device type
- Whether double-click launched on first try (with or without downloading Python)
- Whether original and modified audio were audibly distinct
- Whether rotating/annotating preserved playback, especially after 5 minutes
- Whether response landed at a bar boundary without clipping or stalling
- Whether `.fid` saved and reopened with the same audio identities and annotations
- Any crash log, error message or unexpectedly changed files

## Automated results

Build container: 15 Python unit/integration tests passed; desktop GUI launched and recorded a screenshot in Xvfb; one generated response and `.fid` round-trip were exercised. **This is not a pass for Windows audio device compatibility, real-world perception quality, or a live Syntra integration.**
