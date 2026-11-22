# Rollback from M2.29

1. Keep `VELA_Continuity_M2_29_2026-11-22.zip` immutable for comparison.
2. Extract `VELA_Continuity_M2_28_2026-11-22.zip` (SHA-256 `38d6a36cf3e4300054705f9df2a54de8e2a0cb609af0d0b93ea7f7ea1e05a1b0`) into a new directory, never over the working folder.
3. Run `python -m pytest -q` before using the restored source.
4. Open a **copy** of any `.fid` project; M2.29 made no FID schema changes and no original recording changes.
5. Revalidate physical audio hardware independently before deployment.

No external repositories or protected branches are involved.
