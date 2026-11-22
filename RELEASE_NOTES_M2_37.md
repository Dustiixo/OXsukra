# VELA M2.37 — Native loop-marker GUI regression

One improvement: permanent automated real-Tk test covers cue, mark start, set end, visible two-marker state, clear and close, using simulated output. It guards the existing M2.36 UI without changing production code. Test skips when DISPLAY is absent.

M2.37 native Tk marker lifecycle regression
Parent M2.36: 140/140 manifest entries verified; baseline 91/91 passed.
........................................................................ [ 78%]
....................                                                     [100%]
92 passed in 1.64s
Python compileall: PASS
Xvfb Tk widgets and simulated audio: PASS. Physical Windows audio, driver, GPU and microphone: UNVERIFIED.

No media/FID/provenance changes. VELA NOT COMPLETE.
