# VELA M2.25 — reversible bar attenuation
## M2.25 update (2026-11-22)
- Human-selected audio-object bar attenuation (-6 dB, 5 ms edge ramps where length permits) and single-step undo, including after FID reopening. Pause playback and wait for any response rendering to finish, inspect a loaded deck, select a point, click SELECTED BAR −6 dB, then play. Pause and click UNDO BAR EDIT to restore the previous deck. Original recordings stay intact. The edit uses constant four-beat bars at current transport BPM, not automatic beat detection. No new FID schema or external integration. Existing pending audio responses are not rescheduled. Windows hardware acceptance outstanding.


## 2026-11-22 — M2.25 reversible selected-bar edit
- Parent: immutable M2.24, SHA-256 `f6c352deaabbb24413a7d2f1d339f3dbb5191c4f2b97f7e66237ef6629c7bb84`; ZIP integrity and 88/88 manifest hashes verified; fresh baseline 75 tests passed in 1.60s.
- One improvement: human-triggered -6 dB selected-bar attenuation on the inspected deck, with short gain ramps, derived WAV/object provenance, recorded exact original sample range, and one-step undo from verified previous audio/deck metadata, including after FID reopening. Original media remains unchanged. Editing requires paused playback and no in-flight response render. No AI proposal acceptance or cross-project integration added.
- Verification: 78/78 Linux pytest passed; source compilation PASS; real Tk GUI edit/undo under Xvfb PASS; screenshot captured. Offline transport output matched its existing limiter applied to edited samples. Native Windows startup, physical audio, drivers, microphone, GPU and full five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.24 into a separate directory. No FID schema migration; new historical event fields and graph relationship are additive. Keep original and edited FID copies separate. Next: audible A/B comparison of selected-bar edits with explicit original/edited view, rather than only undo.

Screenshot: demo/VELA_M2_25_native_linux.png (actual Tk window under Xvfb; synthetic two-bar source; no audio device). Reproduce with `PYTHONPATH=. xvfb-run -a -s "-screen 0 1440x900x24" python demo/verify_bar_edit_linux.py` (requires Pillow with X11 support, Tk, Xvfb and dependencies). No trained model claim. Undo is single-step per current edit, not a general multi-step edit history.
