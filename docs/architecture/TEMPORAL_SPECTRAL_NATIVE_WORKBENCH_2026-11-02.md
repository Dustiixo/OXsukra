# OXsukra / IXO — Temporal-Spectral Native Workbench
Version: DESIGN-TSW-2026-11-02-R1 | Status: APPROVED VISUAL / INTERACTION BASELINE, NOT IMPLEMENTATION
Date: 2026-11-02 | Owner: existing IXO / DOOR native workspace

## Purpose
This document consolidates the approved visual and interaction direction into the original OXsukra/IXO project. It does not authorize another disconnected shell, a wholesale merge of GitHub projects, or a claim of runtime completion.

The goal is a continuously animated, inspectable native engineering environment for projects, Git source, model components, parameters, experiments, agents, notes and verification. Its central navigational reference is time. Richness comes from truth-backed relationships, not from covering the display with a decorative dashboard.

## System identity and ownership
- OXsukra = interoperable ecosystem / shared contracts.
- IXO = native engineering workspace and operator authority. DOOR and ORBITAL provide architect/spatial project lenses.
- Thought Spine = freeform engineering notebook plus branch-aware temporal/causal history; EUREKA = promoted hypothesis/insight markers.
- Slotline = planned time, schedules and bounded work orchestration. Calendar = external commitments; PC clock = observed wall time; these are distinct.
- PARALLAX = real browsing surface with captured, permissioned provenance; GHOSTFIELD = gesture/MIDI signals; GREMLIN = offline capture/intake.
- Build Factory, Goose, Git services, models and third-party tools remain independently owned executors/adapters. The native IXO remains the subject and effect-authority surface.
- Meta-meta optimization (M²) is a capability within IXO: propose -> compose -> execute in isolated candidate -> evaluate -> preserve evidence -> human promotion or rollback.

## Temporal Boundary — non-negotiable
1. A measured, pixel-oriented ruler is permanently present at a desktop boundary, ordinarily the bottom edge, independent of active page.
2. Default visual height is approximately 0.5 inch at physical display scale; pointer proximity gently expands it to approximately 1.5 inches, with resolution/DPI calibration. These are design targets, not fixed pixel counts.
3. The resting strip compresses clock, Slotline, event density and spectral signatures into one continuous line-like band, not separate permanent mini-dashboards.
4. When foreground software covers/approaches the boundary, the strip becomes subordinate, darkened and partially occluded but remains locatable. At pointer approach it rises above context without requiring a program switch. Preserve the normal Windows taskbar and app focus.
5. A clear NOW cursor stays anchored to PC-observed time; historical scrubbing is a separate playhead and must never masquerade as NOW. If selected history differs from live time, show both.
6. At every temporal zoom, show ticks, units, labeled major intervals, timezone and actual pixel-to-time resolution. Zoom from milliseconds where measured, through minutes, hours, days, months, years and multi-year records.
7. Thermal density lives BEHIND the time ruler; event markers, forks, calendar commitments, source references, notes and evidence live ABOVE it. Avoid mixing units or equating intensity at incompatible scales.
8. Slotline planned windows, calendar events, observed execution and retrospective notes remain visually and semantically distinct. The calendar never proves that work happened.
9. Selection and hover reveal scoped events, connected files, model state, experiment receipts and branch lineage, without replacing the time reference.
10. Context persists through applications, source jumps, zoom, branches and restarts; dormant/abandoned ideas retain ancestors and do not become falsely labeled failures.

## Temporal input / motion states
- Rest: subtle live oscillations and a measured NOW cursor; activity is condensed; no constant attention-grabbing animation.
- Boundary hover: expansion upward, backdrop depth/dimming, progressively disclosed tracks. No modality trap.
- Pointer hover of event: focus lens, source identity and relationship wires; unrelated elements recede, not disappear.
- SHIFT while hovering: annotation / Thought Spine context and links, read-only by default. Annotation creation requires a deliberate click or input.
- CTRL+SHIFT on a selected event: modification / mapping workspace for permitted changes to parameter adapters, candidate branches, source links and Slotline allocations. Never apply silently.
- SHIFT+ALT: visual spectra / alternate lenses (proposal).
- ALT+T: temporal scale/navigation; ALT+P: selected model/parameter inspector (proposed remappable shortcuts).
- Wheel / drag: temporal zoom and scrub with visible scale; drag should not mutate source state.
- Keyboard chords are user-configurable and scoped to IXO focus, not globally intercepted. Provide clickable and accessible equivalents, plus reduced-motion mode.
- Outside hover, the boundary collapses gracefully while maintaining the temporal selection and source chain.

## The shared hashfield (a visual index, not an event database)
A multiresolution spatial-temporal hashgrid indexes source-backed events and exposes synchronized projections. Each event has an immutable unique ID, source/owner ID, time and duration (where known), timezone-normalized UTC, event type, payload schema, evidence reference, project/branch IDs, relationship edges and trust status. Hash collisions never conflate events: the grid indexes the underlying unique event records.

