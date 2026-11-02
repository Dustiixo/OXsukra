# OXsukra Governance Router — shared contract v0

**Status: reference implementation / integration proposal; not installed in any owner runtime.** This is an OXsukra-wide cross-owner *decision* boundary, not a separate IXO shell and not a replacement for any source history.

## Purpose

When a consequential decision spans programs, collect **four independent democratic lenses** before an authorized owner acts:

1. `direct` — equal participation; describe who could participate and the recorded preference. No automatic vote weighting.
2. `deliberative` — evidence examined, uncertainties, expert input and challenges.
3. `liquid` — subject-specific voluntary delegation, with revocation handled by the future voting owner; this module never grants standing proxy authority.
4. `participatory` — input from people affected by a decision, including dissent and anticipated consequences.

A lens can be `reported`, `pending`, or `not_applicable` with an explicit reason. The router **does not** compute a majority across the lenses, score people by intelligence or qualification, decide what is correct, certify evidence, count votes, or authorize actions. It allows contested findings to be escalated, not erased. Human rights, equal baseline civic standing, access, accountable expertise and informed consent are constraints, not weights.

## Entry criteria and exception

Use the router for cross-owner changes, policy/permission changes, consequential resource allocations, releases/promotions, safety-impacting decisions, irreversible effects, or disagreements over authority. Routine local work with an already approved scope stays on the normal owner path; do not route every keystroke through a democratic referendum. Emergency protective pauses may stop work immediately, but must not quietly become authorization for new effects.

## Boundary / integration matrix

| Component | Integration | Remains owned by |
|---|---|---|
| IXO | Initiate decision, show four parallel perspectives, request human review | IXO / human authority surface |
| Thought Spine / WRAP | Store source-linked deliberation lineage, alternate hypotheses and changes over time | Thought Spine / WRAP |
| EUREKA | Fork proposals, record competing ideas and objections | EUREKA |
| ORBITAL / PARALLAX | Visualize perspective and dispute links (read-only) | Their visual/capture owners |
| GREMLIN | Capture offline input and enqueue pending review; never silently finalize | GREMLIN |
| OX cognitive coordinator / agents | Gather cited evidence, question assumptions, flag unsupported claims | Cognition owner / agent provenance |
| Build Factory / Packbot | Accept only owner-verified scoped handoffs; run approved work separately | Execution owner |
| OX Relay / Slotline | Carry durable review requests and timeboxed tasks; do not conflate dispatch with permission | Relay / time owners |
| OX WITNESS | Independently assess factual claims and effect receipts | Independent verification owner |
| Release Controller | Apply existing promotion and rollback policy after scope-matched authorization | Release owner |

**Single transport rule:** store only typed references, scope digest and provenance in cross-owner packets. Do not copy owner-private journals, vote rosters, or credentials into the shared router. Integrators must implement consent/access control, privacy, revocation, accessibility, source protection and persistence in their owning systems.

## Minimal decision packet

```json
{
  "schema": "ox.governance.decision.v0",
  "decision_id": "D-001",
  "origin_owner": "IXO",
  "target_owner": "BuildFactory",
  "action_ref": "proposal://change-17",
  "impact": "cross-owner code modification",
  "question": "Should the change be promoted?",
  "affected_owner_refs": ["owner://IXO", "owner://BuildFactory"],
  "lenses": {
    "direct": {"state": "pending"},
    "deliberative": {"state": "pending"},
    "liquid": {"state": "not_applicable", "reason": "No revocable delegation service"},
    "participatory": {"state": "pending"}
  }
}
```

Each reported lens requires method, summary, at least one evidence reference, and a list of dissent references (may be empty). A waiver is visible and justified, not a fabricated outcome. `review(packet)` describes completeness and conflict. `scope_digest(packet)` binds the full decision record (the intended effect and all review findings) to its proposed approval. `prepare_handoff(packet, approval, registered_owners=..., verify_human_approval=...)` fails closed without a real host-supplied approval verifier and returns a **non-executing** handoff for the receiving owner.

## Non-negotiable checks

- Four lenses considered or explicitly waived; no hidden `expert_override` or automated winner.
- A different proposed action, owner or scope invalidates the old approval digest.
- Human approval receipts require cryptographic or trusted host validation outside this package; a caller-provided string is **not proof**.
- Destination owner rechecks receipt, scope, source lock, permissions and safety rules before effects.
- Append-only audit, receipts, consent/delegation revocation, authenticated vote counting, duplicate detection, source verification and durable transport are **not implemented** here.
- Failed review is blocked; a unit test is **not** proof of real integration or human adoption.

## Local verification

From the repository root: `python -m unittest discover -s tests -v`.

Next vertical slice: add a read-only IXO decision card backed by this packet; create a real human approval adapter and OX Relay baton bridge only after source ownership, permission tests and a verified on-device run.

## v0.1 additive adaptive optimisation (reference only)

`governance_router.adaptive.recommend_route(packet)` gives a **non-authorizing** risk-based routing recommendation. Missing/unknown flags and cross-owner or higher-impact effects default to a full four-lens review. Known low-risk, reversible same-owner actions may use the owner's pre-existing policy; that policy still governs permission. This does **not** alter the v0 `review()` and `prepare_handoff()` contract.

`governance_router.adaptive.suggest_improvements(observations, verify_receipt=trusted_callback)` summarises verified review durations, missing-evidence signals, clarification demand and reopened decisions per workflow. Without a supplied independent receipt verifier, nothing counts as verified. With at least five verified observations, the module may propose small experiments: evidence preflight, an independent second review, read-only context prefill or clearer question template. It never modifies policy, voting power or execution permissions; the observations are descriptive and cannot establish causal improvement.

**Promotion boundary:** predeclare a baseline, freeze a held-out evaluator, run comparably with versioned receipts, assess accessible participation and dissent/rights risks, obtain exact-scope human approval, and keep rollback. This reference kit has no live persistence, receipt service, held-out runner, identity/delegation registry or owner runtime integration.
