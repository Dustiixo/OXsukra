# VELA M2.27 release notes

## 2026-11-22 — M2.27 interactive bar A/B audition
- Parent: immutable M2.26, SHA-256 `f7e35751837a0e9922b3b0ad889016ce213561c474dbb09849492ad1731a63fc`; ZIP integrity and 97/97 source-manifest checks passed, 80/80 baseline tests passed.
- One improvement: explicit modal A/B listening controls for the latest active bar edit on the inspected deck. Matched buffers restart at sample zero with equal fixed 0.65 gain, play once, and stop at the end. Requires paused main playback and no recording; audition uses an independent audio-device adapter and does not write project state, media or proposal approvals. Stop/Close available. A second output stream may be unavailable on some audio devices; the dialog reports errors.
- Verification: 82/82 pytest tests passed, source compilation passed, real Tk controls exercised under Linux Xvfb using a simulated audio device and verified output samples, screenshot captured. sounddevice is not installed in this execution environment; physical playback, native ASUS Windows audio, driver/stream coexistence, microphone, GPU and full five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.26 separately; no media/FID migration. Next: interactive comparison of a second musical transformation (e.g. bar reverse), with reversible provenance and matching audition.
