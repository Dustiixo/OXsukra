# Synthetic Self literal handoff fixture (not executed in a VM)

`baseline_rev00000.self` is a generated Self object expression tied to `../example_world`'s revision zero. `edited_depth_rev00000.self` differs in exactly one numeric slot: `depth` 1.2 → 2.25. `manifest.json` contains verified SHA-256 identities.

Both files are **manual static text specimens**, not Transporter module output or native outliner evidence. To run the authenticated chain, create a fresh outside-world key (at least 32 securely random bytes), copy the baseline outside the world, use `self-stage` with the edited copy and stage a receipt. Never reuse the test key from the tests or include a key in any archive.
