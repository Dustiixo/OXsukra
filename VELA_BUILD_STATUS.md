# VELA — authoritative continuity checkpoint (2026-11-20)

## Project identity and boundaries
- VELA owns the music-native creative intelligence and workstation, DJ/playback, audio-as-object/FID experiments, musical call-and-response and the five-scene product concept.
- DeepBrew Studio is a separate homebrew modding and visual mutation editor, not a VELA subsystem or alternative brand.
- IXO, Thought Spine, ECHOFOLD and other systems are independent; adapters must be authorized, versioned, and tested before integration.
- Self and Syntra are external research/integration candidates; the local rules adapter is **not** Syntra.

## Source and provenance
- Derived from the previously generated DeepBrew_VELA M2 source package, without altering that original source.
- This checkpoint corrects *visible* VELA branding but deliberately retains previous internal module names and serialized identifiers (`deepbrew.object/0.2`, `deepbrew.proposal/0.1`) to preserve existing `.fid` compatibility. A future rename requires explicit migration tests, not a string replacement.
- Never claim Windows hardware, audio-driver, microphone or GPU verification from Linux/Xvfb alone.

## Available now (prototype only)
- Native Tkinter app with two-deck playback/mix loop, background procedural response generation, quantized response queue, alternative views, FID archive, object graph and annotation traces.
- 3D audio structure is a visualization driven by measured features, **not** semantic reverse engineering of an MP3.
- Local proposal adapter is heuristic and deterministic, **not** a trained VELA music language model.

## Verification gate
- Python test suite (`python -m pytest -q`) must pass after every change.
- Test real Windows startup, playback, and microphone separately on the target machine.
- For each release attach code diff, test output, screenshots or audio if relevant, rollback instructions, and list of unverified claims.
- No automatic promotion, repository push to protected branches, or rewriting user history without user-approved contracts.

## Milestone path
1. Stabilize M2 baseline and real Windows launch/audio device verification.
2. Make audio-object selection and edits musically meaningful, with audible before/after and reversible history.
3. Encode/version a stable FID contract with raw source + time-aligned structures + explicit provenance; demonstrate integrity and round-trip.
4. Local music-call-response adapter with evaluation and human controls; compare against deterministic baseline.
5. Reconnect visual genome and separate five-scene VELA navigation without replacing prior approved visual baselines.
6. Demonstrate governed adapter interaction with Thought Spine / Syntra only after stable interface and permissions.

## Completion claim
**NOT COMPLETE.** A complete product requires the user's real-device acceptance, the five connected scenes and a substantive musically communicative model, not just passing synthetic tests.

## M2.1 update (2026-11-21)
- Verified Linux-container FID deck checksum guard, including legacy archives without object graph.
- Tests: 17/17 PASS. Windows hardware acceptance still **NOT VERIFIED**; overall VELA **NOT COMPLETE**.

## M2.2 update (2026-11-21)
- Generated-response FID checksum guard tested in Linux container (19/19). Windows device acceptance NOT VERIFIED. VELA NOT COMPLETE.

## M2.3 update (2026-11-21)
- FID import rejects ZIP symbolic links before extraction; Linux-container tests 21/21 PASS. Windows device acceptance NOT VERIFIED. VELA NOT COMPLETE.

## M2.4 update (2026-11-21)
- Cross-platform FID ZIP filename ambiguity guard: Linux-container 27/27 tests PASS. ASUS Windows acceptance NOT VERIFIED; VELA NOT COMPLETE.

## M2.5 update (2026-11-21)
- FID case-insensitive path collision guard, Linux-container tests passed. ASUS Windows/audio acceptance NOT VERIFIED; VELA NOT COMPLETE.

## M2.6 update (2026-11-21)
- FID Unicode NFC + casefold path collision guard, Linux-container tests 31/31 PASS. ASUS Windows/audio acceptance NOT VERIFIED; VELA NOT COMPLETE.

## M2.7 update (2026-11-21)
- FID malformed metadata rejected before extraction; Linux-container tests 35/35 PASS. Windows hardware acceptance NOT VERIFIED; VELA NOT COMPLETE.

