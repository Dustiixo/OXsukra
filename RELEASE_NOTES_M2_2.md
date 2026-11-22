# VELA M2.2 — generated response provenance

Parent: VELA M2.1. One code improvement: record and validate optional `sha256_pcm_wav` on generated response media, including FIDs without object graphs. No schema change; legacy responses without digest remain compatible.

## Verification
19/19 `python -m pytest -q` passed in Linux container. No Windows hardware, playback or driver acceptance.

## Rollback
Restore unchanged M2.1 source ZIP. No destructive operations or media migrations performed.
