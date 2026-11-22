# VELA M2.7 release notes

Parent: VELA_Continuity_M2_6_2026-11-21.zip (immutable).

One change: FID imports validate manifest object, deck/response collection types, and entry types before extraction. Invalid metadata raises ValueError. Existing valid FID formats, audio source hashes and five-scene roadmap are unchanged.

Tests: 35/35 Python pytest tests passed in Linux container; four new malformed-metadata cases. No native Windows ASUS, driver, playback, microphone or GPU acceptance performed.

Rollback: use the unchanged M2.6 ZIP in a separate directory. No existing user media or FIDs were modified.
