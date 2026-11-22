# Provenance and invariant inventory — v0.2.2

Parent: `OX_Spatial_Fabric_v0.2.1_SELF_RECEIPT_TESTED.zip`, already saved in ChatGPT Library `/OX_Spatial_Fabric/Continuity/`. Baseline independently executed before edits: 61/61 Python tests and existing 8 splice + 9 byte JavaScript test groups. Parent is itself an additive continuation of v0.2.0 and original OX Morph Lab/Spatial Fabric v0.1.1. No protected repositories were changed.

v0.2.2 changes: `bytebridge/self_exchange.py`; backwards-compatible `OX_SELF_SLOT_OBSERVATION/2` handling in `bytebridge/self_receipt.py`; CLI commands `self-export`, `self-stage`, and candidate-bound `self-import`; `tests/test_self_exchange.py`; synthetic handoff example; native gate docs and test report. Existing `engine.py`, spatial 3D/sonification algorithms, UI assets, Self reference expression, and previous test suites are retained.

The signed receipt has **two distinct source hashes**: `sourceSha256` for original raw input and `objectSourceSha256` for edited Self text, plus `baselineSourceSha256`, representation print, base revision and head. Signing alone is not proof of VM execution. This format preserves a strict one-slot textual delta, not arbitrary Self file-out module parsing.

The local runtime lacked a native Self executable and direct `git ls-remote https://github.com/russellallen/self.git` failed DNS resolution. Source repo/build instructions verified separately from the public handbook; no upstream revision or binary hash is fabricated.
