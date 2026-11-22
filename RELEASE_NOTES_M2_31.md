# VELA M2.31 — Shared A/B waveform cue point

**Single new capability:** click within the native A/B waveform to set a shared sample-accurate audition cue. Press **A · BEFORE** or **B · AFTER** to listen from that same position. Clicking the waveform stops current audition; it never begins playback on its own. Cursor updates to the cue immediately and follows subsequently rendered frames. Existing un-cued A/B calls still begin at frame 0.

**Scope and compatibility:** `BarAudition.select(choice, start_frame=0)` adds an optional offset; original call sites remain valid. Validation prevents seeking outside the audition. Main transport, project manifest, original source media, `.fid` schema, approval state and five-scene project boundaries are unchanged. Legacy DeepBrew compatibility labels stay untouched; VELA is independent.

**Verification:** baseline M2.30 (119/119 manifest; 86/86 pytest); updated source (88/88 pytest, Python compilation); Linux virtual-display native Tk click/cue/play/stop/undo smoke with simulated audio and screenshot; release manifest and ZIP checks separately verified. No claim of acoustic speaker synchronization or Windows acceptance.

**Limitations:** the cursor measures frames *rendered*, not sound arriving at the listener; output-device latency, stream coexistence, native Windows startup/audio, microphones, GPU and complete five-scene product are unverified.
