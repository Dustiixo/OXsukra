# OX Spatial Fabric changelog

## v0.2.2 — 2026-11-21 — controlled Self source handoff

- New deterministic, revision-bound Self object source export and manifest.
- Exact single bounded numeric edit acceptance; all other text/structure rejects.
- New signed source-evidence receipt schema `/2`; retain `/1` compatibility.
- CLI `self-export`, `self-stage`, and source-bound `self-import` → manual commit → render, with adversarial tests and demo hashes.
- Fixed precision loss for small/high-precision numeric ledger slots in exported Self literals.
- Baseline 61 Python tests expanded to 77 passing; 17 existing JS groups continue passing.
- Native Self VM/world/Morphic remains **BLOCKED**, not falsely promoted.

## v0.2.1 — 2026-11-21 — operator-attested receipt importer

- Added read-only HMAC-signed Self observation ingest; replay and revision checking; review-only proposal; 61 Python tests and 17 JavaScript groups reported. No native Self VM proof.

## v0.2.0 — 2026-11-21 — byte-first spatial bridge

- Preserved v0.1.1 audio-splice application, added raw-byte lossless ledger, heuristic dynamic patches, 1000 index splices, self-literal candidate, versioned OBJ and WAV projections, and proposal/commit mapping ledger. 50 Python tests and 17 JavaScript groups reported.

## v0.1.1 — 2026-11-21 — inherited retested spatial audio baseline

- 23 Python tests and 8 JavaScript groups in original independent retest; silence and selected-object DOM defects fixed. Self runtime untested. Original retest retained in `TEST_REPORT_v0.1.1.md`.
