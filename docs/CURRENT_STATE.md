# CURRENT STATE — OX Spatial Fabric v0.2.2, 2026-11-21

**Implemented and verified locally:** continuation from unmodified v0.2.1 source archive, which passed 61 Python and 17 JS groups before changes. Added a deterministic revision/head-bound Self object literal, one-slot static source diff, source-bound HMAC receipt `OX_SELF_SLOT_OBSERVATION/2`, safe stage/import into existing review-only ledger, and a full manual approval -> revisioned OBJ/WAV render integration test. Legacy `.../1` receipts remain supported. The original asset is preserved bit-for-bit with `SHA-256` and 1000 addressed splices.

**Test results:** see `TEST_REPORT.md` for verified final commands and counts. Tests demonstrate a literal-text fixture, **not** the original Self runtime.

**NOT VERIFIED / BLOCKED:** original `russellallen/self` VM parse, actual world launch, Morphic outliner, live slot-edit export, first-party Transporter format, runner provenance. No Self executable/source available to current container; external source checkout blocked by DNS. `Self` field values in receipt are operator metadata, not an attested origin.

**NOT INTEGRATED:** learned Meta BLT / next-byte entropy patcher, protected IXO/VELA/DeepBrew/ECHOFOLD/Opris adapters, production mutation or external GitHub push. Empirical byte entropy remains only a deterministic heuristic.

**Trust model:** Self source strings are not evaluated. Literal checker allows *exactly one* finite, bounded scalar change and no structural changes. Stage signing key is external to world and source. Receipt `schema/2` covers both baseline and candidate SHA-256, but an operator with the signing key can still forge the claim. Replay protection and ledger are local disk controls, not tamper-proof against a malicious same-user process. Committing requires separate human approval. No protected projects were written.
