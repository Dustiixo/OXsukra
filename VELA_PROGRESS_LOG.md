# VELA progress ledger

## 2026-11-20 — M2 continuity checkpoint
- Recovered previous VELA M2 source from the conversation's working container.
- Established explicit boundaries: VELA owns the audio object; DeepBrew Studio stays independent.
- Changed UI naming to VELA Audio Object while keeping old FID internals for compatibility.
- Added documented verification gates, next milestone, and a path to independent integration.
- Tests: 15/15 passed in checkpoint container; Windows audio device remains unverified.
- Windows native/audio hardware: unverified.

## 2026-11-21 — M2.1 FID deck integrity gate
- Parent checkpoint: VELA_Continuity_M2_2026-11-20.zip, SHA-256 verified against 35 source manifest entries.
- One code improvement: on FID import, verify deck `sha256_pcm_wav` against archived normalized WAV bytes, including legacy FIDs lacking object-graph hashes. No schema change. Existing FIDs without this optional digest retain prior compatibility.
- Added two regression tests: corrupted legacy deck rejected, untampered legacy deck round-trips.
- Verification: 17/17 pytest PASS on Linux container; parent baseline 15/15 PASS. No Windows startup, driver, microphone, GPU or audio-device acceptance claimed.
- Rollback: retain immutable M2 ZIP and restore its `vela/project.py`; M2.1 makes no on-disk project migrations.
- Next: Windows device startup and real audio playback acceptance on ASUS, when safe to run.

## 2026-11-21 — M2.2 generated-response provenance
- Parent: immutable M2.1 checkpoint, verified 36/36 SHA-256 source entries before modification.
- One improvement: newly generated response WAVs receive optional SHA-256 digests; FID imports verify these even when the object graph is absent. Older responses without digests remain loadable.
- Verification: 19/19 pytest PASS on Linux container; two new tests cover tamper detection and legacy compatibility.
- Hardware: Windows startup, playback, drivers, microphone and GPU remain unverified.
- Rollback: use original M2.1 ZIP; no existing project/media was modified or migrated.

## 2026-11-21 — M2.3 FID symlink import hardening
- Parent: immutable M2.2 checkpoint; source manifest 38/38 SHA-256 verified before change.
- One improvement: reject Unix symlink-typed ZIP members during FID import before extraction, while accepting ordinary Unix-mode WAV entries. No schema change or existing media modification.
- Verification: 21/21 pytest PASS in Linux container; two regression tests added.
- Windows ASUS startup, audio playback, drivers, microphone, GPU and filesystem-specific behavior remain unverified.
- Rollback: restore M2.2 source ZIP; no existing project files migrated.

## 2026-11-21 — M2.4 cross-platform FID filename guard
- Parent: immutable M2.3 ZIP; all 40 source SHA-256 manifest entries matched before modification.
- One improvement: reject Windows-ambiguous ZIP member basenames (backslashes, alternate-data-stream colons, reserved device names, trailing spaces/dots and control characters) before any FID extraction. Existing valid media and serialized FID schema unchanged.
- Verification: 27/27 pytest PASS in Linux container (21 prior + 6 regression cases); parent 21/21 PASS. Windows device/filesystem, driver, playback, microphone and GPU acceptance remain NOT VERIFIED.
- Rollback: restore immutable M2.3 ZIP. No project/media files were modified or migrated.
- Next: run native Windows startup and real audio playback acceptance after ASUS migration preflight.

## 2026-11-21 — M2.5 case-insensitive FID path collision guard
- Parent: immutable M2.4 ZIP, verified against all source SHA-256 entries before modification.
- One improvement: reject FID ZIP member paths that collide after Unicode casefolding, before extraction; no FID schema or media change.
- Two tests: colliding media paths rejected; valid round-trip retained.
- Linux-container pytest passed; native ASUS Windows startup, playback, driver, microphone and GPU acceptance remain UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract original M2.4 archive into a separate folder. No existing media/project migrated.
- Next: native Windows startup and real playback acceptance when ASUS preflight permits.

## 2026-11-21 — M2.6 Unicode-normalized FID collision guard
- Parent: immutable M2.5, verified against its 44 SHA-256 source entries before modification.
- One improvement: FID ZIP member collision check now applies Unicode NFC normalization before casefolding. Distinct ZIP spellings that resolve to the same normalized path are rejected before extraction; no FID schema or media changes.
- Two regression tests cover normalized collisions and ordinary round-trip. Linux-container pytest 31/31 PASS. Native Windows filesystem, startup, playback, drivers, microphone and GPU remain UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.5 source ZIP into a separate directory. No existing project/media was modified or migrated.
- Next: native Windows startup and playback acceptance when ASUS preflight permits.

