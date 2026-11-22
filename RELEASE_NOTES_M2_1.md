# VELA M2.1 — FID deck provenance guard

Parent: `VELA_Continuity_M2_2026-11-20.zip`. One change: reject a `.fid` whose deck WAV content differs from its stored `sha256_pcm_wav`, even when no object graph is present. FIDs without this optional field remain loadable. No project schema or UI changes.

## Test receipt
- Original archive manifest: 35/35 SHA-256 matched.
- Baseline: 15 passed (`python -m pytest -q`).
- M2.1: 17 passed (`python -m pytest -q`), including two new legacy FID regression tests.
- Execution: Linux container, Python pytest; no real Windows driver/audio acceptance.

## Rollback
Keep parent archive unchanged. Replace M2.1 source with parent M2 ZIP if necessary. No original media or existing `.fid` files were modified.
