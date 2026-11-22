# VELA M2.5 — case-insensitive FID member collision guard

Parent: immutable M2.4. One change: refuse ZIP member paths that collide under Unicode casefolding before extraction, preventing two entries from resolving to the same file on case-insensitive filesystems. Existing FID schema and source media are unchanged.

## Verification
The M2.4 source manifest was checked before modification and its baseline pytest suite passed. The updated Linux-container test suite passed with two new regression tests. This is NOT Windows hardware, driver or playback acceptance.

## Rollback
Extract the original M2.4 ZIP into a separate directory; do not overwrite a working installation. No existing projects or media were migrated.