## 2026-11-21 — M2.7 malformed FID metadata validation
- Parent: immutable M2.6, 46/46 SHA-256 entries verified; 31/31 parent tests passed.
- One improvement: validate FID manifest top-level object and deck/response collection and element types before extracting archive members. Malformed input now fails with explicit ValueError rather than unexpected type errors; no schema or valid media change.
- Four parametrized regression cases; 35/35 Linux-container tests passed. ASUS Windows startup/audio hardware remains UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract M2.6 ZIP to a separate folder; existing FIDs were not migrated.
- Next: Windows native startup and real playback acceptance when ASUS storage preflight permits.

## 2026-11-21 — M2.8 FID audio-object graph structural validation
- Parent: immutable M2.7 source ZIP, 48/48 SHA-256 entries verified, baseline 35/35 tests passed.
- One improvement: malformed optional object graph collection/object types rejected before extraction, with explicit ValueError; legacy graph-less FIDs remain compatible.
- Five new parametrized/regression test cases; 39/39 Linux-container tests passed. No hardware test.
- Rollback: restore immutable M2.7 source ZIP separately; no user audio or project files migrated.
- Next: native Windows startup and playback acceptance when storage preflight permits. VELA NOT COMPLETE.

## 2026-11-21 — M2.9 malformed original provenance guard
- Parent: immutable M2.8; 62/62 SHA-256 entries verified; 39/39 baseline tests passed.
- One improvement: validate optional original_binary provenance records in deck, response and audio-object metadata before dereferencing or extracting; invalid envelopes yield controlled ValueError. No schema, audio, or existing FID migration.
- Three parametrized regression cases; 42/42 Linux-container pytest PASS. Native ASUS Windows/audio hardware NOT VERIFIED; VELA NOT COMPLETE.
- Rollback: extract M2.8 ZIP separately; do not overwrite user projects or audio.
- Next: native Windows startup and playback acceptance when ASUS storage preflight permits.

## 2026-11-21 — M2.10 FID ZIP feature preflight
- Parent: immutable M2.9 ZIP; source SHA-256 52/52 verified; 42/42 baseline tests passed.
- One improvement: reject encrypted or non-stored/non-deflated ZIP members before extracting any media; existing valid FIDs unchanged.
- Two tests cover unsupported BZIP2 and accepted DEFLATE. 44/44 Linux-container tests PASS. Native ASUS Windows/audio NOT VERIFIED; VELA NOT COMPLETE.
- Rollback: extract immutable M2.9 archive to a separate folder. No media was modified or migrated.
- Next: native Windows startup and real playback acceptance when storage preflight permits.

## 2026-11-21 — M2.11 FID pre-decompression metadata bounds
- Parent: immutable M2.10, 54/54 source manifest hashes verified, 44/44 parent tests passed.
- One improvement: enforce archive entry-count, total declared uncompressed size and 8 MiB manifest metadata cap before JSON decompression/parsing. Prevents oversized metadata from being processed before safety checks. Valid FID schema, source media and musical response behavior unchanged.
- Two new regression tests; 46/46 Linux-container pytest PASS. Native ASUS Windows startup, drivers, microphone, GPU and playback remain UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.10 source ZIP separately. Do not overwrite projects or audio.
- Next: native Windows audio acceptance on the actual ASUS when safe.

## 2026-11-21 — M2.12 conflicting original provenance guard
- Parent: immutable M2.11 ZIP; 68/68 parent manifest hashes verified before modification, 46/46 baseline tests previously confirmed and 47/47 current tests passed.
- One improvement: refuse FID records that declare different SHA-256 identities for the same original media path. Previously dictionary deduplication could silently discard one conflicting claim. No media, FID schema, or generated music changed.
- One new regression test; Linux-container pytest 47/47 PASS. ASUS Windows launch, playback, driver, microphone, GPU and filesystem acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract M2.11 ZIP to a separate directory. No existing project/media was modified or migrated.
- Next: non-destructive native Windows startup and real playback acceptance.