Spectra are alternate views into the SAME selected time:
- Thermal: activity, utilization or other selected quantity, always with legend, aggregation rule and units.
- Compute: resource use and training runtime measurements.
- Signal: wave/frequency/token/audio/MIDI activity where actual samples exist.
- Flow: directional transfers and handoffs.
- Phase: scheduling drift, latency and overlap.
- Causal: typed ancestry, dependency, hypothesis and fork lines; branch lines never imply proof without evidence.
- Verification: tests, regressions, independent receipts and proof gates.
- Uncertainty: gaps, missing data, inferred relationships and disagreements rendered differently from observed facts.
- Memory: preserved layers, old source revisions and thought fossils.

At low zoom render aggregates; zooming reveals original events with identity preserved. Visualization can show many projections simultaneously but must not obscure selection, labels and time measurement.

## Motion grammar — concurrent but legible
All animations may run concurrently; animation is secondary to source-backed state.
- Ambient: near-silent slow changes, uninterrupted clock, low contrast. Not fake telemetry.
- Operational: data/compute/source changes generate pulses along typed connections, anchored to event IDs and observed timestamps.
- Interactive: pointer proximity lifts geometry and reveals relationship wireframes; transitions maintain orientation.
- Temporal: scrub replays recorded transitions; show unrecorded intervals as gaps, not invented historical states.
- Evidence: verification signal follows the actual graph of test -> artifact -> result -> authority. Pass, fail, unknown and provisional states have clearly different movement AND shape, not only color.
- Fork: parent anchors remain, alternatives diverge with typed branch edges and preserve reversible lineage.
- Failure/recovery: interruptions, rollback and retry have distinguishable trajectories; no green flashes before true confirmation.

Visual style: precise 4K-native density, crisp instrument typography, deep near-black background, minimal luminous circuit traces, measured neon accents and high-resolution 2D -> 2.5D -> 3D spatial depth. Watch Dogs / cyberpunk are references for reactive scanning/wireframe grammar, not templates to copy. Avoid a permanent forest of glossy panels, random particle noise or animations that imply nonexistent computation.

Performance target: responsive native interaction at 4K/60fps on suitable hardware, adaptive detail under load; independent renderer/input loop; animation timing decoupled from slow inference; graceful degradation and reduced-motion preferences. This target is not measured performance.

## Parameter and Git mastery — eventual core experience
Select an actual file, Git commit, model, LoRA/adapter, evaluator or experiment and reveal its available, versioned parameters. Unsupported or unavailable parameters remain visibly unavailable; do not fabricate controls. A change:
1. Resolves concrete subject/owner/repo/commit/model/checkpoint IDs.
2. Creates an isolated candidate or typed fork with a reproducible diff and explicit approval boundary.
3. Applies only supported adapter mutations and records environment, tool version, seed/budget and source lineage.
4. Schedules with Slotline if chosen; reflects observed PC time separately.
5. Runs validation and evaluates results against an immutable baseline.
6. Adds evidence to Proofbook/independent OX WITNESS boundary; user reviews promotion or rollback.
7. Reopens the full lineage and parameter history from any point in the Temporal Boundary.

## Cross-surface navigation / screen roles
- Research / Project World: original project context, native execution and source-backed orientation.
- ORBITAL: operable systems-architect lens (typed ports, graph dependencies, editable actual records).
- Thought Spine/EUREKA: temporal ideas, hypothesis branches, annotations, source identity and evidence.
- Verification Theater: baseline/candidate comparisons, gates, receipts, failures and performance.
- Spatial Atlas: repos, collaborators, papers, model runs and lineage with real citations/source keys.
- PARALLAX: authentic webpage left and intelligence boundary right; temporal rail persists outside the page.
- Models & M² Workbench: parameter sweeps, adapter identity, candidate forks, compare and undo.

These are distinct cognitive sectors, not recolored identical cards. They share stable project, object, branch, time and origin IDs and always reconnect to the temporal boundary.

## Provenance and trust
- Distinguish OBSERVED, REPORTED, INFERRED, SIMULATED, MISSING and VERIFIED-by-independent-evidence.
- Never infer a running GUI, integrated source, completed agent task or merged Git branch from an image, README or test count alone.
- User-directed edits are explicit, bounded, reviewable and reversible. Do not deploy unsigned updates or execute unknown repository code merely because it appears in an index.
- The Karpathy research atlas and Fusion Lab are references and an optional external experiment lab. They are NOT proof of an installed feature in the authoritative native IXO source.
- Preserve native-first Windows/Android direction and offline local operation; do not substitute browser shells for native implementation.

## Engineering rule
FULL-SYSTEM design; MINIMUM independently provable change size.
All new work must trace into the existing authoritative IXO source / project identity. Avoid another replacement application or fake end-to-end demonstration. All feature claims need a source commit, test evidence and native-host interaction proof.

See IXO_NEXT_VERIFIABLE_STEP_2026-11-02.md for the delivery order and honest status.