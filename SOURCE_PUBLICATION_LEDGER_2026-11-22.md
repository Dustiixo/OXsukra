# OXsukra public source publication ledger

**Audited 2026-11-22.** Source branches are publicly accessible under the authenticated GitHub owner `Dustiixo`; this does **not** mean all projects are independent GitHub repositories or promoted releases.

Twelve **review/staging** branches contain **628 source/artifact files**. A direct GitHub tree audit compared each uploaded file's remote Git blob SHA with SHA-1 calculated over the sanitized local source bytes: **628/628 matched**, with no extra or missing branch blobs. The public root `main` holds this index and the read-only audit harness; the source branches stay separate. No force pushes or existing PR merges were made.

| Candidate | Git blobs | Public source branch | Commit | Test evidence |
|---|---:|---|---|---|
| VELA M2.40 | 124 | [publish/vela-m2-40-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/vela-m2-40-source-20261122) | `bcac1c52028e` | 95 pytest under Xvfb; staged source PASS |
| OX Treasury v0.17 | 48 | [publish/ox-treasury-v0-17-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/ox-treasury-v0-17-source-20261122) | `712611ca9937` | 93 unittest; staged source PASS |
| FlowMesh M0.6 | 77 | [publish/flowmesh-m0-6-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/flowmesh-m0-6-source-20261122) | `253e62f498b1` | 47 core and 4 visual tests staged PASS; 6 spatial BLOCKED |
| Underbyte web v0.9 | 11 | [publish/underbyte-v0-9-web-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/underbyte-v0-9-web-source-20261122) | `deb021f3bdf0` | Original archive evidence only; staged native tests NOT RUN |
| OX Ripple v0.42 public subset | 88 | [publish/ripple-v0-42-public-subset-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/ripple-v0-42-public-subset-20261122) | `3cf928efc80f` | 48 original coordinator tests PASS; public-only subset not independently runnable |
| Cubix M0.1 | 24 | [publish/cubix-m0-1-recovered-20261122](https://github.com/Dustiixo/Cubix/tree/publish/cubix-m0-1-recovered-20261122) | `d85891751705` | 18 unittest PASS; complete three-commit bundle retained |
| AIXO local bridge M0.2 | 28 | [publish/aixo-local-bridge-m0-2-20261122](https://github.com/Dustiixo/Aixo-/tree/publish/aixo-local-bridge-m0-2-20261122) | `5732a63c226f` | 48 unittest; staged source PASS |
| PARALLAX Linux M0.7 + Session Atlas M0.1 | 42 | [publish/parallax-linux-m0-7-session-atlas-m0-1-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/parallax-linux-m0-7-session-atlas-m0-1-20261122) | `2bc3cf207c11` | 9 Python host, 7 Node atlas and 2 extension/content scripts PASS |
| IXO engineering v0.4.1 | 99 | [publish/ixo-v0-4-1-engineering-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/ixo-v0-4-1-engineering-source-20261122) | `9c9b32b1caf8` | 152 Python unittest on source archive PASS |

| SpatialDoor v0.1 | 22 | [publish/spatial-door-v0-1-source-20261122](https://github.com/Dustiixo/SpatialDoor/tree/publish/spatial-door-v0-1-source-20261122) | `d60152c3ce5e` | 50 unittest under Xvfb passed; remote SHA match 22/22 |
| DeepBrew Studio G0.3.1 | 49 | [publish/deepbrew-studio-g0-3-1-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/deepbrew-studio-g0-3-1-source-20261122) | `956a27d254bc` | Python compileall passed; Godot test report historical, NOT independently rerun |
| ECHOFOLD Ocean G0.1 | 16 | [publish/echofold-ocean-g0-1-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/echofold-ocean-g0-1-source-20261122) | `1d7e963c4737` | 5 Python unittest passed; remote SHA match 16/16 |

## Important limits

1. **Source publication is not functional completion.** Production native Windows/ASUS acceptance, device integrations, cross-owner contracts, 3D GPU acceptance, and full release approvals remain separate gates.
2. **Source isolation:** VELA, Treasury, Ripple, FlowMesh, Underbyte, PARALLAX and IXO are currently staged as separate public branches of `OXsukra`, **not** as individually named repositories. This is temporary because the connected GitHub action surface cannot create new repositories. Do not merge their trees into `main` as one product.
3. **Safety:** no audio recordings, credential files, runtime databases, private Ripple registry, or local private user data were published. The omitted files mean some demos/tests cannot run from public source alone. The source was checked for obvious secret and personal-path patterns; this is not a formal secret-scanning certification.
4. **Cubix history:** original Git bundle HEAD `d2c4c36ad85c9ec75077c302e437d678a3c51658`; original three commits are preserved inside the branch under `history/`. The uploaded branch's snapshot SHA differs from original ancestry by design; no existing `main` history was overwritten.
5. **Review gate:** governance router [PR #4](https://github.com/Dustiixo/OXsukra/pull/4) intentionally remains unmerged until independent source and owner-boundary acceptance.
6. **Unreconciled work:** native/current IXO source history, HermesXO owner source, full AIXO engine, DeepBrew Studio independent source, Opris, ECHOFOLD, GREMLIN, WRAP, and other ecosystem projects require exact source, license, privacy and test reconciliation. Existing README-only repositories are not counted as published implementations.

For each project: create or select its correctly named repository, validate licensing and lineage, import the source without overwriting existing history, run tests on the resulting tree, open a reviewed PR, and only then promote to its default branch. This ledger is designed to make progress measurable, not substitute for those steps.

## Publication follow-through

An hourly evidence-first GitHub publication workflow is active to reconcile the remaining source archives and repo boundaries. It must skip unchanged digests and must not bypass licensing, privacy, testing, author-ownership or release acceptance. This task is still **incomplete**: outstanding dedicated repositories and owner-controlled integrations cannot be declared complete based on source snapshots.
