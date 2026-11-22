# IXO component-by-component reconstruction

This is a **source-refactor and contract-test milestone**, not a completed spatial OS. Historical IXO claims are not rebranded as implemented capabilities.

## Verified current scope

| Component | Own implementation | Primary entrypoint | Acceptance criterion | Current limitation |
|---|---|---|---|---|
| Storage | `ixo/storage.py` | `Storage` | SQLite v1 survives restart; compatible with v0.3 | IXO components share one database and adapter |
| Habitat | `ixo/habitat.py` | `Habitat.activate_set` | Only known sets; event emitted on activation | Static set list; orbit is visual client |
| Hermes | `ixo/hermes.py` | `Hermes.propose`, `Hermes.resolve` | No silent fact insertion, reject memory origin, enforce bounded writes | REVIEW is conservative heuristic, **not** historical Mark 12 |
| Moon2 | `ixo/moon2.py` | `Moon2.moon` | Stage recorded with workspace; no fact write | Manual ledger, no autonomous cognition |
| Inspection | `ixo/inspection.py` | `Inspector.status` | Read-only state snapshot | Snapshot limited for large tables |
| Commands | `ixo/commands.py` | `CommandSurface.command` | Routes to component façade; errors on unknown command | No native OS commands |
| AIXO | `aixo/engine.py` | `AIXOEngine` | Own database, ordered lessons, evidence and evaluations | Narrow assertions only, no sandboxed external execution |
| Bridge | `ixo/bridge.py` | `capture` | IXO → AIXO, duplicate capture idempotent | Full-event scan; provenance multi-source safety still needs work |
| Visual | `web/app.js` | browser client | Black hole is an active `/go main` target | 2D Canvas, not native 3D or measured 4K/8K |

## Actual architecture

```
IXORuntime (composition root, compatible v0.3 façade)
├── Storage: SQLite v1, lock, event writer
├── Habitat: activate_set
├── Hermes: propose / resolve
├── Moon2: staged observation ledger
├── Inspector: status
└── Commands: command dispatch
           ↓ committed events (read only)
      IXO → AIXO bridge
           ↓
      AIXOEngine (different SQLite database)

Visual client — HTTP commands → IXORuntime
Black-hole viewport is presentation/navigation; no authority to alter DB directly.
```

## Independent-before-integrated acceptance strategy

1. Run `python -m unittest tests.test_components -v` from the unpacked root (use `python -m unittest discover -s tests -p test_components.py -v` if the tests directory is not a package).
2. Run the full regression suite `python -m unittest discover -s tests -v`.
3. Start the service via `python -m ixo`, navigate to each workspace, issue a fact proposal, and observe Moon2 activity. Test these UI interactions on the target PC; this environment has not verified rendering.
4. Never promote a researched repository or historical claimed contract until a source audit and a passing adapter test exist.

## Evidence distinctions

- **Observed in this rebuild:** Python tests running against these actual files; SQLite persistence and event boundaries.
- **Inherited from v0.3 with regression coverage:** local HTTP server, AIXO bridge, black-hole Canvas client.
- **Historical reference only:** source-specific Hermes Mark 12 policy, Moon2 autonomous agent, PySide6 spatial renderer.
- **Future build target:** dependency injection through narrowly scoped component ports (today `__getattr__` forwards to the whole runtime), migration safety, event-source identity for multiple IXO databases, and high-resolution 3D navigation.

The remaining runtime-wide `__getattr__` is a deliberate migration adapter, **not** proof of full sandboxed modules. Remove it only after replacing all usages with explicit interfaces and expanding tests.
