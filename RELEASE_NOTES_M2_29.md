# VELA M2.29 — Read-only matched A/B waveforms (2026-11-22)

## Parent and scope
- Parent: immutable `VELA_Continuity_M2_28_2026-11-22.zip` (SHA-256 `38d6a36cf3e4300054705f9df2a54de8e2a0cb609af0d0b93ea7f7ea1e05a1b0`).
- Actual parent manifest: 105/105 SHA-256 entries matched; ZIP CRC passed. 84/84 baseline pytest tests passed in Linux.
- Exactly one user-facing improvement: the existing A/B listening dialog renders the original and edited stereo waveform peaks on a common, fixed full-scale amplitude scale. Reversal and attenuation can be inspected without modifying transport, files, history, or proposals.
- No FID schema migration, audio rescheduling, model approval, media modification, or cross-project integration.

## Verification
- `python -m pytest -q`: 85 passed, 1 new read-only waveform-envelope regression.
- `python -m compileall -q vela tests`: passed.
- `PYTHONPATH=. xvfb-run -a -s '-screen 0 1700x1100x24' python demo/verify_reverse_ab_linux.py`: passed. Real native Tk reverse button, original/edited visual envelopes, simulated A/B output sample equality, stop/close, undo and preservation checks executed.
- `demo/VELA_M2_29_native_linux.png` is an actual screenshot from the Linux Tk application under Xvfb, not concept art. Audio output was simulated, not played on speakers.

## Acceptance limits
- Native ASUS Windows UI, real playback and driver/stream coexistence, microphone, GPU and complete five-scene workstation remain UNVERIFIED. `sounddevice` was unavailable in this Linux test container. VELA NOT COMPLETE.

## Rollback
- Extract the immutable M2.28 archive into a separate folder. Existing FID files and source media do not require migration. Never overwrite production media.

## Next milestone
- Offer an explicit visual scrub marker for A/B listening so users can locate the selected bar change while previewing, then validate on ASUS hardware separately.
