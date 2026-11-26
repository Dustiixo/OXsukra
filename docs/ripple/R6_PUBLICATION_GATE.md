# RIPPLE R6: required review-branch publication attempt

Status: **proposed public policy; draft review only**. This document describes the GitHub publication gate for the scheduled RIPPLE coordinator. It does not itself implement CI, grant repository permissions, or imply that any underlying application is released.

## Per-iteration sequence

1. Recover and verify the authoritative source and immutable continuity archive (R0).
2. Make a bounded reversible change; execute relevant tests and reconcile failures (R1-R4).
3. Store the versioned source, exact test logs, screenshot evidence if applicable, rollback, receipt and SHA256 manifest in the private continuity library (R5).
4. **Attempt R6 on every successful verified and packaged iteration.** Derive an explicit public allowlist. Review each byte and changed path before writing to GitHub. Scan for credentials, personal data, private registry/crosswalk, internal repo mappings, third-party ownership, copyright/license restrictions, private archives and misleading claims. When any gate is uncertain, fail closed.
5. Write permitted content only to an isolated, nonprotected review branch and open or update a **draft** pull request. Never push directly to the default branch, force-push, auto-merge, publish private source or imply that public metadata is executable application source.
6. Fetch back the published paths, verify their exact contents and capture the branch, commit SHA, PR URL, published paths and privacy-review outcome. If unavailable, record the exact failure. Do not infer publication from a local commit or an attempted API call.
7. Record a machine-readable R6 receipt in the next immutable continuity archive: `PUBLISHED_REVIEW`, `PUBLISHED_METADATA_ONLY`, or `BLOCKED`. Explicitly distinguish code publication from metadata publication. A locally verified candidate with `BLOCKED` publication is not a GitHub release.

## Hard boundaries

- The public capsule board is a candidate coordination surface, **not** the private project/source crosswalk.
- Project families keep independent code, owners, licenses, histories, tests and approvals. Do not transplant code between them, including external collaborations.
- GitHub account/commit identity and publication history are public. Aliases do not anonymize an author.
- Preserve all failed checks and historical journal findings; do not rewrite legacy evidence to obtain an apparent pass.
- Device/host acceptance, adapter transactions, repository merges and release acceptance are separate gates.
- If no license or publication authorization is demonstrable for source code, publish at most separately reviewed neutral status documentation; leave source publication BLOCKED.
- If the GitHub connector is unavailable, private-source review cannot run, or review branch cannot be created, record `BLOCKED` and its cause rather than silently skipping R6.

## Required receipt fields

`iteration`, `local_archive_sha256` (private receipt only), `scope`, `source_review`, `privacy_review`, `status`, `published_paths`, `branch`, `commit_sha`, `draft_pr_url`, `remote_verification`, `blocked_reasons`, `created_utc`. Keep non-public fields out of the public PR body and files.

No production deployment or automatic promotion is authorized by this policy.