# NEXT ACTION — Actual native Self VM + Morphic slot-edit evidence (G1)

**Start from full v0.2.2 checkpoint and passing tests, not an unrelated demo.**

1. Get a real executable and world built from a **pinned `russellallen/self` commit** on a network-capable scratch system, logging official source commit, VM hash, world/snapshot hash, architecture, OS, build config and license. The current container cannot resolve GitHub and has no Self executable.
2. Run the native Self evaluator on `bytebridge.cli self-export`'s `baseline.self`, open a Morphic outliner for the resultant object, and edit a numeric slot. Capture actual logs/screenshots and a reproducible command sequence, including proof the edited slot is on that exact object rather than a separately typed fixture.
3. Determine a safe native **typed slot exporter** or precise file-out representation. A raw Transporter module will not necessarily match the v0.2.2 strict literal source contract. Build and validate that adapter against real VM output, without granting arbitrary Self code execution to Python.
4. Independently verify the serialized observed slot and runtime fingerprint before an `OX_SELF_SLOT_OBSERVATION/2` receipt can claim `nativeSelfVerified`. The current receipt has no such field or claim: it is operator-attested and must stay labeled as such.
5. Complete signed source import → review → explicit commit → revisioned 3D/audio render on real native evidence. Keep original-byte hash, representation print, 1000 splices and all previously accepted tests invariant. Add adversarial tests and allow-lists for new native file-out grammar.
6. Optionally explore learned BLT using pinned Meta upstream, but measure model outputs separately from entropy-heuristic patches; never label a heuristic learned.

**If VM blocked again:** do not ship another synthetic version just to increase a version number. A real upstream VM/world or independently verifiable capture is the current promotion gate.
