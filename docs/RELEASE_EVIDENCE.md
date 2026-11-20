# Source, status and release evidence policy

Status terminology:

- **Concept:** specified intent; no inspected executable source claimed.
- **Source-inspected:** exact code/commit located and analyzed.
- **Checkpointed:** source snapshot and repeatable reference retained.
- **Tested-on-host:** tests/effects observed on a named host/revision.
- **Integrated-on-host:** one actual owner-to-owner effect observed, including
  permissions, restart, failure and recovery.
- **Unverified:** insufficient or conflicting evidence. This is a useful
  result, not a failure to be hidden.

Historical intake labels (`HOST`, `PACKAGE`, `STAGED`, `DESIGN`) are
not substitutes for these release states. Mockups and old screenshots cannot
move software to a stronger status.

## Reproduced source checkpoints, 2026-11-20

| Source | Exact revision | Local verification | Unproven |
| --- | --- | --- | --- |
| Private IXO M0 Git bundle | `1d1ae62` (ancestor `8d3c643`) | `python -m unittest discover -s tests -q` → 5 passed | Pinned StardustXR graphics interaction, native UI and installed IXO |
| Archived IXO engineering v0.4.1 ZIP | Packaged Python source, distinct from M0 Git branch | Same command → 152 passed | Latest installed ASUS worktree, GUI, autonomous native adapters |
| Original Cubix M0.1 Git bundle | `d2c4c36` (ancestors `cb27ab6`, `47652f7`) | Same command → 18 passed | Import preserving original Git history and rerun on published checkout |

Those commands were run in an isolated managed Linux workspace. The archives
remain owner-held; they have **not** been published in this public repository.
The numbers are tests within each source, not a combined product score.

## Before a source release or merge

1. Identify owner, authoritative revision, original ancestry and licence.
2. Review diffs and scan for secrets, private conversations, device backups,
   personal financial records, copyrighted media and model weights.
3. Confirm tests and real effect on named OS/hardware; independently record
   fail/skip cases as well as passes.
4. Define exact permission boundary, source revisions and rollback receipt.
5. Publish to the correct repository via a **review branch and PR**. The
   private canonical IXO is not to be restored into this public umbrella.
6. Promote status only after a real end-to-end acceptance, including reboot,
   offline and rejection paths where relevant.

The next hard IXO gate remains a verified original host source lock, followed
by one native source-to-visual read-only path. Full integration follows
owner-signed contracts, not an appealing representation.
