# OXsukra — ecosystem contracts

This repository is an umbrella for shared **contracts**, not an authoritative mirror of IXO, Thought Spine, EUREKA, GREMLIN, Build Factory or private source histories. Each program retains its own source, state, approval and execution permissions.

## Shared governance router: reference v0.1

- [Four-lens decision contract and owner integration map](GOVERNANCE_ROUTER.md)
- [Four-lens validation and scope-bound handoff](governance_router/core.py)
- [Risk-aware routing and evidence-bounded adaptive proposals](governance_router/adaptive.py)
- [Original verification tests](tests/test_governance_router.py)
- [Adaptive regression tests](tests/test_adaptive.py)

To run the standalone Python 3.10+ tests locally:

```bash
python -m unittest discover -s tests -v
```

**Status:** Reviewable reference implementation only. The router does not intercept live calls, collect actual ballots, verify evidence, authenticate delegation, generate real approvals, or execute a decision. It does not mutate its own policy, increase anyone's voting authority, or change an owner repository. Real owner-by-owner adapters, authenticated approval receipts, independent effect checks and host evidence are prerequisites.

Adaptive assessment is **advice**: missing/unknown risk defaults to full four-lens review. Verified observations may propose small experiments but never auto-promote policy. Require a trusted `verify_receipt` callback for observation analysis.

- Pull request: https://github.com/Dustiixo/OXsukra/pull/4
- Integration stages: https://github.com/Dustiixo/OXsukra/issues/5

The separate downloadable Home Kit includes Windows scripts, a Word guide, offline preview and the v0-to-v0.1 patch; those packaging assets are not part of this source repository.
