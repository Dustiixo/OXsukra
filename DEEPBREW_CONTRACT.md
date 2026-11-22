# DeepBrew Object Contract 0.2 / Proposed Syntra Adapter 0.1

## The three separate responsibilities

1. **VELA/FID** is the native audio environment and durable object store. Its input is real source material. Its outputs include playable material and explicitly labeled analysis.
2. **Self-inspired direct manipulation** is an interaction design strategy, not a dependency on Self code: every entity has a stable ID, labelled behaviours, an inspectable description, and a way to interact with it in a projected scene. Changing viewpoint doesn't change the underlying object.
3. **Syntra (future)** is a separate cognitive contributor behind a negotiated, versioned proposal interface. For now `LocalRulesAdapter` does modest deterministic signal-informed proposals, entirely inside the VELA process. There is no code import from Syntra and no claim of compatibility with Alex's specific internal APIs until a contract is agreed and tested.

## Content vs. representation

- Source audio is preserved in original imported bytes when provided, plus a normalized WAV for playback and DSP.
- `content_sha256` identifies the actual stored normalized WAV media. `original_binary.sha256` separately identifies the unchanged original imported file.
- `features.segments[]` holds rounded analysis measurements and sample-aligned temporal intervals, not secretly embedded musical meaning.
- `project_points()` derives a 3D coordinate *view*: time along x, frequency bands on a circular scaffold, radial energy from spectral power/RMS and deviation from flux. Rotations alter only display coordinates.
- `object_graph.objects` maps immutable content-addressed audio IDs to their feature descriptions and available actions. `edges` represent annotation, derivation, slicing and revision relationships.
- `.fid` embeds manifest, media and any original binaries. Every object's stored bytes must match the checksum during import; corrupted archives are rejected.

## Proposed cognitive adapter I/O

An adapter implements:

```
propose(graph, source_id, intent, bpm, bars) -> proposal
```

The `deepbrew.proposal/0.1` response contains `id`, `origin_object_id`, `origin_hash`, `instruction`, `bpm`, `bars`, bounded `plan`, `based_on` measurements, `status=proposed`, limitations and adapter provenance.

Audio engine operations are deliberately separate. An adapter response does **not** authorize writing files, altering source bytes, modifying agent permissions or starting execution. The human accepts or rejects. If accepted, the audio worker renders a bounded mode (`drums|bass|melody|pad|glitch`, 0..1 density/intensity, limited MIDI root), schedules the audio overlay on the next beat-grid bar boundary and logs its new object and revision ID.

**Future Syntra bridge:** build an isolated protocol adapter that translates a minimal copy of the DeepBrew proposal into an agreed SyntraLang/world-model capability request. The protected IXO broker should own authorization and execution. Do not bind directly to Syntra internals or allow a planner to write an archive or execute arbitrary code. Reconcile actual Syntra APIs from a pinned commit before implementing.

## Provenance and semantics

- Capture: stored media and its content hash.
- Observation: measured descriptor, with method and approximations.
- Inference: a proposed music operation from a named adapter.
- Human agency: accept, reject, annotation and correction.
- Effect: rendered response ID, acoustic change metric, musical entrance point and export.

An audio feature vector can reveal rhythm/frequency structure; it **cannot** infer intent, historical memory, or meaning without additional data. Those live in separate, attributable events. No stored inference is promoted to raw fact.

## Security exclusions and non-goals

- Native local app, offline audio, no remote access. Optional Ollama uses localhost only when deliberately enabled in the original VELA mode.
- Current import restricts ZIP member paths, sizes and member count; verifies audio objects and original binary hashes. This guards accidents and some tampering, but is not a cryptographic provenance signature, hostile-media decoder sandbox or full enterprise security design.
- First-run launcher may download dependencies and official Python on Windows. Confirm user-visible prompts/installer logs before assuming success.
