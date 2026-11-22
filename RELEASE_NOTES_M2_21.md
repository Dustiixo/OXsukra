# VELA M2.21 — scheduled response audition boundary guard

Parent: immutable M2.20.

One change: queued WAV audition export now verifies both approved response ID and the scheduled impact frame when the save dialog returns. A reschedule of the same response during the dialog aborts without writing a WAV or export-history event. `expected_pending_at` is an optional keyword argument; existing callers remain compatible.

Tests: 70/70 pytest PASS on Linux, including two new regression cases; Python compileall PASS. Parent 76/76 manifest hashes matched. No Windows hardware test was performed.

Rollback: extract immutable M2.20 in a separate directory. No FID schema or media migration.

Unverified: ASUS native Windows startup, speaker playback, microphone, audio drivers, GPU, GUI rendering, complete five-scene acceptance. VELA NOT COMPLETE.
