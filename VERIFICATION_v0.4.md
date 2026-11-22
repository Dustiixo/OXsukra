# HERMES Purpose Funnel v0.4 — observed verification

Date: 2026-11-13.

Source: existing v0.3 shareable ZIP, extended in a new directory without modifying the previous checkpoint.

## Tests actually run

- `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -q` — **25 passing tests** on the build environment (previous 16, 8 new purpose tests, and 1 operator-launcher regression).
- `java adapters/java/HermesBridge.java selftest` — **PASS** using OpenJDK 21 source launcher, no network.
- Java `HermesBridge.java preview` — **PASS** against the running localhost Python hub with the issued test member token, checked by the test suite.
- `node --check` on the adaptive-purpose dashboard JavaScript — **PASS** using Node 24.
- A clean ZIP extraction uncovered a pre-existing `tools/operator.py` standard-library shadowing bug and a missing explicit `importlib.util` import. Both were corrected by renaming the helper to `tools/hermes_operator.py`, updating all launchers, and adding a real child-process test for `doctor`.

The new tests cover: non-executing evidence-backed previews, provisional labels, persisted Dump Hub triage requests, human-approved novel purpose creation, reclassification that teaches a bounded rule, explicit missing-file ticket, restricted-business metadata preflight, idempotent taxonomy startup, actual Java/HTTP request-response, and dashboard existence.

## Important negative evidence

- No live Discord guild, Google Drive account, external music bot, VPS, remote worker, or real Syntra process was connected.
- Java interop demonstrates the contract, **not** a claim that Syntra already consumes it.
- The rules are explainable deterministic keyword matches; there is no semantic classifier, AI learning, calibrated probability, auto-rearranging Discord categories or access-control isolation.
- Legacy member roles can still view shared-hub artifacts across purposes; filenames and metadata alone cannot reliably determine confidentiality. Do not feed real business or personal material into this pilot.
- Uploaded code is not executed; the hub still has the v0.3 production limitations around quotas, retention/deletion, backups and protected workflows.
- Windows BATs are preserved, plus an optional Java-source self-test launcher. They were statically examined but not run on a real Windows machine.

## Next evidence gate

Alex runs the Java client with a private staging token and reports one result from a real independent workstation. The four developers agree whether Syntra needs any contract changes before code adapters are built. No automated cross-system execution is authorized by this package.
