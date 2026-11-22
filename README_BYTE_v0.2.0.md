# OX SPATIAL FABRIC v0.2.0 | BYTE × RCLL × SELF PORT

An **incremental, backward-preserving** extension of the verified Morph Lab → Spatial Fabric v0.1.1 path. Contains all previous audio and local object interfaces plus new source-byte analysis, experimental byte visualization, Self-native object source export, audited change proposals, audio sonification, OBJ 3D projection and integration gates.

## Run the local UI

Windows: double-click `start-windows.bat`. Linux: `bash start-linux.sh`. Or `python run.py`.

- `http://127.0.0.1:8765/` = original OX Morph live-object lab
- `http://127.0.0.1:8765/splice` = original music/RCLL 1,000-splice projection
- `http://127.0.0.1:8765/byte` = new raw-byte patching and 3D visual browser study

All local endpoints bind to loopback only. Python 3.10+ required; Node 18+ for JavaScript tests. No dependencies from pip/npm and no CDN or remote services.

## Deterministic checked world: CLI

```sh
python -m bytebridge.cli ingest examples/synthetic_signal.bin --out examples/my_world
python -m bytebridge.cli verify examples/my_world
python -m bytebridge.cli render examples/my_world
python -m bytebridge.cli self-gate examples/my_world
```

`ingest` stores `original.bin`, `vessel.json`, `world.json`, `native_self_object.self`. `render` writes one immutable versioned OBJ + WAV + receipt directory. Do not open native Self source in a privileged, unrestricted environment before reviewing it.

A mapping change must first be proposed and then explicitly committed:

```sh
python -m bytebridge.cli propose examples/my_world --slot twist --value 3.3 --reason "Investigate higher-curvature projection"
# Read the resulting proposals/ID.json; then supply that exact file below:
python -m bytebridge.cli commit examples/my_world --proposal examples/my_world/proposals/ID.json --expected-revision 0 --approve
python -m bytebridge.cli verify examples/my_world
python -m bytebridge.cli render examples/my_world
```

Every write is local mapping-only. `commit` requires human operator approval and an exact expected revision; it never changes the original bytes or external systems.

## Test everything

Windows: `tools\test-all-windows.bat`; Linux: `bash tools/test-all.sh`.

The Python verification suite, JS analysis suites and local HTTP smoke must pass. Report native VM and real browser acceptance separately. `docs/CURRENT_STATE.md` holds the truth table; `docs/RESEARCH_AND_ROADMAP.md` holds the extended research program.

## Critical distinctions

**This is not Meta BLT.** Meta's learned next-byte entropy patching architecture requires the actual upstream code/weights and runtime. Our patcher is an independently tested, deterministic local-entropy **baseline**. It does not gain LLM intelligence by encoding a prompt as bytes.

**This does not yet run original Self.** It exports a Self-language object expression for the actual `russellallen/self` VM. Until the original VM/world/Morphic parses that source and returns a live edited slot, native integration is **BLOCKED**. The original `self/oxSpliceObject.self` remains a manual source artifact.

**3D and WAV are projections, not recoveries.** They map byte statistics, not latent musical semantics. The raw binary is retained exactly.

## Continuity

The project exists **inside OX Spatial Fabric** as a new capability, with testable adapters to IXO and VELA planned. Avoid branching this into a pile of unrelated apps. Maintain verified checkpoints and preserve any prior v0.1.1 accepted source and tests.

## v0.2.1 operator-attested Self observation intake

`python -m bytebridge.cli self-import WORLD --receipt receipt.json --key-file /path/outside/WORLD/key`

This reads a strict signed observation and produces a review-only proposal in `WORLD/proposals/`; it **never commits**. The signer is intentionally separate from the Self world, and this is NOT proof of native Self VM execution. See `docs/CURRENT_STATE.md`, `NEXT_ACTION.md` and `TEST_REPORT_v0.2.1.md`.
