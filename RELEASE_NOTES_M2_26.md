
## 2026-11-22 — M2.26 read-only bar A/B audition API
- Parent M2.25, SHA-256 `274115f7dae38f5083a9c8748be0a184ecb14984be0443ca77d0e732c7c78b93`; 94 manifest hashes and ZIP verified; baseline 78 tests passed.
- `Project.audition_bar_edit(deck)` returns matching before/after samples for the latest active attenuation, verifies both media identities and bounds, and leaves deck, history and files unchanged. Works after FID reopening. No GUI playback switch yet.
- Linux pytest 80 passed; compileall passed. Windows hardware, GUI integration of this API, physical listening and five-scene acceptance unverified. VELA NOT COMPLETE.
- Rollback: extract immutable M2.25 separately; no FID migration. Next: connect this API to an explicit A/B audition UI.
