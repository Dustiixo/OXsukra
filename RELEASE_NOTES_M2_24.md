# M2.24 — Failure-safe audition export

## 2026-11-22 — M2.24 failure-safe audition publication
- Parent: immutable M2.23, SHA-256 `57c0b5a1db1413204509c86c280d636d9b8f84d01354ed2a5f1adfc49bce2e46`; ZIP integrity and all 85 source-manifest entries verified; 72 baseline tests passed.
- One improvement: encode approved queued-response WAV into a uniquely named temporary sibling, flush and close it, then publish by exclusive hard link. Existing recordings are never replaced. Unsupported link operations fail closed. Temporary file removed on handled failures; abrupt process termination may leave a `.tmp` file but cannot expose an unfinished final WAV during encoding. History is written only after publication and cleanup. Other exports, approval workflow, transport, FID schema and source media unchanged.
- Verification: 75 Linux-container tests passed (three new cases: failed encoder, late destination collision, unsupported link); Python source compilation passed. Windows filesystem/link support, native GUI, physical audio, drivers, microphone, GPU and complete five-scene acceptance remain UNVERIFIED. VELA NOT COMPLETE.
- Rollback: extract immutable M2.23 into a separate directory. No media/FID migration. Next: non-destructive real ASUS audition acceptance, including destination filesystem support.

This is namespace-atomic publication, not a power-loss durability guarantee. On abrupt termination an orphan `.vela-audition-*.tmp` may remain; do not delete while any export is active.
