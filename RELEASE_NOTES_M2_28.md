
## 2026-11-22 — M2.28 reversible bar reversal
- Parent: VELA_Continuity_M2_27_2026-11-22.zip, SHA-256 `dfab556955f304e3b624e8b7c40c3d4e9f4837f8d514700bb22d3f9eefd5efa0`; ZIP and 102 manifest hashes verified; baseline 82 tests passed.
- Human-triggered selected-bar reversal with 5 ms edge blends, unchanged outside samples, derived object relationship, matched A/B and single-step undo after FID reopening. Legacy attenuation API retained.
- Linux pytest 84 passed in 1.76s; compileall passed. GUI wiring added but not exercised in this run; physical playback and Windows device acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.27 separately; retain original FID copies; no schema migration. Next: exercise reverse and A/B controls in running Tk.
