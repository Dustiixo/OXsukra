# VELA M2.19 — audition response provenance snapshot

Parent: canonical immutable M2.18 `VELA_Continuity_M2_18_2026-11-21.zip` SHA-256 `1f4e9207d32eac784b9fa235c55c310d04fc868d89795e8bf904cb3de55fcb3b`. The parallel M2.18(1) experiment was inspected but not merged.

One change: the offline queued audition API can optionally return the response ID captured from the same transport snapshot as the rendered audio. The Tk export ledger now records that ID, rather than reading the mutable live transport after WAV rendering. Legacy array-only API calls remain unchanged. This avoids misattributing an audition when live playback advances or a later response is queued during export.

No automatic proposal acceptance, source-media rewrite, FID schema change, cross-project integration, or protected branch push.

Rollback: extract canonical M2.18 into a separate directory; no media or FID migration. Windows/ASUS driver, speaker, microphone, GPU, and five-scene acceptance NOT VERIFIED. VELA NOT COMPLETE.
