# VELA M2.36 — Visible A/B loop markers

One change: the A/B waveform now draws a green dashed start marker and a cyan dashed end marker when the user marks an audition loop. Clearing the loop removes both. Markers are view-only and do not affect audio, FID, provenance, or transport.

Verification: M2.35 136/136 source hashes verified; 90/90 baseline tests. M2.36 91/91 automated tests passed on Linux; compilation passed. Native GUI runtime and Windows audio hardware NOT tested in this iteration.

Rollback: extract immutable M2.35 into a separate directory, do not overwrite original audio or FID projects. No migration required.

Next: native Tk interaction test for visual marker lifecycle with simulated output. VELA NOT COMPLETE.
