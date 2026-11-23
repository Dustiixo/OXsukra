# RIPPLE v0.50 / Native Evidence Navigation

**Review state:** Tested local candidate, not an accepted release. This publication is metadata only.

## Independently bounded functional change
The native desktop evidence interface now supports selecting one recorded source excerpt, viewing its complete recorded provenance, and navigating to an exact matching local ledger receipt and branch context. Navigation checks the ledger hash chain and current excerpt identity before opening. It does not write research state.

## Verification evidence (retained in immutable continuity archive)
- Parent continuity archive SHA256: `c2b509023271f30ce24827d44a4a6eea481d6331b4ddcfa40a5b08f613acb155`.
- Native Python/Tk on Xvfb project tests: **62/62 PASS**, including three GUI interaction tests.
- Independent coordinator regression suite: **48/48 PASS**.
- Native interactive capture: **PASS**, two screenshots from actual Tk/Xvfb sessions.
- Reversible source patch replay: **PASS**.
- New receipt-segment strict audit: **PASS**.
- Pre-existing historical journal strict audit: **BLOCKED**, exit 2, records preserved.

## Nonclaims and unresolved gates
No Windows/ASUS physical acceptance, Godot build, Android build, independently authorized peer adapter, or end-to-end user acceptance is claimed. The source-license/ownership review necessary for a public code release is not complete.

## Public privacy allowlist
Only this Markdown evidence summary is authorized in this review branch. No application source, private registry, ownership crosswalk, credentials, personal data, local workstation paths, binaries, or private screenshots are included. Do not merge automatically into the protected branch.
