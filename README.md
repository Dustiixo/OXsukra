# VELA — Water's Edge / Audio Object M2 Continuity Checkpoint

**Owner:** VELA (OXsukra ecosystem). **Status:** experimental native source package, not a completed AI/music workstation.

This checkpoint fixes the previously conflated DeepBrew Studio branding in the visible VELA interface. It does *not* merge the two projects. Older internal `deepbrew.*` archive identifiers are kept solely for backward compatibility; changing those safely requires an explicitly versioned migration.

## Quick start
1. On Windows, extract this complete ZIP to a normal directory.
2. Double-click `START VELA.bat` (internet may be required only for initial Python/dependencies install).
3. `LOAD DEMO` → `PLAY` → `04 AUDIO OBJECT` → rotate / inspect audio structure → propose / accept or reject musical variation.
4. Save and reopen a `.fid` project; compare the original and changed mix and inspect the timeline.
5. If it fails on Windows, run `DIAGNOSE_WINDOWS.bat` and read `VELA_STARTUP_LOG.txt` (review private paths before sharing).

## Development
- `python -m pytest -q` runs deterministic unit tests; package is not Windows device-verified.
- `VELA_BUILD_STATUS.md` defines ownership, open gates, and the verified milestone progression.
- `VELA_PROGRESS_LOG.md` captures this checkpoint and is intended as an append-only project ledger.
- `HISTORICAL_M2_README.md` and the legacy `DEEPBREW_*` documentation remain as preserved historical context, not current VELA naming.

## Not yet built
No deployed Syntra integration, trained musical-language intelligence, complete five-scene workstation, full DAW, or reversible semantic MP3-to-3D representation. The 3D view projects measured spectral features of source audio.

## Safety and provenance
Keep original recordings untouched. Treat AI heuristics as proposals, not authoritative facts. Do not update core OXsukra/Syntra code, push protected GitHub branches, or merge project identities without explicit authorization and tests.

## M2.12 update (2026-11-21)
- Conflicting original source checksums for one FID path rejected; Linux-container 47/47 tests PASS. Native Windows/audio acceptance UNVERIFIED. VELA NOT COMPLETE.

## M2.13 update (2026-11-21)
- `Transport.queue_response(audio, response_id, quantize_bars=4)` schedules a human-approved response at the next four-bar boundary. Supported values: 1, 2, 4, 8; default 1. This is an API capability; GUI selection is not yet wired. Linux tests: 55/55 PASS; Windows device acceptance UNVERIFIED.

## M2.14 update (2026-11-21)
- Response-entry phrase length is selectable in the native GUI (1/2/4/8 bars); defaults to legacy one bar. Linux-container tests 56/56 PASS. Windows hardware UNVERIFIED.

## M2.15 update (2026-11-21)
- Audio-object view shows the next approved response's loop-relative impact position and remaining bars. Linux-container tests 58/58 PASS; native Windows hardware UNVERIFIED.

## M2.16 update (2026-11-21)
- Exact-frame response commit at callback boundary, Linux-container 60/60 PASS; ASUS hardware UNVERIFIED.

## 2026-11-21 — M2.17 non-destructive offline response audition
- Parent: immutable M2.16, 66/66 SHA-256 manifest entries matched; 60/60 baseline automated tests passed.
- One improvement: `audition_queued_response(transport, frames)` renders up to 120 seconds of the current mix with its already-approved pending response at the exact phrase boundary, without audio hardware or modifying live transport state, source media, or FID schema. This is an API capability, not a GUI audition button or AI proposal approval.
- Verification: 62/62 Linux-container pytest tests PASS, including two new offline audition regressions; Python compileall PASS. Native ASUS Windows audio, GUI, drivers and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: restore immutable M2.16 ZIP in a separate directory. No project or media migration.
- Next: expose an explicit user-triggered audition/export control in VELA's interface, with no automatic proposal acceptance.

## M2.18 update (2026-11-21)
- New `EXPORT QUEUED AUDITION .WAV` GUI control renders an already-approved pending response through its entry boundary without changing live playback. Requires an approved queued response; no proposal auto-accept. Linux-container 64/64 tests PASS. ASUS Windows acceptance UNVERIFIED.

## M2.20 update (2026-11-21)
- Queued WAV audition export refuses a changed approved response while the save dialog is open; Linux 68/68 tests PASS. Windows hardware UNVERIFIED.

## M2.24 update (2026-11-22)
- Queued audition export publishes only a finished WAV, never overwrites an existing file, and cleans up temporary files after handled failures. Choose a local hard-link-capable filesystem (e.g. NTFS; Windows behavior not yet verified). Other export paths are unchanged.

## M2.25 update (2026-11-22)
- Human-selected audio-object bar attenuation (-6 dB, 5 ms edge ramps where length permits) and single-step undo, including after FID reopening. Pause playback and wait for any response rendering to finish, inspect a loaded deck, select a point, click SELECTED BAR −6 dB, then play. Pause and click UNDO BAR EDIT to restore the previous deck. Original recordings stay intact. The edit uses constant four-beat bars at current transport BPM, not automatic beat detection. No new FID schema or external integration. Existing pending audio responses are not rescheduled. Windows hardware acceptance outstanding.