## 2026-11-21 — M2.13 phrase-aware musical response scheduling
- Parent: immutable M2.12 SHA-256 `43ce226770ebc4bb11e54d937130bd1f95fd1f775f46520fe0a45b8ab3d43e51`; parent manifest 58/58 verified; 47/47 baseline tests passed.
- One improvement: approved responses may enter at the next 1-, 2-, 4-, or 8-bar boundary, preserving the legacy one-bar default and the audio callback's boundary splitting. Reject invalid options without modifying pending state.
- Verification: 55/55 automated pytest tests PASS in Linux container, including new phrase timing and invalid-input regression cases. No physical playback or Windows audio driver test.
- Rollback: restore M2.12 source from its immutable archive in a separate directory; no FID/media migration.
- Next: GUI phrase selection and visible impact marker. VELA NOT COMPLETE.

## 2026-11-21 — M2.14 GUI phrase entry selector
- Parent: immutable M2.13 ZIP; SHA-256 manifest 60/60 matched; baseline 55/55 tests passed.
- One improvement: native Tk GUI exposes 1/2/4/8-bar response-entry selector, default 1; validates selection before proposal acceptance or response-ledger mutation; schedules via M2.13 transport API and records selected phrase in project event.
- Verification: 56/56 Linux-container pytest tests PASS, compileall PASS; no native Windows device/audio playback test. GUI appearance not physically inspected on Windows.
- Rollback: extract immutable M2.13 ZIP to a separate directory; user media and FIDs unchanged. VELA NOT COMPLETE.
- Next: visual impact marker showing pending phrase target in the audio-object view.

## 2026-11-21 — M2.15 pending response impact marker
- Parent: immutable M2.14, 62/62 SHA-256 manifest entries verified and 56/56 baseline pytest tests passed.
- One improvement: VELA audio-object canvas now displays the pending approved response's exact loop-relative entry location and remaining bars, using absolute transport frame scheduling without modifying the audio callback or FID schema. Marker disappears after pending response is applied or cleared.
- Two new automated tests; Linux-container pytest 58/58 PASS and compileall PASS. GUI rendering on ASUS Windows, playback, drivers, microphone, GPU, and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.14 source ZIP to a separate directory. No media/FID migration or cross-project write.
- Next: non-destructive Windows native GUI/audio acceptance and screenshot confirmation when ASUS is accessible.

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

## 2026-11-21 — M2.18 explicit queued-response audition WAV export
- Parent: immutable M2.17 (`99d8d256f9b0fd7d84035c2e3bd23a9a5313299cab0e0de22a28a14a3779fb3c`); source manifest 72/72 matched, baseline 62/62 tests passed.
- One improvement: native Tk GUI button exports a bounded WAV of an already-approved pending musical response across its scheduled phrase entry using the M2.17 offline audition API. No implicit proposal approval; existing standard mix export unchanged. Live transport and source media remain unchanged. Export event stores response ID and output basename.
- Verification: 64/64 Linux-container pytest PASS, including two new GUI-method regressions; Python compileall PASS. Native ASUS Windows startup, speaker output, driver, microphone, GPU and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.17 ZIP in a separate folder; no project/media/FID schema migration.
- Next: real Windows GUI and audio audition acceptance on ASUS with a user-approved response.

## 2026-11-21 — M2.19 queued audition response provenance
- Parent: canonical M2.18 SHA-256 `1f4e9207d32eac784b9fa235c55c310d04fc868d89795e8bf904cb3de55fcb3b`; 70/70 parent manifest checks matched, 64/64 parent tests passed. Parallel M2.18(1) preserved separately and not merged.
- One improvement: export event records response ID from the same offline audio snapshot, not live transport after rendering. Legacy API preserved. Two new regression tests.
- Verification: 66/66 Linux-container pytest PASS; compileall and ZIP integrity checked. Native ASUS Windows hardware/audio and five-scene acceptance UNVERIFIED; VELA NOT COMPLETE.
- Rollback: extract canonical M2.18 separately; no FID or source media migration.
- Next: native ASUS audition/export acceptance, then review parallel M2.18(1) before any consolidation.

## 2026-11-21 — M2.20 queued audition identity guard
- Parent: immutable M2.19; 73/73 parent SHA-256 manifest entries matched, 66/66 baseline tests passed.
- One improvement: prevent exporting a different approved response if queue identity changes while the WAV save dialog is open. Optional expected_response_id is checked under the transport lock during snapshot. No output/event on mismatch; legacy API remains supported.
- Verification: 68/68 Linux-container pytest tests PASS, two new regression tests; Python compileall and ZIP integrity PASS. Native ASUS Windows audio/GUI/drivers and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.19 separately; no media/FID migration.
- Next: real ASUS Windows GUI and playback acceptance.

