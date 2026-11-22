# GitHub Publication Status

This file is a publication gate, **not** evidence that the ecosystem is already pushed or integrated.

Audit baseline: 2026-11-22, connected GitHub account `Dustiixo`. The public `OXsukra` default branch contained only `LICENSE` when checked. `Cubix` had a checkpoint document and a license; `SpatialDoor`, `HermesXO`, `Aixo-` and `OdysseusXO` were primarily README/license placeholders. `OXsukra` PR #4 contains reference governance-router code on a review branch, deliberately unmerged pending integration acceptance. The audit does not modify that review gate.

**No private source, credentials, user files, or arbitrary checkpoint ZIPs should be published without review.** Preserve each component's ownership and Git history. Do not treat a design document, source archive, branch commit, test log, default-branch merge, or live installation as interchangeable evidence.

Run `python -m unittest discover -s tests -v` for local auditor tests and `python tools/check_publication.py` to inspect the selected public default branches through GitHub's API. The latter is read-only and uses no token; GitHub API rate limits or network failures show explicit error states. `HAS_OTHER_FILES_UNVERIFIED` means only that non-placeholder files are present, not that the actual project's source or tests are published.

Independent repository targets waiting for verified source import: IXO, VELA, PARALLAX, DeepBrew Studio, OX Ripple, OX Treasury, Underbyte, Opris and ECHOFOLD.VME. These are backlog names, not claims that the repositories exist, have been published, or are fully implemented. Add canonical source checkpoint provenance, license, reproducible tests and an exact commit link to each project's own repo before marking it published.
