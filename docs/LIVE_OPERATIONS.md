# IXO v0.4.0 — Live Feature Control

## The correction

This is **not** a project register and **not** an HTML-based feature simulation. `operations/hub.py` calls the existing executable Python component code. `ixo_foundation/native_control.py` is an optional Tkinter operator surface; the stable equivalent is `ixo_foundation/ops_cli.py`. The inherited 2D browser interface remains a compatibility client.

## Component ports

| Control operation | Code actually invoked | State/effect |
|---|---|---|
| habitat.activate / inspect | `IXORuntime.habitat.activate_set`, `.status` | changes/reads `ixo.sqlite3` active set |
| hermes.propose / resolve / inspect | `IXORuntime.hermes.propose`, `.resolve`, `.status` | adds proposal; **explicitly** resolves if allowed; no automatic fact promotion |
| moon2.record / inspect | `IXORuntime.moon2.moon`, `.status` | appends actual stage reflections |
| aixo.experiment / evaluate / inspect | `AIXOEngine` | persists experiment and comparison against observed IXO state; false results stay false |
| dsoe.plan / approve / dispatch / inspect | `DSOESystem` + `DSOEStore` | durable protocol handoff with approvals; **not** native Pantheon execution |
| experience.sync / ingest / balance | `ExperienceStore` | actual IXO event capture, opt-in real file reading, balanced selection |
| frameshift.analyze | `Foundation.probe` / `frameshift.construct.analyze_text` | executes existing language analysis without trust promotion |
| quality.tests | allowlisted `unittest` subprocess | executes real source tests and returns exit code/stderr; 90s timeout |
| workflow.investigate | FrameShift + `Foundation.case` | sequential analysis + Habitat + Moon2 stages + Hermes **pending** proposal + AIXO experiment + event capture |
| workflow.ingest_project | ExperienceStore | recursively reads files, reports changed corpus, returns current balanced selection |

`operations.sqlite3` records timestamps, feature IDs, input/output SHA-256, pass/fail, and bounded result JSON. All errors from supported operations produce receipts; malformed or unsupported requests fail validation before execution. This independent audit does *not* provide cross-database atomic transactions.

## Run without a browser

On Windows after installation, launch **IXO Live Features** from Desktop or Start menu; GUI requires Python's optional Tk/Tcl support. Otherwise the launcher drops into a text control console. `Start_IXO_Terminal.cmd` always opens that console.

From a source checkout:

```sh
python -m ixo_foundation.ops_cli --home ./state list
python -m ixo_foundation --home ./state features
python -m ixo_foundation --home ./state run-feature habitat.inspect
python -m ixo_foundation.ops_cli --home ./state console
python -m ixo_foundation.native_control --home ./state
python -m ixo_foundation.ops_cli --home ./state run habitat.inspect
python -m ixo_foundation.ops_cli --home ./state run quality.tests --data '{"suite":"operations"}'
python -m ixo_foundation.ops_cli --home ./state run frameshift.analyze --data '{"text":"I scream or ice cream"}'
```

For an actual independent project (directory must exist; **explicit opt-in**):

```sh
python -m ixo_foundation.ops_cli --home ./state run workflow.ingest_project --data '{"path":"./other-project","project":"Other project","domain":"development"}'
```

You may pass `--data @params.json` to avoid shell quoting on Windows. Run `history` to see persisted receipts.

## Boundaries and unresolved work

- `Hermes` remains a conservative review gate, **not** a verified Mark 12 port.
- `Moon2` is a stage-recording system, **not** an autonomous observer/controller.
- `FrameShift` performs deterministic existing analysis, **not** general-purpose AI reasoning.
- `DSOE` exports protocol handoffs; native Pantheon providers remain disconnected.
- No agent runs your desktop apps or accesses your PC without an explicit, implemented capability.
- No model inference, self-training or automatically validated skill transfer is introduced in v0.4.0.
- Tk GUI is unverified on Windows from the Linux build environment. CLI is the reliable interface; Tk support depends on the Python distribution.
- This release **does** run the tested underlying features rather than only label or track them.

## Validation

Full regression: `python -m unittest discover -s tests -q` — 149 tests passed on Linux/Python 3.11+ (including 137 inherited tests and 12 tests verifying actual component effects). Tests are not a Windows GUI acceptance test. The installer stages the unpacked source and reruns them before replacing the installed program, while retaining state separately.
