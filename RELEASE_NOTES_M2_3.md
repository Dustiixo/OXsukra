# VELA M2.3 — FID symlink import hardening

Parent: M2.2. One change: reject ZIP members marked as Unix symbolic links during `.fid` import before extraction. Regular Unix-mode media remains compatible. No schema or source-media migration.

## Verification
21/21 Python tests passed in Linux container. No Windows filesystem, hardware, audio driver, playback, microphone, or GPU acceptance claimed.

## Rollback
Use immutable M2.2 source ZIP. No project files or user media were changed.
