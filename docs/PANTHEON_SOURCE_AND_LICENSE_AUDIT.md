# Three Pantheons — identity, interface, licensing evidence

Reviewed against public repository descriptions on **2026-10-13**. Local network access to clone GitHub sources was unavailable, so this is **README / visible metadata verification**, not an imported-source audit. Integration state must not be overstated.

| Repository | Upstream identity | Declared license | Advertised interface/features | DSOE v0.2 integration |
|---|---|---|---|---|
| PantheonOS | https://github.com/aristoteleo/PantheonOS | BSD-2-Clause | Python package `pantheon-agents`, CLI, teams, NATS/Fleet, agent evolution | schema-validated `pantheonos` file handoff, stage `plan` |
| Pantheon (Odysseus fork) | https://github.com/ImPanick/pantheon | AGPL-3.0-or-later | Python/Docker self-hosted workspace, workflows, MCP, research/desktop UI | schema-validated `odysseus_pantheon` file handoff, stage `operate` |
| Pantheon (Duskript) | https://github.com/Duskript/Pantheon | AGPL-3.0 | privacy-first personal AI, specialized gods, Hermes Agent dependency, gateway/web UI | schema-validated `duskript_pantheon` file handoff, stage `review` |

**No code copied, packaged, imported or executed from these three repositories.** The manifest in `dsoe/registry.py` is an external-source reference and workflow mapping. Even if a name appears in the adapter manifest, that does not mean it installed successfully.

**Compliance warning:** the two AGPL upstreams are not permissively equivalent to BSD PantheonOS. A future combined/modified/network-served derivative may incur source-disclosure obligations; review precise linking, process separation and redistribution strategy with legal counsel before distributing. Process isolation is not automatically a legal exemption.

## Requirements for an upstream-native adapter

1. Clone/fetch an explicitly pinned upstream commit; preserve source hash, license, notices and dependency lock.
2. Verify entrypoint, authenticating API, supported request/response shape and sandbox lifecycle from source/tests.
3. Implement `dsoe-json-file-v1` translator without direct IXO SQLite/Hermes writes.
4. Apply explicit capability permissions, timeouts, credential handling, rate limits, safe local bind, and isolation.
5. Add contract tests with actual upstream in disposable containers; test failures/restarts/partial success.
6. Mark adapter as `upstream_connected=True` only when tests pass and include exact verified commit.
7. Record evidence in AIXO *only* after operator acceptance; all model claims remain untrusted until externally verified.

### Boundary currently proven

`uv run python -m unittest discover -s tests -v` runs local tests, including all DSOE stages in deterministic fixture mode, without a model/API/network. These tests do **not** claim Pantheon upstream compatibility or live agent execution.
