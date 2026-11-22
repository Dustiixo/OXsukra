# OX Spatial Fabric v0.2.2 — Independent Evidence Report

Date: 2026-11-21. Parent: exact full v0.2.1 source archive `OX_Spatial_Fabric_v0.2.1_SELF_RECEIPT_TESTED.zip` (SHA-256 `20d567220f20a904b6194ee5ffee4821acccd55eb82ff586c5c2b0f10214d9b5`). **No separate new program; no protected OXsukra/GitHub sources modified.**

## Baseline evidence

- Parent archive: ZIP integrity check passed; 56 regular parent files byte-for-byte match the recovered source checkout.
- Parent acceptance: `bash tools/test-all.sh` ran **61 Python tests**, plus the existing **8 splice and 9 byte JavaScript test groups**; all passed before changes.
- Existing web HTTP integration tests exercise local endpoints; inherited audio/splice regressions retained. Full interactive browser UI was **not** tested end-to-end in this release.

## The new falsifiable vertical slice

- New `bytebridge/self_exchange.py` generates a deterministic Self object expression bound to a specific source hash, representation print, head and revision. `self-export` creates a verifiable, immutable-by-policy baseline and manifest.
- `self-stage` checks an external edited Self-language source against that exact canonical baseline. It accepts **one** numeric delta in `depth`, `twist`, `hue` or `threshold` only. Extra Self code, syntax, altered patch metadata, two edits, changed revision identity or out-of-bounds numbers reject. No source text is executed or dynamically evaluated.
- `OX_SELF_SLOT_OBSERVATION/2` signs the baseline/candidate source hashes, upstream byte identity, representation print, changed scalar, revision/head, nonce and operator runtime metadata. `self-import --candidate` rechecks the exact candidate bytes, HMAC and nonce, producing a **review-only** proposal. Prior `schema/1` receipts remain compatible.
- Explicit `commit --approve` and `render` complete the controlled chain. End-to-end fixture changed mapping `depth` from 1.2 to 2.25, held revision at 0 before approval, then advanced to revision 1. The original asset hash and content print remained unchanged, splice count stayed **1000**, OBJ hash changed and WAV hash remained identical. See `examples/self_literal_exchange/DEMO_EVIDENCE.json` for exact hashes. No signing keys shipped.
- A precision bug in the candidate text formatter was caught and fixed: tiny and high-precision finite values now roundtrip through fixed-point decimal text without silent truncation.

## Final verification

- `bash tools/test-all.sh` after implementation: **77/77 Python tests PASS** (61 inherited + 16 new) and **17/17 JavaScript groups PASS** (8 splice + 9 byte).
- Python compilation and Node `--check` passed through the same test-all command.
- Tests cover positive source staging/review/approval/render plus adversarial multi-slot edit, added method text, patch/header change, NaN, out-of-bounds, non-ASCII, newline differences, stolen/mismatched evidence, missing candidate, replay, stale revision, unauthorized key placement and altered export baseline. Existing v0.2.1 HMAC tests retained.
- Local CLI evidence independently demonstrates source SHA-256 identity, unchanged 1000 splices, review-only import and new OBJ render. It is a *synthetic literal-edit test*; the edit was not performed in a Self VM.

## Explicit unpassed gates / limitations

- **Native Self VM, Self World, Morphic and actual outliner live slot editing: NOT RUN / BLOCKED.** Neither `Self` nor `self` executable was present, and direct GitHub checkout failed `Could not resolve host: github.com`. The Self literal generator has *not* been parser-tested in the original VM.
- The generated expression is not a general Self Transporter file-out parser. Real native serialization may differ; `docs/SELF_NATIVE_GATE.md` documents the exact next proof.
- A signature does not prove a VM ran, and self-reported runtime metadata is not an attestation. Local replay registry is not hardened against an attacker operating as the same OS user. Receipt+nonce+proposal writes are separate files, not a transactional database.
- Learned Meta BLT: **NOT RUN or trained**. Existing entropy heuristic is not learned next-byte prediction, and audible/3D projections are not claims of recovered musical meaning.
- No full browser-assisted UI acceptance in this container, and no live adapters to IXO, VELA, DeepBrew, Opris or ECHOFOLD.

## Release verdict

**ACCEPTED:** controlled source-bound single-slot Self-language literal handoff into the existing authenticated, human-reviewed OX byte/spatial render pipeline.

**NOT PROMOTED:** native Self runtime integration, runtime attestation, Meta BLT and protected downstream integrations. The next substantive step must demonstrate the real Self VM and Morphic/outliner slot-edit provenance. No surrogate source-diff success can satisfy that gate.