## 2026-11-21 — M2.21 scheduled audition boundary consistency
- Parent: immutable M2.20; parent ZIP integrity and 76/76 SHA-256 entries verified; baseline pytest 68/68 PASS.
- One improvement: optional expected_pending_at is checked under the same transport lock as expected_response_id, so a rescheduled approved response cannot silently export at a different phrase boundary while the save dialog is open. The GUI supplies the captured pending frame. Legacy API calls remain valid.
- Verification: 70/70 Linux pytest PASS, two new regression tests; Python compileall PASS; native ASUS Windows startup, audio, drivers, microphone, GPU and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.20 into a separate directory; no FID or source media migration.
- Next: non-destructive real-device Windows GUI/audio audition acceptance on ASUS.

## 2026-11-21 — M2.22 coherent audition request capture
- Parent: immutable M2.21, SHA-256 `3e64e2e761737ab385075d9f1ce47958ec0a9e5e23dedecdb035e63528d8fc04`; 84/84 manifest entries verified, baseline 70/70 passed.
- One improvement: capture audition duration and expected response identity/boundary under one reentrant lock before the save dialog, eliminating the inter-read callback race. Existing approval and source/FID unchanged.
- Verification: 71/71 Linux pytest passed; compileall passed. Windows hardware, drivers, GUI and five-scene acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.21 separately. Next: native ASUS audition acceptance.

## 2026-11-22 — M2.23 exclusive audition export
- Parent: immutable M2.22, SHA-256 `087e064880a76796360519260809c13d8225f38678ca51ab6cbca4dcd825bcbc`; 82 manifest entries verified, baseline 71 tests passed.
- One improvement: queued audition WAV export uses exclusive file creation, preserving existing recordings even if a destination appears during rendering. No history event on collision; other export APIs unchanged.
- Verification: Linux pytest 72 passed; compileall passed. Windows GUI/audio/drivers and five-scene acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.22 separately; no media or FID migration. Next: native ASUS audition acceptance.

## 2026-11-22 — M2.24 failure-safe audition publication
- Parent: immutable M2.23, SHA-256 `57c0b5a1db1413204509c86c280d636d9b8f84d01354ed2a5f1adfc49bce2e46`; ZIP integrity and all 85 source-manifest entries verified; 72 baseline tests passed.
- One improvement: encode approved queued-response WAV into a uniquely named temporary sibling, flush and close it, then publish by exclusive hard link. Existing recordings are never replaced. Unsupported link operations fail closed. Temporary file removed on handled failures; abrupt process termination may leave a `.tmp` file but cannot expose an unfinished final WAV during encoding. History is written only after publication and cleanup. Other exports, approval workflow, transport, FID schema and source media unchanged.
- Verification: 75 Linux-container tests passed (three new cases: failed encoder, late destination collision, unsupported link); Python source compilation passed. Windows filesystem/link support, native GUI, physical audio, drivers, microphone, GPU and complete five-scene acceptance remain UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.23 into a separate directory. No media/FID migration. Next: non-destructive real ASUS audition acceptance, including destination filesystem support.

## 2026-11-22 — M2.25 reversible selected-bar edit
- Parent: immutable M2.24, SHA-256 `f6c352deaabbb24413a7d2f1d339f3dbb5191c4f2b97f7e66237ef6629c7bb84`; ZIP integrity and 88/88 manifest hashes verified; fresh baseline 75 tests passed in 1.60s.
- One improvement: human-triggered -6 dB selected-bar attenuation on the inspected deck, with short gain ramps, derived WAV/object provenance, recorded exact original sample range, and one-step undo from verified previous audio/deck metadata, including after FID reopening. Original media remains unchanged. Editing requires paused playback and no in-flight response render. No AI proposal acceptance or cross-project integration added.
- Verification: 78/78 Linux pytest passed; source compilation PASS; real Tk GUI edit/undo under Xvfb PASS; screenshot captured. Offline transport output matched its existing limiter applied to edited samples. Native Windows startup, physical audio, drivers, microphone, GPU and full five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.24 into a separate directory. No FID schema migration; new historical event fields and graph relationship are additive. Keep original and edited FID copies separate. Next: audible A/B comparison of selected-bar edits with explicit original/edited view, rather than only undo.

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

