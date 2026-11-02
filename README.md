# OXsukra — ecosystem contracts

This repository is an umbrella for shared **contracts**, not an authoritative mirror of IXO, Thought Spine, EUREKA, GREMLIN, Build Factory or their private source histories. Each program owns its source, state and execution permissions.

## New: Governance Router (reference v0)

- [Decision-governance policy and owner integration map](GOVERNANCE_ROUTER.md)
- [Pure-Python, standard-library router](governance_router/core.py)
- [Tests](tests/test_governance_router.py)

Run `python -m unittest discover -s tests -v` from the repository root.

**Status:** this is a proposal and tested non-executing library. It does not intercept live owner calls, collect real votes, verify evidence, or execute a decision. A trusted human approval service and explicit owner-by-owner integration are required before live use.
