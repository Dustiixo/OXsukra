# OX Spatial Fabric v0.2.1 test report

Date: 2026-11-21. Baseline: complete v0.2.0 archive (not a fresh implementation).

## Result

- `bash tools/test-all.sh`: PASS, **61 Python tests** (previous 50 plus 11 new receipt tests), and existing JavaScript test groups PASS (8 splice + 9 byte groups).
- Verified synthetic signed receipt: produces proposal, no world revision change until existing manual `commit` is invoked.
- Rejected: replayed nonce, tampered MAC, wrong key, wrong source identity, stale revision, code-like slot, NaN, extra schema field, short signing key, key stored in world directory.
- Original waveform, spatial projection, 1000 splices and byte verification regressions pass.
- Native original Self VM execution: **NOT RUN / BLOCKED**; no VM available in current runtime. Morphic outliner/slot editing **NOT VERIFIED**.
- Learned Meta BLT **NOT RUN**. Existing patcher uses empirical entropy heuristic.

## Trust limitations

HMAC proves a signing key was used, **not** native Self execution or truthful outliner observation. Receipt is an operator-attested claim, not hardware or VM attestation. Replay registry and local files are not protected from malicious same-user modification. No production project was changed. No GitHub push.
