# VELA: The Water's Edge — End-State Contract

## Why this exists

The desired system is NOT a conventional DAW, a toy chatbot, a website visualizer, or a text-to-music app. It is an expressive native interface where a person can play two songs, improvise, record beatboxing, ask for musical changes, compare the result, and keep playing. FL Studio and REAPER remain the precision finishing environments.

Music is a first-class communication mode for VELA. The system should understand the musical consequences of a user's performance and form meaningful audible responses, but **does not need instantaneous intelligence**. The audio transport must be continuous and reliable while the response worker thinks for 0.1, 3, 30 or more seconds as needed.

## Core metaphor

**Water's Edge:** interaction boundary and measurable point of impact where human expression and generative contribution meet. The system can increase, decrease or withhold its response, not simply generate more content.

**Black Hole Alignment:** multiple expressive inputs and their relationships converge around the same musical idea. The central lens reveals dependencies and related concepts rather than replacing the media.

**Outside Observer / Thought Spine:** VELA and the human can change perspective to examine the whole evolution and evaluate the differences, then return to the *same* moment. Perspective is a view on the same stable project state, not a disconnected duplication.

## Audio call-and-response protocol

1. The user plays/imports/records audio; the raw original is preserved.
2. Audio descriptors and user intent are attached as evidence with source and confidence.
3. An optional language model plans a response in a constrained operation vocabulary.
4. A worker synthesizes/edits a response without blocking the audio callback.
5. The system schedules the contribution on an aligned musical boundary.
6. The user hears the impact and can A/B, accept, reject, revert, modify or annotate.
7. Actual changes and measured consequences are recorded; interpretations are explicitly separate.
8. The next response can observe the *result*, not merely the first input.
9. The outside observer can compare branches before presenting an evidence-linked recommendation.

A 30-second response is acceptable but not required. The workload determines latency; the audio device never has to wait for the worker.

## FID (working name, experimental)

A proposed *portable collapsible audio object*, playable as music in its primary representation, but expandable to related time-aligned layers:

- Raw source recordings, human vocal ideas and beatbox, held as first-class immutable inputs.
- Audio event timeline with timing, musical measurements, sources and confidence.
- Original and generated audio stems plus non-destructive revision graph.
- Musical intent, annotations and remembered reactions linked to the event timeline.
- Multiple spatial lenses: Water's Edge, Black Hole, outside view and Thought Spine.
- Export to ordinary audio and production tools.

An MP3 alone is not a reversible representation of arbitrary annotated 3D structures, separated stems, intent and all transformations. A self-describing container plus compressed media and manifests is an honest starting point. In M1, `.fid` is a ZIP with WAV assets and JSON provenance. Later versions may use content-addressed blocks, event/beat graphs, efficient compression, embedded lightweight summaries, progressive loading, and backward-compatible metadata profiles.

## Modules and boundaries

**Audio transport:** continuously running local native callback; deterministic time/beat/bar clock; source and response layers; preview/transition, no model inference in callback.

**Observation:** input buffer or file → robust beat grid, harmonic estimates, instrument/timbre descriptors and uncertainty. M1 exposes only an inexpensive approximating onset/pitch estimate.

**Reasoning:** VELA model consumes explicit symbolic audio evidence and user intention, chooses controllable actions, and can ask for clarification rather than invent acoustic certainty. M1 has heuristic plans and optionally a local Ollama planner.

**Generative synthesis:** response plans into actual audio; incremental, reversible, auditionable. M1 uses deterministic DSP; later implementations need learned and editable text/audio-conditioned generation and strong rhythmic coherence.

**Thought Spine:** persist time-stamped interactions and decisions with source links and corrections; compare branches; no silent truth promotion. M1 has an explicit JSON log and annotated timeline.

**Spatial lenses:** all operate over the same durable object IDs and timebase. M1 uses lightweight 2D projections. Higher-fidelity interactive 3D must be built and tested separately.

**DAW handoff:** render mix, original audio, response layers, and MIDI where available; later add ALS/RPP projects and accurate warp markers. M1 exports WAV layers and rough drum MIDI.

**Governance:** the human is the decision-maker; automatically generated content never overwrites raw inputs. Models must identify uncertainty and limit claims. Cloud not required. Optional local model must not be described as an installed trained musical intelligence.

## The test ladder

| Stage | Demonstration | Status in M1 |
|---|---|---|
| 1 | Native continuous audio playback | Engine implemented; Windows device still requires hands-on testing |
| 2 | Two synchronized decks, crossfade | Implemented; audio device test pending |
| 3 | Audio or beatbox input drives generated response | Implemented with coarse onset/DSP, not deep semantic understanding |
| 4 | Async worker + musically quantized handoff | Implemented and unit-tested |
| 5 | Repeated generative evolution + optional local language planner | Implemented; local Ollama not externally validated |
| 6 | A/B, undo and preserve earlier versions | Implemented with current+previous quick revert and archived versions |
| 7 | Three perspectives share one state | Implemented as 2D canvas lenses; 3D and full outside observer not finished |
| 8 | Portable structured audio and provenance | `.fid` experimental round-trip tested |
| 9 | DAW handoff | Stereo mix, stems, beatbox-onset MIDI; not a full DAW session export |
| 10 | Robust sound-to-intent understanding and meaningful musical judgment | Research target, not implemented |
| 11 | True navigable 3D annotation, semantic memory, source-backed multi-step reflection | Research target, not implemented |
| 12 | Source rights / lawful music discovery integration | Not implemented; local user-supplied files only |

## Measurable success criteria for full vision

- User can start an arbitrary loop without manual re-timing and experience no dropout during inference.
- Music-conditioned response demonstrably follows a beatboxed groove better than a random baseline across a blinded set of trials.
- Generated responses expose change provenance; source raw media is unchanged.
- The user can navigate perspectives and return to the exact same anchor and mix state.
- A persistent project survives close/reopen with sources, interpretations, alternatives and corrections preserved.
- User can reject/undo any generative change and import the useful material into FL Studio or REAPER.
- A/B preference and estimated musical fit are evaluated separately from response speed and effect magnitude.
- The program remains useful entirely offline, with models and capabilities honestly labeled.

This contract preserves the **complete intended concept**, not a claim that M1 completes it.