## 2026-11-22 — M2.29 matched before/after waveform visualization
- Parent: immutable M2.28 (`38d6a36cf3e4300054705f9df2a54de8e2a0cb609af0d0b93ea7f7ea1e05a1b0`); ZIP CRC and 105/105 manifest hashes passed; baseline 84/84 pytest passed.
- One improvement: visible fixed-scale, read-only before/after waveform peaks in native A/B audition dialog. Original audio, new transformations, proposal approval, FID schema and transport remain unchanged.
- Verification: 85/85 Linux pytest passed, one new regression; compileall passed; running Tk reversal → A/B sample playback (simulated device) → Undo passed under Xvfb, with native screenshot receipt. Windows physical audio, drivers, microphone, GPU and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.28 into a separate directory. No FID/media migration. Next: A/B visual scrub/impact marker then real ASUS acceptance.

## 2026-11-22 — M2.30 A/B waveform playback marker
- Parent: M2.29; single change: read-only, clamped cursor on the original/edited waveforms, following the isolated audio render frame position; closes cleanly with audition window.
- Verification: Python pytest and compileall receipt included. The cursor represents frames rendered, not physical speaker output. Windows audio device, driver, microphone, GPU, and five-scene acceptance remain UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.29 separately; no FID/media migration. Next: test cursor behavior in native Tk with simulated output, then Windows device acceptance.

## 2026-11-22 — M2.31 shared sample cue for A/B waveform
- Parent: M2.30 ZIP, SHA-256 `85d36ecdaff9f9d60ba7035ba389cb916237099b88f0e2e5e3e028e7f046e81e`. Retrieved actual original archive from `/VELA/Continuity/`; archive CRC PASS; 119/119 parent SHA-256 manifest entries PASS; baseline 86/86 pytest PASS.
- **Exactly one feature:** clicking the native waveform selects a bounded sample cue; original and edited A/B auditions start from the same selected sample on their next explicit play press. New `BarAudition.select(choice, start_frame=0)` is backward compatible. Cursor immediately reflects cue, then follows rendered-frame progress; clicking stops any current audition. This is deterministic position alignment, not confirmed DAC latency.
- Verification: 88/88 automated tests including 2 new tests; `compileall` PASS; native Linux Tk/Xvfb click → A render → B render → cursor → Stop/Close → Undo smoke PASS using simulated audio-device output, screenshot `demo/VELA_M2_31_native_linux.png`. Original source project and file bytes unchanged.
- Release source checksum manifest and ZIP CRC must match independently. Physical speakers, native ASUS Windows drivers, microphone, GPU and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.30 in a separate directory; do not overwrite FID or source media. No FID migration or integrations.

## 2026-11-22 — M2.32 A/B audition keyboard controls
- Modal A/B window shortcuts: A original, B edited, Space stop, Escape close. No changes to media, FID, or main transport.
- Linux automated tests and compilation passed. Physical Windows audio and native key-event interaction not verified. VELA NOT COMPLETE.
- Rollback: extract M2.31 separately; do not overwrite original media.

## 2026-11-22 — M2.33 A/B modal keyboard isolation
- Parent M2.32 manifest verified. One change: handled modal A/B/Space/Escape keys return Tk `break` to prevent underlying root Space transport action.
- Linux 89/89 tests, Xvfb Tk keyboard interaction and compilation passed. Physical Windows device acceptance unverified. NOT COMPLETE.
- Rollback: extract M2.32 separately, no FID/media migration.

## 2026-11-22 — M2.34 bounded A/B loop-region engine
- Parent: immutable M2.33 (`ab6145b3c9d2e38025602b06f16fe129b10ec47c85424976631ee6eafb6ea4e6`), ZIP CRC verified; 128/128 SHA-256 parent entries verified; 89/89 baseline tests passed.
- Exactly one improvement: opt-in `BarAudition.set_loop_region(start_frame, end_frame)` and `clear_loop_region()` provide half-open, nonempty, sample-aligned A/B repeating intervals in the isolated audition engine. Both versions share the same bounds; switching preserves matched cue semantics. Default one-shot behavior is unchanged. No GUI loop controls in this iteration. No media, FID, main transport, or approvals are written.
- Linux automated tests: 90/90 passed, including one new regression test; Python compilation passed. Physical Windows playback, driver, GPU, microphone, native loop UI and complete five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract M2.33 separately; retain original source media and FID backups. No migration. Next: expose explicit region controls in A/B GUI and native-test with simulated output.

