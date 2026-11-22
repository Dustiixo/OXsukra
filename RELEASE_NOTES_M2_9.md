# VELA M2.9 release notes — 2026-11-21

One improvement: reject malformed optional `original_binary` provenance records in FID manifests before extraction. Applies to decks, responses, and audio objects; validates dictionary, string path, and string SHA-256 digest. Legacy archives without original source metadata remain compatible. No audio, project identities, FID schema, or external repositories changed.

Rollback: extract immutable `VELA_Continuity_M2_8_2026-11-21.zip` into a separate directory. Do not overwrite user media.

Unverified: native ASUS Windows startup, drivers, microphone, GPU and real playback; five-scene completion.
