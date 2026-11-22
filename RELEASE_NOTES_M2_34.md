# VELA M2.34 — Isolated A/B loop-region engine

## 2026-11-22 — M2.34 bounded A/B loop-region engine
- Parent: immutable M2.33 (`ab6145b3c9d2e38025602b06f16fe129b10ec47c85424976631ee6eafb6ea4e6`), ZIP CRC verified; 128/128 SHA-256 parent entries verified; 89/89 baseline tests passed.
- Exactly one improvement: opt-in `BarAudition.set_loop_region(start_frame, end_frame)` and `clear_loop_region()` provide half-open, nonempty, sample-aligned A/B repeating intervals in the isolated audition engine. Both versions share the same bounds; switching preserves matched cue semantics. Default one-shot behavior is unchanged. No GUI loop controls in this iteration. No media, FID, main transport, or approvals are written.
- Linux automated tests: 90/90 passed, including one new regression test; Python compilation passed. Physical Windows playback, driver, GPU, microphone, native loop UI and complete five-scene acceptance UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract M2.33 separately; retain original source media and FID backups. No migration. Next: expose explicit region controls in A/B GUI and native-test with simulated output.