## M2.8 update (2026-11-21)
- FID optional audio-object graph structural validation: 39/39 Linux-container tests PASS. ASUS Windows/audio hardware NOT VERIFIED; VELA NOT COMPLETE.

## M2.9 update (2026-11-21)
- Malformed optional original source provenance envelopes now fail with explicit ValueError before extraction. 42/42 Linux-container tests PASS. Native ASUS Windows and audio acceptance NOT VERIFIED; VELA NOT COMPLETE.

## M2.10 update (2026-11-21)
- FID import preflights unsupported ZIP compression/encryption before media extraction. Linux-container 44/44 tests PASS; ASUS Windows/audio acceptance NOT VERIFIED. VELA NOT COMPLETE.

## M2.11 update (2026-11-21)
- FID import bounds manifest size and total declared archive size before reading/parsing JSON. Linux-container 46/46 tests PASS; native Windows hardware acceptance NOT VERIFIED. VELA NOT COMPLETE.

## M2.12 update (2026-11-21)
- Conflicting original source checksums for one FID path rejected; Linux-container 47/47 tests PASS. Native Windows/audio acceptance UNVERIFIED. VELA NOT COMPLETE.

## M2.13 update (2026-11-21)
- Phrase-aware human-queued response scheduling: 1/2/4/8 bars, legacy default preserved; 55/55 Linux tests PASS. Native Windows/audio and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.

## M2.14 update (2026-11-21)
- GUI phrase selector wires into transport scheduling and recorded event provenance. Automated 56/56 PASS; native Windows playback and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.

## M2.15 update (2026-11-21)
- Display-only pending-response impact marker in audio-object view, with future phrase timing and no audio scheduling change. Linux-container 58/58 tests PASS; native ASUS hardware/audio/GUI acceptance NOT VERIFIED. VELA NOT COMPLETE.

## 2026-11-21 — M2.16 exact-boundary response commit
- Parent: immutable M2.15, 64/64 SHA-256 source manifest entries verified; 58/58 baseline tests passed.
- One improvement: commit approved response exactly at scheduled transport frame even when a render callback ends on that frame, preventing one-callback delay in applied event and impact-marker state; no premature audio output.
- Verification: 60/60 Linux-container pytest PASS, including two new boundary regressions; compileall PASS. Native ASUS Windows startup, audio hardware, drivers, microphone, GPU and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: restore immutable M2.15 ZIP to a separate directory; no FID or source-media migration.
- Next: native Windows playback and visual impact-marker acceptance on the ASUS.

## 2026-11-21 — M2.17 non-destructive offline response audition
- Parent: immutable M2.16, 66/66 SHA-256 manifest entries matched; 60/60 baseline automated tests passed.
- One improvement: `audition_queued_response(transport, frames)` renders up to 120 seconds of the current mix with its already-approved pending response at the exact phrase boundary, without audio hardware or modifying live transport state, source media, or FID schema. This is an API capability, not a GUI audition button or AI proposal approval.
- Verification: 62/62 Linux-container pytest tests PASS, including two new offline audition regressions; Python compileall PASS. Native ASUS Windows audio, GUI, drivers and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: restore immutable M2.16 ZIP in a separate directory. No project or media migration.
- Next: expose an explicit user-triggered audition/export control in VELA's interface, with no automatic proposal acceptance.

## M2.18 update (2026-11-21)
- Explicit Tk queued-response audition WAV export control added; existing audio and FID workflows preserved. Linux-container 64/64 tests PASS; real ASUS Windows device acceptance UNVERIFIED. NOT COMPLETE.

## M2.19 update (2026-11-21)
- Queued WAV audition event uses audio-snapshot response identity rather than mutable live pending ID. Linux 66/66 tests PASS; ASUS device acceptance UNVERIFIED. VELA NOT COMPLETE.

## M2.20 update (2026-11-21)
- Approved response identity is checked atomically with offline audition snapshot; Linux 68/68 tests PASS. ASUS Windows hardware UNVERIFIED; VELA NOT COMPLETE.

## M2.22 update (2026-11-21)
- Coherent audition request capture under one lock; Linux 71/71 tests pass. Native ASUS acceptance UNVERIFIED; VELA NOT COMPLETE.

