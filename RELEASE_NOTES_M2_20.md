# VELA M2.20 — queued response export identity guard

Parent: immutable M2.19.

One change: the explicit queued-response WAV export captures the approved response identity before the save dialog, and the offline audition API validates that identity atomically with its audio snapshot. If the pending response changes while the dialog is open, export aborts without writing audio or recording a misleading event. The optional expected_response_id parameter preserves the old API.

No automatic proposal approval, FID schema change, source media rewrite, or cross-project integration.

Rollback: extract immutable M2.19 ZIP into a separate folder. No data migration.

Native ASUS Windows startup, audio drivers, speaker playback, microphone, GPU and full five-scene acceptance remain UNVERIFIED. VELA NOT COMPLETE.
