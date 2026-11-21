# Ripple Review Protocol v0.1

**Nothing is complete merely because it was named, drawn, committed, or unit-tested.**

## One reviewable ripple

1. **Recover:** exact project/source/ref and historical receipts, with authorisation.
2. **Probe:** one falsifiable question with expected result.
3. **Change:** smallest useful reversible modification, in an isolated branch.
4. **Verify:** exact test command/output and source SHA; don't infer hardware tests from simulation.
5. **Reconcile:** explain failures and revisions while preserving previous evidence.
6. **Package:** diff, append-only receipt, content hashes, rollback, known limitations.
7. **Promote:** only after independent review and appropriate approval.

## Suggested result fields

`capsule_id`, `source_ref`, `source_sha256`, `test_command`, `environment`, `expected`, `observed`, `status=PASS|FAIL|BLOCKED`, `evidence_ref`, `rollback`, `next_probe`.

Public submissions must NOT contain private project mappings, confidential code, passwords, tokens, personal data, or unreleased collaborators' material. Alias IDs only help track work. The repository owner remains visible.