## M2.23 update (2026-11-22)
- Exclusive audition WAV creation; 72 Linux tests passed. Windows acceptance unverified.

## M2.24 update (2026-11-22)
- Failure-safe queued-response WAV export using temporary sibling and no-replace publication; 75 Linux tests passed. Filesystems without hard-link support reject export. Windows acceptance unverified; VELA NOT COMPLETE.

## M2.25 update (2026-11-22)
- Human-selected audio-object bar attenuation (-6 dB, 5 ms edge ramps where length permits) and single-step undo, including after FID reopening. Pause playback and wait for any response rendering to finish, inspect a loaded deck, select a point, click SELECTED BAR −6 dB, then play. Pause and click UNDO BAR EDIT to restore the previous deck. Original recordings stay intact. The edit uses constant four-beat bars at current transport BPM, not automatic beat detection. No new FID schema or external integration. Existing pending audio responses are not rescheduled. Windows hardware acceptance outstanding.

## 2026-11-22 — M2.26 read-only bar A/B audition API
- Parent M2.25, SHA-256 `274115f7dae38f5083a9c8748be0a184ecb14984be0443ca77d0e732c7c78b93`; 94 manifest hashes and ZIP verified; baseline 78 tests passed.
- `Project.audition_bar_edit(deck)` returns matching before/after samples for the latest active attenuation, verifies both media identities and bounds, and leaves deck, history and files unchanged. Works after FID reopening. No GUI playback switch yet.
- Linux pytest 80 passed; compileall passed. Windows hardware, GUI integration of this API, physical listening and five-scene acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.25 separately; no FID migration. Next: connect this API to an explicit A/B audition UI.

## 2026-11-22 — M2.27 interactive bar A/B audition
- Parent: immutable M2.26, SHA-256 `f7e35751837a0e9922b3b0ad889016ce213561c474dbb09849492ad1731a63fc`; ZIP integrity and 97/97 source-manifest checks passed, 80/80 baseline tests passed.
- One improvement: explicit modal A/B listening controls for the latest active bar edit on the inspected deck. Matched buffers restart at sample zero with equal fixed 0.65 gain, play once, and stop at the end. Requires paused main playback and no recording; audition uses an independent audio-device adapter and does not write project state, media or proposal approvals. Stop/Close available. A second output stream may be unavailable on some audio devices; the dialog reports errors.
- Verification: 82/82 pytest tests passed, source compilation passed, real Tk controls exercised under Linux Xvfb using a simulated audio device and verified output samples, screenshot captured. sounddevice is not installed in this execution environment; physical playback, native ASUS Windows audio, driver/stream coexistence, microphone, GPU and full five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.26 separately; no media/FID migration. Next: interactive comparison of a second musical transformation (e.g. bar reverse), with reversible provenance and matching audition.

## 2026-11-22 — M2.28 reversible bar reversal
- Parent: VELA_Continuity_M2_27_2026-11-22.zip, SHA-256 `dfab556955f304e3b624e8b7c40c3d4e9f4837f8d514700bb22d3f9eefd5efa0`; ZIP and 102 manifest hashes verified; baseline 82 tests passed.
- Human-triggered selected-bar reversal with 5 ms edge blends, unchanged outside samples, derived object relationship, matched A/B and single-step undo after FID reopening. Legacy attenuation API retained.
- Linux pytest 84 passed in 1.76s; compileall passed. GUI wiring added but not exercised in this run; physical playback and Windows device acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.27 separately; retain original FID copies; no schema migration. Next: exercise reverse and A/B controls in running Tk.

## M2.29 update (2026-11-22)
- A/B waveform comparison in native Tk, fixed amplitude scale, read-only; Linux 85/85 tests and Xvfb reverse/A-B/undo interaction passed with simulated device. ASUS Windows physical audio and full five scenes unverified; NOT COMPLETE.

