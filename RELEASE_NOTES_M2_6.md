# VELA M2.6 — Unicode-normalized FID member collision guard

Parent: immutable M2.5. One change: reject ZIP member names colliding after Unicode NFC normalization and casefolding before extracting any data. This protects cross-platform FID extraction from equivalent composed/decomposed Unicode filenames. The FID schema, source audio and existing projects are unchanged.

## Verification
M2.5 source manifest 44/44 PASS; M2.5 baseline 29/29 PASS; M2.6 Linux-container tests 31/31 PASS, including two new regressions. Windows device, driver, microphone and playback acceptance NOT VERIFIED.

## Rollback
Restore immutable M2.5 archive into a new directory; no project migration or destructive writes were performed.
