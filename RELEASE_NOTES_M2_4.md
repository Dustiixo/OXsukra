# VELA M2.4 — cross-platform FID member name guard

Parent: immutable M2.3. One change: before extraction, reject archive member basenames that Windows may interpret differently from Linux, including device names, alternate-data-stream colons, backslashes, trailing dots/spaces, and control characters. This prevents ambiguous extraction paths. FID schema and source media are unchanged.

## Verification
Parent: 40/40 SHA-256 manifest entries matched; 21/21 pytest passed. New build: 27/27 pytest passed in Linux container; 6 regression cases (five unsafe names, one safe roundtrip). This is NOT Windows filesystem or real-device verification.

## Rollback
Extract the original M2.3 ZIP into a separate directory and use that version; no migrations or writes to user projects are performed by this change.