## 2026-11-22 — M2.30 A/B waveform playback marker
- Parent: M2.29; single change: read-only, clamped cursor on the original/edited waveforms, following the isolated audio render frame position; closes cleanly with audition window.
- Verification: Python pytest and compileall receipt included. The cursor represents frames rendered, not physical speaker output. Windows audio device, driver, microphone, GPU, and five-scene acceptance remain UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.29 separately; no FID/media migration. Next: test cursor behavior in native Tk with simulated output, then Windows device acceptance.

## 2026-11-22 — M2.31 click-to-cue A/B audition
- Parent: immutable M2.30 (`85d36ecdaff9f9d60ba7035ba389cb916237099b88f0e2e5e3e028e7f046e81e`). One compatible change: user-selected A/B sample-aligned cue on the existing waveform, enabling accurate before/after listening at a transient or bar subdivision.
- A/B previews remain single-shot, require explicit Play A or B, do not alter transport/project/media/FID/proposal approval. Existing start-at-zero behavior remains default.
- Linux automated tests and virtual-display Tk exercise included; hardware audio/driver/GPU/microphone/Windows startup and complete five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Next: real ASUS audio-device acceptance, comparing audible cues and latency.

## 2026-11-22 — M2.32 A/B audition keyboard controls
- Modal A/B window shortcuts: A original, B edited, Space stop, Escape close. No changes to media, FID, or main transport.
- Linux automated tests and compilation passed. Physical Windows audio and native key-event interaction not verified. VELA NOT COMPLETE.
- Rollback: extract M2.31 separately; do not overwrite original media.

## M2.33
- A/B modal keyboard event propagation guarded and Linux virtual-display tested. Native Windows device acceptance remains open. NOT COMPLETE.

## 2026-11-22 — M2.34 bounded A/B loop-region engine
- Parent: immutable M2.33 (`ab6145b3c9d2e38025602b06f16fe129b10ec47c85424976631ee6eafb6ea4e6`), ZIP CRC verified; 128/128 SHA-256 parent entries verified; 89/89 baseline tests passed.
- Exactly one improvement: opt-in `BarAudition.set_loop_region(start_frame, end_frame)` and `clear_loop_region()` provide half-open, nonempty, sample-aligned A/B repeating intervals in the isolated audition engine. Both versions share the same bounds; switching preserves matched cue semantics. Default one-shot behavior is unchanged. No GUI loop controls in this iteration. No media, FID, main transport, or approvals are written.
- Linux automated tests: 90/90 passed, including one new regression test; Python compilation passed. Physical Windows playback, driver, GPU, microphone, native loop UI and complete five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract M2.33 separately; retain original source media and FID backups. No migration. Next: expose explicit region controls in A/B GUI and native-test with simulated output.

## M2.35
Native loop start/end/clear controls tested under Linux simulated audio; Windows hardware UNVERIFIED. VELA NOT COMPLETE.

## 2026-11-22 — M2.38 waveform resize alignment
- Parent: M2.37 archive retrieved and inspected; 144/144 manifest hashes matched; baseline 92/92 tests passed.
- One improvement: redraw A/B waveform, playback cursor, and sample-boundary loop markers against the actual canvas width on resize; waveform clicks use the same width. No audio/FID changes.
- Linux/Xvfb pytest: 93/93 passed, including resize/sample-boundary regression. Windows speakers, drivers, microphone, GPU and full five-scene acceptance UNVERIFIED.
- Rollback: extract immutable M2.37 separately; no migration, no original media changes. Next: native Tk resize interaction smoke test. VELA NOT COMPLETE.

## 2026-11-22 — M2.40 active loop resize regression
- Parent: canonical M2.39 ZIP, actual source inspected; 94/94 baseline Linux/Xvfb tests passed. Independent MORPH M2.39 branch inspected but NOT integrated.
- One improvement: native Tk test resizes waveform at three widths during active bounded A/B loop playback, checks loop/cue marker positions, preserved sample position and playing state, and wrap after subsequent render. Production code, FID and original media unchanged.
- Linux/Xvfb tests: 95/95 passed. Physical ASUS Windows output, drivers, microphone, MIDI, GPU and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract canonical M2.39 separately; no migration. Next: physical Windows playback acceptance or explicitly approved MORPH branch reconciliation.
