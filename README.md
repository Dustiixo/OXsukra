# IXO v0.4.0 — Executable Python Feature Control (native, no HTML required)

**Default:** Windows one-click installer `Install_IXO_Live_Features_v0_4_0.cmd`, then **IXO Live Features**. Actual component calls execute under `operations/hub.py`. Native Tkinter UI where available, always-functional text console `Start_IXO_Terminal.cmd`. The previous browser shell remains optional. 

**Run from extracted source:** `python -m ixo_foundation.ops_cli --home ./state console` or `python -m ixo_foundation.ops_cli --home ./state list`. See [docs/LIVE_OPERATIONS.md](docs/LIVE_OPERATIONS.md) for real operations, acceptance tests, and limits. This is not autonomous general AI.

---

# IXO v0.3.2 — Experience boundary added

**New tested behavior:** trace IXO-only exposure; ingest independently labelled preexisting work; generate general-purpose balanced source manifests; require explicit cross-domain held-out task assessments before promoting a method *within the isolated experience registry*. This does not claim model learning or a general-purpose assistant. Read [docs/EXPERIENCE_BOUNDARY.md](docs/EXPERIENCE_BOUNDARY.md). The existing IXO / AIXO / DSOE architecture and source remain in place. The browser adds an EXPERIENCE / BALANCE tab.

A new v0.3.2 installer is supplied separately if you prefer a Windows double-click setup; the v0.3.1 installer will not install the new module.

> **Windows one-click install added in v0.3.** Download the standalone `Install_IXO_DSOE_One_Click_v0_3_1.cmd`, double-click it, and launch from your Desktop shortcut. Read [README_ONE_CLICK.md](README_ONE_CLICK.md) for installation, data safety and limits. The earlier v0.2 Python CLI remains intact, with a new `python -m ixo_foundation.desktop` UI service.

# IXO × AIXO × DSOE — `uv` Python Foundation v0.2

**A source-code increment on the earlier `IXO_UV_FOUNDATION_v0_1`, not a regenerated HTML project.** Includes the same IXO, AIXO and FrameShift Python modules and tests, plus a persistent DSOE orchestrator for **three distinct Pantheon references**.

**Boundary:** The local Python implementation, SQLite state machines, bridge JSON, test fixtures and AIXO evidence sink are real. No original PantheonOS, Odysseus/Pantheon or Duskript/Pantheon code is bundled or executed. Native provider integration requires a future source-audited connector. No AI model, cloud API or other Python dependency is needed for this core.

## 1. Start (PowerShell, macOS or Linux)

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), extract the archive and open a terminal in the project directory.

```sh
uv sync
uv run python -m unittest discover -s tests -v
uv run python -m ixo_foundation --home ./state status
uv run python -m ixo_foundation --home ./state dsoe providers
```

`.python-version` pins 3.11 but project supports Python 3.11+. On a machine using a different installed Python, you can use `uv run --python 3.13` explicitly. No third-party runtime dependencies are installed by the default project.

## 2. Build and approve a durable DSOE task

```sh
# Start inside Habitat's current workspace (default: main).
uv run python -m ixo_foundation --home ./state dsoe plan "Inspect IXO source, suggest an agent plan, operate a workflow, review risks"
```

Copy `task.id` from the JSON output (replace `TASK_ID` below):

```sh
uv run python -m ixo_foundation --home ./state dsoe approve TASK_ID
uv run python -m ixo_foundation --home ./state dsoe dispatch TASK_ID
```

Dispatch creates a JSON handoff inside `./state/dsoe/outbox/pantheonos/` and prints its `job_id`. **It does not start PantheonOS.** An audited bridge or an operator can produce a matching result document. Test the entire internal boundary with a labelled fixture:

```sh
uv run python -m ixo_foundation --home ./state dsoe fixture JOB_ID fixture.json
uv run python -m ixo_foundation --home ./state dsoe report JOB_ID fixture.json
uv run python -m ixo_foundation --home ./state dsoe review JOB_ID accept --reason "Reviewed as a schema fixture, not empirical evidence"
uv run python -m ixo_foundation --home ./state dsoe evidence JOB_ID
```

Dispatch `TASK_ID` again and repeat for the **second** provider `odysseus_pantheon`, then the **third** `duskript_pantheon`. You cannot skip the previous stage or record evidence before reviewing. Check persistent state:

```sh
uv run python -m ixo_foundation --home ./state dsoe detail TASK_ID
uv run python -m ixo_foundation --home ./state status
```

`AIXO.dsoe_evidence_count` increases after accepted evidence. `IXO.counts.facts` does **not** increase.

## 3. Existing IXO + AIXO commands are preserved

```sh
uv run python -m ixo_foundation --home ./state set research
uv run python -m ixo_foundation --home ./state case --workspace research --observation "I scream or ice cream" --hypothesis "The word boundary is ambiguous" --question "Which reading is supported?"
uv run python -m ixo_foundation --home ./state capture
uv run python -m ixo_foundation --home ./state course
uv run python -m ixo_foundation --home ./state probe "Find every clue"
```

## 4. Source map

| Module | Purpose |
|---|---|
| `ixo/` | existing Habitat, Hermes, Moon2, local state and command surface |
| `ixo_foundation/` | Python composition and CLI, now owns DSOE lifecycle |
| `aixo/` | ordered course, experiments/evaluations, plus provenance-bound DSOE evidence |
| `dsoe/registry.py` | three separate Pantheon identities, roles, upstream licenses |
| `dsoe/store.py` | SQLite source identity, tasks, approvals, jobs, hashes, trace |
| `dsoe/system.py` | ordered handoff dispatch, operator-reviewed result import, AIXO bridge |
| `dsoe/protocol.py` | independent per-provider schema checks and simulated test fixtures |
| `frameshift/` | isolated language / judgment experiments, not a source of facts |
| `tests/test_dsoe.py` | new integrity, provenance, restart, orchestration tests |

## 5. Read this before building the next component

- [`docs/IXO_DSOE_DISTILLATION.md`](docs/IXO_DSOE_DISTILLATION.md): source-aware system distillation and architecture.
- [`docs/PANTHEON_SOURCE_AND_LICENSE_AUDIT.md`](docs/PANTHEON_SOURCE_AND_LICENSE_AUDIT.md): exact three upstream identities, licensing, and native-adapter checklist.
- [`docs/DSOE_PROTOCOL_AND_FAILURES.md`](docs/DSOE_PROTOCOL_AND_FAILURES.md): state machines, interchange schema, hazards, acceptance gates.
- [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md): inherited baseline status; historical v0.1 content (not updated to claim DSOE abilities).

## 6. Deliberate exclusions

No unverified model execution, cloud dependency, GPU workload, OS file access by agents, network API exposure, AIXO model fine-tuning, Hermes Mark 12 restoration, autonomous Moon2 intelligence, native 3D world, or AGPL third-party code. The browser prototype is present only as inherited compatibility material, not as DSOE's implementation.

**Rule for v0.3:** pin and audit all three upstream code revisions, test native transports in isolated environments, add capability-scoped execution, preserve every v0.2 regression; do not rebuild from scratch.