## 2026-11-22 — M2.26 read-only bar A/B audition API
- Parent M2.25, SHA-256 `274115f7dae38f5083a9c8748be0a184ecb14984be0443ca77d0e732c7c78b93`; 94 manifest hashes and ZIP verified; baseline 78 tests passed.
- `Project.audition_bar_edit(deck)` returns matching before/after samples for the latest active attenuation, verifies both media identities and bounds, and leaves deck, history and files unchanged. Works after FID reopening. No GUI playback switch yet.
- Linux pytest 80 passed; compileall passed. Windows hardware, GUI integration of this API, physical listening and five-scene acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.25 separately; no FID migration. Next: connect this API to an explicit A/B audition UI.

## M2.27 update (2026-11-22)
- Pause playback and stop recording; inspect the edited deck, then click A/B AUDITION BAR EDIT. Choose A BEFORE or B AFTER; STOP or CLOSE ends the comparison. The isolated preview uses a separate native output stream, which may be unavailable on some devices. No edits or undo are performed. Linux sample/Tk interaction checks pass; real playback and Windows hardware unverified.

## 2026-11-22 — M2.28 reversible bar reversal
- Parent: VELA_Continuity_M2_27_2026-11-22.zip, SHA-256 `dfab556955f304e3b624e8b7c40c3d4e9f4837f8d514700bb22d3f9eefd5efa0`; ZIP and 102 manifest hashes verified; baseline 82 tests passed.
- Human-triggered selected-bar reversal with 5 ms edge blends, unchanged outside samples, derived object relationship, matched A/B and single-step undo after FID reopening. Legacy attenuation API retained.
- Linux pytest 84 passed in 1.76s; compileall passed. GUI wiring added but not exercised in this run; physical playback and Windows device acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.27 separately; retain original FID copies; no schema migration. Next: exercise reverse and A/B controls in running Tk.

## M2.29 update (2026-11-22)
- The A/B audition dialog now displays matched before/after stereo peak waveforms on a fixed scale. It does not change audio or approval state. Reversal → A/B → Undo was exercised in a real Linux Tk session with simulated output; Windows physical audio remains unverified.

## M2.30 update
The A/B waveform dialog includes a read-only playback marker. It tracks frames rendered by the audition stream, not confirmed speaker latency.

## M2.31 update (2026-11-22)
- Native A/B waveform now lets the user click to cue **both** versions to the same sample index. Pressing A or B explicitly begins a one-shot preview from that cue; no automatic audio playback on click. Default zero-offset `BarAudition.select(choice)` is retained for callers. Linux Tk/Xvfb proof uses simulated output; physical audio / Windows drivers remain unverified.

## 2026-11-22 — M2.32 A/B audition keyboard controls
- Modal A/B window shortcuts: A original, B edited, Space stop, Escape close. No changes to media, FID, or main transport.
- Linux automated tests and compilation passed. Physical Windows audio and native key-event interaction not verified. VELA NOT COMPLETE.
- Rollback: extract M2.31 separately; do not overwrite original media.

## M2.33
- A/B modal keyboard shortcuts consume handled events to avoid triggering main transport. Windows audio-device acceptance unverified.

## 2026-11-22 — M2.34 bounded A/B loop-region engine
- Parent: immutable M2.33 (`ab6145b3c9d2e38025602b06f16fe129b10ec47c85424976631ee6eafb6ea4e6`), ZIP CRC verified; 128/128 SHA-256 parent entries verified; 89/89 baseline tests passed.
- Exactly one improvement: opt-in `BarAudition.set_loop_region(start_frame, end_frame)` and `clear_loop_region()` provide half-open, nonempty, sample-aligned A/B repeating intervals in the isolated audition engine. Both versions share the same bounds; switching preserves matched cue semantics. Default one-shot behavior is unchanged. No GUI loop controls in this iteration. No media, FID, main transport, or approvals are written.
- Linux automated tests: 90/90 passed, including one new regression test; Python compilation passed. Physical Windows playback, driver, GPU, microphone, native loop UI and complete five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract M2.33 separately; retain original source media and FID backups. No migration. Next: expose explicit region controls in A/B GUI and native-test with simulated output.

## 2026-11-22 — M2.38 waveform resize alignment
- Parent: M2.37 archive retrieved and inspected; 144/144 manifest hashes matched; baseline 92/92 tests passed.
- One improvement: redraw A/B waveform, playback cursor, and sample-boundary loop markers against the actual canvas width on resize; waveform clicks use the same width. No audio/FID changes.
- Linux/Xvfb pytest: 93/93 passed, including resize/sample-boundary regression. Windows speakers, drivers, microphone, GPU and full five-scene acceptance UNVERIFIED.
- Rollback: extract immutable M2.37 separately; no migration, no original media changes. Next: native Tk resize interaction smoke test. VELA NOT COMPLETE.
