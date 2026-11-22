# OX Spatial Fabric v0.2.0: Test evidence

Date: 2026-11-21.

## Source lineage

Library baseline: `/OX_Spatial_Fabric_v0.1.1_TESTED.zip`, original ZIP SHA-256 `cb18358d9bce1a15ad4a3503fca028e25ff5b450d8693169157e42adb23736a2`.

## Positive tests observed

- `python -m unittest discover -s tests -v` **50/50 passed** (inherited Morph Lab, inherited audio/RCLL and new bytes, ledger, render, loopback routes).
- `node tests/test_splice_core.mjs` **8/8 groups passed**.
- `node tests/test_byte_core.mjs` **9/9 groups passed**, including a fixed cross-language metrics fixture.
- `python -m compileall -q ...` and `node --check static/byte.js`: passed.
- `python -m bytebridge.cli ingest examples/synthetic_signal.bin --out examples/example_world`: created and retained exact 5,112 bytes with 74 patches and 1,000 splices.
- `python -m bytebridge.cli verify examples/example_world`: passed, original SHA-256 `e76c2071d3db7a49edb33550d47ceb8397843c635f7769e1b7a5f85a64d9721d`, representation print `888c574abc9e1e8d525597e13437478c41f2c182464376d6c596a99c110be2a8`.
- `python -m bytebridge.cli render examples/example_world`: produced real versioned OBJ, PCM16 WAV and digest receipt. OBJ SHA `b702b48c13dc2a655123a9660adbe13fb2fc2e730736eca52053d9dfef73bf7a`; WAV SHA `4349b72c93cef71efb38eea8aaf52a4abb05bdb8b852847f1ea901c644ab1f55`.
- `python -m bytebridge.cli self-gate examples/example_world`: status **BLOCKED**, no original Self executable available in current environment.

## Negative tests observed

- Missing CSRF and hostile Origin rejected with HTTP 403 (inherited).
- New loopback Host check rejects hostile Host before returning app resources/CSRF state with HTTP 403.
- Byte patch gap, source corruption, patch hash mutation, splice tamper, oversized input and type mismatch rejected.
- Unknown/out-of-bound/NaN mapping slots rejected, stale revision and modified audit events rejected.
- Proposals cannot be committed by the CLI without explicit `--approve`; existing render revision cannot be overwritten.

## Not established

- Running Meta BLT with its learned model or weights: **not performed**.
- Original Self VM parsing, Morphic outliner inspection, Transporter module, Self slot edit → OX receipt: **not performed**.
- End-to-end browser control on the user's target ASUS: **not performed**; original report noted Chromium sandbox restrictions.
- External IXO/VELA/Cleanroom/Sentinel integrations: **not performed**.

This release demonstrates a useful, *limited* byte-to-representation experiment; it does not establish new AI cognition.
