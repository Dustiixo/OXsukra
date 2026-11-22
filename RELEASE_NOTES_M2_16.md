# VELA M2.16 — exact-boundary response commit

Parent: immutable M2.15. One transport correctness improvement: the approved response is committed at the exact scheduled frame even if the audio callback ends on that frame. The new response is first audible in the following buffer, with no premature sample output; the applied event is timestamped at the target frame and emitted once. No changes to approval, FID schema, original media, five-scene roadmap or project identities.

## Rollback
Extract immutable M2.15 ZIP into a separate directory; do not overwrite user projects or original audio. No migration required.

## Unverified
Automated Linux-container tests only; ASUS Windows startup, physical playback, drivers, microphone, GPU and complete five-scene acceptance remain UNVERIFIED. NOT COMPLETE.
