# VELA M2.35 — Native A/B loop-region controls

One improvement: mark loop start at a waveform cue, cue a later endpoint, activate a bounded repeating interval, or clear it to restore one-shot behavior. A and B share sample boundaries. Cues outside an active loop clamp to the loop. No source/FID/media writes or main transport changes.

Verification: parent M2.34 136/136 hashes matched, 90/90 baseline tests passed. Updated 90/90 tests passed; native Linux Tk simulated-device interaction verified loop wrap, matched A/B, clear and close. Python compilation and ZIP integrity checked. Physical Windows drivers/speakers/microphone/GPU and five-scene acceptance unverified.

Rollback: extract immutable M2.34 separately; no project migration. Next: add regression coverage for native loop UI and visualize loop boundaries. VELA NOT COMPLETE.
