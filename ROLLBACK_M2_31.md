# Rollback from M2.31

1. Preserve your original `.fid` projects and source recordings in a separate backup location. Never overwrite them with demonstration media.
2. Extract immutable `VELA_Continuity_M2_30_2026-11-22.zip` into a **new** directory, rather than overwriting an M2.31 installation. Parent SHA-256: `85d36ecdaff9f9d60ba7035ba389cb916237099b88f0e2e5e3e028e7f046e81e`.
3. Launch and use the original A/B auditions. The M2.30 `BarAudition.select(choice)` zero-offset behavior is unchanged in M2.31; no FID schema or media migration is required.
4. Retain both archives and their test receipts to audit provenance. Do not merge other OXsukra/DeepBrew/Syntra projects during rollback.

Native Windows audio-device acceptance remains required.