## 2026-11-22 — M2.35 native loop selection
# VELA M2.35 — Native A/B loop-region controls

One improvement: mark loop start at a waveform cue, cue a later endpoint, activate a bounded repeating interval, or clear it to restore one-shot behavior. A and B share sample boundaries. Cues outside an active loop clamp to the loop. No source/FID/media writes or main transport changes.

Verification: parent M2.34 136/136 hashes matched, 90/90 baseline tests passed. Updated 90/90 tests passed; native Linux Tk simulated-device interaction verified loop wrap, matched A/B, clear and close. Python compilation and ZIP integrity checked. Physical Windows drivers/speakers/microphone/GPU and five-scene acceptance unverified.

Rollback: extract immutable M2.34 separately; no project migration. Next: add regression coverage for native loop UI and visualize loop boundaries. VELA NOT COMPLETE.


## 2026-11-22 — M2.36 visible A/B loop boundaries
# VELA M2.36 — Visible A/B loop markers

One change: the A/B waveform now draws a green dashed start marker and a cyan dashed end marker when the user marks an audition loop. Clearing the loop removes both. Markers are view-only and do not affect audio, FID, provenance, or transport.

Verification: M2.35 136/136 source hashes verified; 90/90 baseline tests. M2.36 91/91 automated tests passed on Linux; compilation passed. Native GUI runtime and Windows audio hardware NOT tested in this iteration.

Rollback: extract immutable M2.35 into a separate directory, do not overwrite original audio or FID projects. No migration required.

Next: native Tk interaction test for visual marker lifecycle with simulated output. VELA NOT COMPLETE.


## 2026-11-22 — M2.37 native loop-marker lifecycle regression
- Parent M2.36: 140/140 SHA-256 verified, 91/91 baseline tests.
- One improvement: real Tk/Xvfb regression tests mark start/end, two marker visibility, clear and close using simulated output. No production or FID changes.
- 92/92 tests pass with Xvfb; Python compileall passes. Windows physical hardware unverified.
- Rollback: extract M2.36 separately. Next: verify marker placement at actual sample boundaries and resize behavior. VELA NOT COMPLETE.

## 2026-11-22 — M2.38 waveform resize alignment
- Parent: M2.37 archive retrieved and inspected; 144/144 manifest hashes matched; baseline 92/92 tests passed.
- One improvement: redraw A/B waveform, playback cursor, and sample-boundary loop markers against the actual canvas width on resize; waveform clicks use the same width. No audio/FID changes.
- Linux/Xvfb pytest: 93/93 passed, including resize/sample-boundary regression. Windows speakers, drivers, microphone, GPU and full five-scene acceptance UNVERIFIED.
- Rollback: extract immutable M2.37 separately; no migration, no original media changes. Next: native Tk resize interaction smoke test. VELA NOT COMPLETE.

## 2026-11-22 — M2.39 native Tk resize/loop interaction regression
- Parent M2.38 source ZIP: original SHA-256 manifest verified before changes.
- One improvement: persistent native Tk/Xvfb regression exercising real canvas Configure events at three widths, loop marker sample alignment, and cue selection while loop remains active. Production audio/UI code unchanged; source media and FID untouched.
- Linux/Xvfb automated suite: 94/94 passed; Python compileall passed. Physical Windows audio devices, microphone, GPU and five-scene acceptance NOT verified.
- Rollback: extract immutable M2.38 in a separate directory; no data migration. Next: verify actual Windows audio playback and driver/device selection on target ASUS hardware. VELA NOT COMPLETE.

## 2026-11-22 — M2.40 active loop resize regression
- Parent: canonical M2.39 ZIP, actual source inspected; 94/94 baseline Linux/Xvfb tests passed. Independent MORPH M2.39 branch inspected but NOT integrated.
- One improvement: native Tk test resizes waveform at three widths during active bounded A/B loop playback, checks loop/cue marker positions, preserved sample position and playing state, and wrap after subsequent render. Production code, FID and original media unchanged.
- Linux/Xvfb tests: 95/95 passed. Physical ASUS Windows output, drivers, microphone, MIDI, GPU and five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract canonical M2.39 separately; no migration. Next: physical Windows playback acceptance or explicitly approved MORPH branch reconciliation.
