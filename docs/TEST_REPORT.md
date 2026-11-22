# FlowMesh M0.1 — reproducible acceptance report

**Tested:** 2026-11-12/13 development container (not user's hardware), CPython 3.13.5 Linux.

| Gate | Result | Evidence |
|---|---|---|
| Syntax/import | PASS | `python -m compileall -q flowmesh tests` |
| Headless contracts | PASS | 44 unit tests using `unittest` |
| Fresh project safety | PASS | Reject occupied directories; source size/extension/symlink limits |
| Adaptive scheduling | PASS | Finite work units, evidence gain shifts shares, manual park reallocates, focus changes weights |
| Prompt interruption | PASS | Simulated slower model response while user revises; stale result rejected without losing new prompt |
| True parallel model dispatch | PASS **mocked** | Two mock agents synchronize via thread barrier, showing two executor threads can overlap |
| Source-based recovery | PASS | New relevant document wakes an exhausted branch, deliberate user park is respected |
| Ledger and source integrity | PASS | Transactional SHA-256 receipts; change a DB event, snapshot, or preserved source and verification fails |
| Independent demo | PASS | 6 cycles; 4 branches total, 72 receipts; 15 source-verified excerpts; session ID unchanged; user park/wake |
| Native GUI | PASS under Xvfb | Created tabs and graph, captured 3 screenshots, completed one background engine step, checked new journal state |
| Ollama adapter | Unit-mocked only | URL, JSON schema, failure paths, local-only endpoint and output parsing checked; **no live model call** |
| IXO/VELA/GHOSTFIELD/STRAY integration | NOT TESTED | Existing projects preserved; no bridge or hardware writes |
| CPU/GPU efficiency | NOT MEASURED | `work credits` represent scheduling decisions, not hardware reservations |

## Inspect the proof

`sample_output/SESSION_DEMO/DEMO_PROOF.json`, `events.sqlite`, `sources/`, and `docs/` screenshots are included. Validate independently:

```bash
python VERIFY_PACKAGE.py
python -m unittest discover -s tests -v
python -m flowmesh verify --root sample_output/SESSION_DEMO
python -m flowmesh status --root sample_output/SESSION_DEMO
```

The bundled example source documents contain clearly labeled design notes derived from the prior IXO thread. Exact source excerpt verification is not independent validation that the author's statements are true.

**Signoff:** M0.1 offline/reference gate only. No claim of installed or autonomous IXO orchestration, successful AI reasoning, physical resource optimization, protected kernel access, or real-time media scheduling.
