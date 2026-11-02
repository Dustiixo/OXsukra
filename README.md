# OXsukra Governance Router — Home Kit v0.1

**ONE DOWNLOAD. TWO LOCAL CHECKS. NO AUTOMATIC INSTALLATION.**

Status on 2026-11-02: standalone reference implementation tested locally; GitHub PR #4 contains the reviewable source; cross-owner integration is tracked as issue #5. It is **not wired into your current IXO installation**. This package does not include any canonical private IXO repository or any existing owner database.

## When you get home (Windows)

1. Extract the ZIP to a normal folder, e.g. `Downloads\OXsukra_Governance_Home_Kit_v0_1`. **Do not extract into `IXO-work` and do not replace existing programs.**
2. Read `START_HERE.md` or `OXsukra_Home_Setup_Guide.docx` (Microsoft Word compatible).
3. Double-click **`01_TEST_FIRST.cmd`**. It verifies file hashes, runs local Python tests, then generates a **read-only offline preview**.
4. Open `reports\decision-preview.html` in any browser. This shows two **fictional** decisions, the four-lens review and risk routing; it neither connects to your projects nor approves anything.
5. Double-click **`02_REVIEW_LOCAL_IXO.cmd`**. It inventories known IXO-work folders and Git state *without writing to them*. Read `reports\workspace-readonly-check.txt`.
6. **Stop at this gate.** Do not apply the patch to IXO yet. The next engineering step requires the exact local source and verified owner adapter boundaries.

If Python is missing, the test script stops; there is no automatic installation. Avoid running unsigned scripts from untrusted sources; scripts are provided as plain text for inspection.

## Where everything is

| File/folder | Purpose |
|---|---|
| `01_TEST_FIRST.cmd` | Stage 1: hash verification, unit tests, offline preview |
| `02_REVIEW_LOCAL_IXO.cmd` | Stage 2: local source inventory, read-only |
| `START_HERE.md` | Step-by-step instructions and acceptance gates |
| `OXsukra_Home_Setup_Guide.docx` | Word version of the guide |
| `governance_router/` | Python source for four-lens checks and bounded adaptive routing |
| `tests/` | Automated tests; no owner integration dependencies |
| `samples/` | Clearly fictional sample packets |
| `scripts/` | Plain-text scripts used by both checks and preview generator |
| `DIFFS/v0_to_v0_1.patch` | Exact source patch relative to the v0 reference files, **for inspection, not direct application to IXO** |
| `DIFFS/CHANGELOG.md` | What changed, what didn't, acceptance gates |
| `SHA256-MANIFEST.json` | File hashes used by Stage 1, excluding generated reports and the manifest itself |
| `reports/` | Generated locally after running checks; may contain local repo names/paths — keep private |

## What systematic adaptive optimisation means here

1. **Classify:** the owning program declares risk flags. Missing/unknown or cross-owner scope defaults to `FULL_FOUR_LENS`.
2. **Route:** an explicitly low-risk, reversible, same-owner case *may* follow the owner's existing policy. That is a **review recommendation, not permission to act**.
3. **Review:** four democratic lenses are considered or transparently waived. Dissent remains visible.
4. **Observe:** independent trusted receipt validation is required before workflow observations contribute to an analysis.
5. **Propose:** after at least five verified observations per workflow, generate small improvement experiments (evidence preflight, second review, prefill, clearer questions). Results are descriptive; no causal improvement is claimed.
6. **Verify:** freeze baseline and evaluator, run held-out tests, examine minority/rights impacts, obtain scoped human review before any policy change.

The module never assigns human intelligence scores, counts actual votes, grants authority, alters live policy, edits owners' databases, or deploys code.

## Source/Review links

- Reviewable changes: https://github.com/Dustiixo/OXsukra/pull/4
- Owner integration checklist: https://github.com/Dustiixo/OXsukra/issues/5
- Repository: https://github.com/Dustiixo/OXsukra

**Do not merge because a standalone test passes.** First complete source reconciliation and a verified read-only IXO vertical slice. No existing app or engine has been installed or changed by this ZIP.
