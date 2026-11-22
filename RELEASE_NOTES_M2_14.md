# VELA M2.14 — GUI phrase entry selection

Parent: immutable M2.13. Single feature: selectable response quantization (1, 2, 4, 8 bars) in Tk sidebar. Legacy default 1 bar. Selection is validated before proposal acceptance or response mutation. The scheduled project event records phrase_bars and target_seconds. No FID schema or media modifications. No cross-project integration.

## Rollback
Extract M2.13 into a fresh directory and launch it. Do not overwrite projects or source audio. No migration required.

## Limitations
Automated Linux tests only. No ASUS Windows startup, actual speaker playback, driver, microphone, GPU or five-scene acceptance verified. NOT COMPLETE.
