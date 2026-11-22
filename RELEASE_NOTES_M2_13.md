# VELA M2.13: Phrase-aware response entry

Parent: M2.12 SHA-256 `43ce226770ebc4bb11e54d937130bd1f95fd1f775f46520fe0a45b8ab3d43e51`.

One functional change: `Transport.queue_response(..., quantize_bars=1)` now optionally schedules an approved generated audio layer at the next 2-, 4-, or 8-bar phrase boundary. Default remains next bar. Invalid quantization is rejected before changing the pending queue. The transport still requires the host/human to explicitly queue a proposal; no automatic approval.

The existing sample-accurate callback splits its rendering at the scheduled boundary. No `.fid` schema, media, or scene navigation change. This is a transport API capability, not a new GUI control or a demonstrated audio-device test.

Rollback: extract immutable M2.12 ZIP to a separate directory; do not overwrite projects or source recordings. No migration required.

Next: expose phrase selection and precise response-entry feedback in the VELA UI with human approval, then test on native Windows hardware.
