# OXsukra public source publication ledger

**Audited 2026-11-22.** Source branches are publicly accessible under the authenticated GitHub owner `Dustiixo`; this does **not** mean all projects are independent GitHub repositories or promoted releases.

Fifteen **review/staging** branches contain **769 source/artifact files**. A direct GitHub tree audit compared each uploaded file's remote Git blob SHA with SHA-1 calculated over the sanitized local source bytes: **769/769 matched**, with no extra or missing branch blobs. The public root `main` holds this index and the read-only audit harness; the source branches stay separate. No force pushes or existing PR merges were made.

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

| Underbyte Native Godot | 22 | [publish/underbyte-godot-native-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/underbyte-godot-native-source-20261122) | `3c0738137393` | 8/10 content tests passed; 2 asset-dependent failed due intentionally withheld media |
| OX Hermes Funnel Pilot v0.8 | 58 | [publish/ox-hermes-funnel-pilot-v0-8-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/ox-hermes-funnel-pilot-v0-8-source-20261122) | `39450690d44a` | Python compileall PASS; full unittest timed out after 15s; test acceptance NOT established |
| OX Spatial Fabric v0.2.2 | 61 | [publish/ox-spatial-fabric-v0-2-2-source-20261122](https://github.com/Dustiixo/OXsukra/tree/publish/ox-spatial-fabric-v0-2-2-source-20261122) | `9f2666807c2a` | Python compileall PASS; full unittest timed out after 15s; test acceptance NOT established |

## Important limits

1. **Source publication is not functional completion.** Production native Windows/ASUS acceptance, device integrations, cross-owner contracts, 3D GPU acceptance, and full release approvals remain separate gates.
2. **Source isolation:** VELA, Treasury, Ripple, FlowMesh, Underbyte, PARALLAX and IXO are currently staged as separate public branches of `OXsukra`, **not** as individually named repositories. This is temporary because the connected GitHub action surface cannot create new repositories. Do not merge their trees into `main` as one product.
3. **Safety:** no audio recordings, credential files, runtime databases, private Ripple registry, or local private user data were published. The omitted files mean some demos/tests cannot run from public source alone. The source was checked for obvious secret and personal-path patterns; this is not a formal secret-scanning certification.
4. **Cubix history:** original Git bundle HEAD `d2c4c36ad85c9ec75077c302e437d678a3c51658`; original three commits are preserved inside the branch under `history/`. The uploaded branch's snapshot SHA differs from original ancestry by design; no existing `main` history was overwritten.
5. **Review gate:** governance router [PR #4](https://github.com/Dustiixo/OXsukra/pull/4) intentionally remains unmerged until independent source and owner-boundary acceptance.
6. **Unreconciled work:** native/current IXO source history, HermesXO owner source, full AIXO engine, DeepBrew Studio independent source, Opris, ECHOFOLD, GREMLIN, WRAP, and other ecosystem projects require exact source, license, privacy and test reconciliation. Existing README-only repositories are not counted as published implementations.

For each project: create or select its correctly named repository, validate licensing and lineage, import the source without overwriting existing history, run tests on the resulting tree, open a reviewed PR, and only then promote to its default branch. This ledger is designed to make progress measurable, not substitute for those steps.

## Work-mode verification receipt — 2026-11-22

**New application source published in this run: 0 files, 0 branches. Publication remains blocked, not complete.** The existing public staging branches were verified without re-uploading them. This receipt supersedes any implication that historical test receipts establish fresh Windows or latest-archive acceptance.

- Basis main: `30e656a7878a3cea10408085610e6d8ceb3d88cd`; all 15 listed source branch heads still match their recorded commits.
- Fresh connector tree comparisons and raw Git blob rehash: **769/769 file references match**, zero missing, extra or mismatched files; **755 distinct blobs**. Git object checks pass for OXsukra, Cubix, Aixo- and SpatialDoor. This proves recovered public-byte integrity, not equivalence to inaccessible original source archives.
- Cubix and SpatialDoor original bundles each contain three commits, validate as complete, and pass a local import/object check. Their original tips remain separate from snapshot branch ancestry. Original history for the other thirteen candidates remains unresolved.
- Current-tree scan matches were reviewed as fictional data/tests or extension identifiers. No live credential was identified by the bounded patterns. Binary/history internals and unavailable private archives are outside that scan; it is not a full privacy certification.
- Only Cubix has a license file in its candidate tree (MIT). Fourteen candidate trees lack one. OXsukra main BSD terms must not be automatically assigned to other independent projects; latest-source attribution and licensing remain gates.

Fresh Windows Python 3.12.14 results on copied public snapshot bytes:

- PASS: main checker 3 tests; Cubix 18; AIXO Bridge 48; FlowMesh core 47 with 1 skipped; IXO engineering 152; SpatialDoor 50; Spatial Fabric 77 plus 8 Node assertions.
- PASS: PARALLAX extension/content assertion scripts and 7 Session Atlas Node tests. Python host dependencies were unavailable.
- FAIL: Treasury v0.17 ran 93 tests with 2 Windows SQLite temporary-directory cleanup errors; ECHOFOLD ran 5 tests with 3 equivalent cleanup errors; Hermes Funnel ran 38 tests with 1 missing-material failure and 1 skipped. Intentionally excluded `MEETING_OVERVIEW.html` is expected by its onboarding test. These results do not change the public source trees.
- NOT RERUN: VELA (missing numerical/audio test dependencies), Underbyte web (no suite in tree), Underbyte Godot (engine/Pillow/media absent), DeepBrew native (Godot/media absent), complete Ripple coordinator (private registry/runtime absent). No full hardware acceptance is claimed.
- A first isolation pass omitted a profile directory and caused environment-only errors for SpatialDoor/IXO. A second pass supplied an empty workspace-local profile; their full suites then passed. Raw logs remain local because they contain machine paths.

**Latest continuity discovery:** VELA **M2.49**, Treasury **v0.29**, Ripple **v0.50**. Their reported hashes are recorded in the manifest and [verification receipt](SOURCE_PUBLICATION_VERIFICATION_2026-11-22.json). Archive bytes were not recovered, so their hashes/tests/privacy/licensing were not independently verified here. Ripple v0.50 review commit `69d63ce909a18f2ee6ef418806a03205a01d3206` is metadata evidence, not application-source publication.

**Exact blockers:**

1. Library access: source-chat reading returns continuity text and sandbox download references, not usable archive bytes. The available browser ChatGPT context could not open the source chat; Library search failed on an initial attempt and one retry. Pages discovery supplied no matching source. Access to the correct Library account or the exact archive files is needed. Prior publication authorization remains valid.
2. Repository creation: connected GitHub tools can write existing repos but expose no create-repository action. The terminal has no GitHub login, and the browser new-repository page requires sign-in. Correctly named dedicated repos therefore cannot be created through the currently authenticated surface. Isolated branches remain an authorized fallback once exact source bytes clear verification.
3. Canonical source and rights: current native IXO, full AIXO engine, HermesXO owner source, Opris, GREMLIN, WRAP and remaining lineages still need exact authoritative archive/history and attribution evidence. Historical Downloads matches were not promoted to canon. Hermes Funnel and HermesXO, IXO historical engineering and native IXO, and Underbyte browser/native histories remain distinct.

**Changes authorized on main:** ledger, manifest and this verification receipt only, as a single additive commit using the current main as parent and a non-force expected-SHA lease. No source promotion, release, duplicate source branch, history rewrite, private asset upload, PR #4 merge or MORPH merge is authorized by this receipt.

Resume by recovering the exact archives and checking their hashes, provenance, licenses, assets and sanitized-tree tests. Skip already-published digests; preserve project boundaries. [Machine-readable receipt](SOURCE_PUBLICATION_VERIFICATION_2026-11-22.json) includes per-project tree SHAs, counts, fresh test scopes, typed authority edges and coverage limits.


### Independent candidate gate: OX Treasury v0.29 (2026-11-23 UTC)

- Library source: `/OX Treasury/Continuity/OX_Treasury_v0_29.zip` (60 ZIP members); SHA-256 `47ee68d23dd21b72f5dfc1c816c140210e1f51fb146db838123c93f72a3db3f4`.
- Independent ZIP integrity **PASS** (`testzip`: no corrupt members); Python `compileall` **PASS**; `python -m unittest discover -s tests -q` **PASS**, 155 tests in 10.021 seconds, exit 0.
- Preliminary privacy scan: no PEM private-key headers, obvious assigned API keys or absolute `/home`/`/Users` paths detected. Email patterns found in `samples/ebay_own_orders_FICTIONAL.csv` and `tests/test_marketplace_map.py`; fictional provenance not independently established. Sample finance/card CSVs present; **withhold** from public release pending review.
- Ownership/license **BLOCKED** (no LICENSE/COPYING/NOTICE in archive); original Git ancestry **MISSING** (no `.git` objects). Network/live-provider and native hardware tests **NOT RUN**. Candidate public-release acceptance **BLOCKED**.
- **Publication decision:** No v0.29 source branch created; no duplicate source blobs pushed. Existing 15 staging branches/769 previously audited blobs unchanged. Repository creation/visibility limitations still block dedicated independent repos; PR #4 not merged. This entry documents verification, not publication.
- Fast-forward safety basis: fetched main HEAD `679ee04e9ad12e454bb4b465f4026ee1a6c4f109` immediately before this ledger update; existing file blob SHA `a0085427e10161d51e416011fbb52cfa3c09e952` supplied as compare-and-swap precondition.


### Independent candidate gate: OX Treasury v0.30 (2026-11-23 UTC)

- Source: Library `/OX Treasury/Continuity/OX_Treasury_v0_30.zip` (106,342 bytes, 60 ZIP members). Independently computed SHA-256 `3c6059760d78425d7c2f67a1ec11dae46a537bdb1ea277ae10cf451cfff2138e`, matching its continuity report; ZIP testzip PASS.
- Reproducibility: Python compileall PASS; `python -m unittest discover -s tests -q` PASS, **158 tests** in **13.344 seconds** on extracted archive bytes. SQLite ResourceWarnings appeared for unclosed connections; tests still exited 0.
- Preliminary privacy scan: no matches for bounded private-key headers, selected GitHub/OpenAI token patterns or absolute user-home paths in Python/CSV/JSON files. This is **not** a complete privacy or history scan. Financial-themed sample CSVs are present; their provenance and suitability for public distribution remain unapproved.
- Ownership/history/license: no LICENSE file and no original `.git` history in the 60-member source archive; original authorship, independent public-license permission, and complete private-data review remain **BLOCKED**.
- External/live provider tests: NOT RUN; no Windows-specific hardware acceptance. Missing-media: NOT ASSESSED. Timeout: NONE during local suite.
- Publication: **0 new source files, 0 branches**; no duplicate upload, merge, release, or PR #4 change. Existing 15 branch/769 blob baseline unchanged; remote blob integrity for new v0.30 source is **NOT APPLICABLE** because it was not published. Dedicated repo creation remains unavailable through the connected GitHub action surface.
