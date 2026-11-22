# IXO L33T Subversion — visual system contract
**Status:** additive design language, not deployed renderer.
**Date:** 2026-11-11

## The useful “cheat”
Spend render resources on *perception*, not on fake system behaviour. Compose precise hairline vectors, shallow 2.5D planes, cached node loops, adaptive level of detail, parallax, event-driven animation and selectively lit source links to make a vast world navigable on ordinary hardware.

The spectacle is a user interface. It must never become a substitute for genuine files, data, actors, measurements or evidence. This extends the Temporal-Spectral Native Workbench baseline in this branch and does not create a second IXO shell.

## Four synchronized views, one canonical object
- **CLEAN:** minimal, legible presentation view. Spatial context and owner labels only when useful.
- **HUD:** actual owner, process, project, source reference, current time and supported parameter controls. If no adapter is registered, a control is visibly unavailable.
- **L33T:** optional stylized identity layer. Character substitutions, ASCII hints, sketch marks, redline annotations, lightweight glitch trails and scanline textures are purely *presentation transforms*, never mutations of source text.
- **PROOF:** readable and exportable evidence overlay: canonical ID, source owner, commit/hash where known, observation time vs replay time, effect authority, receipt IDs, verification result and unsupported claims.

A mode toggle never changes privileges. No “admin” visual theme gives execution rights. Every significant interaction decodes to canonical accessible text and a typed source reference.

## IXO visual identity
- Mostly near-black and white, with pixel-thin linework and pencil-texture interior shading.
- Red is used for warning, error or selected challenge; blue for distinct perspectives; green for established software home bases and bridges. Color alone never determines status.
- The OXsukra world is organic but anchored: a branching cybernetic sakura grows from dark/ASCII geometry; the “tree” is a relationship view, not a claimed live server.
- The observer camera can rise to God's Eye view, enter World Edit for supported operations, or descend into real owned programs.
- A/B/C context views: personal/social, projects/systems, finance/assets. Owners and permissions remain separate from presentation tabs.
- Compact optional VELA observer and freeform pencil/whiteboard annotation should never obscure normal controls.

## Cached scene algorithm (proposed)
1. Resolve a stable canonical node ID and immutable/temporal dependency fingerprint.
2. Render/cache a short loop and source-bound overlays. Mark it “illustration” when it is not generated from live telemetry.
3. Reuse the loop while source dependencies remain unchanged. Invalidate and refresh only affected regions.
4. Keep camera/parallax/UI motion independent of model inference; preserve measured timeline and a true NOW marker.
5. On selection, fetch owner-scoped source evidence. Missing proof stays visible. Do not invent connecting lines or historical transitions.
6. World Edit creates an isolated candidate diff; validation, approval and rollback live outside the renderer.

## Anti-deception rules
- An empty state says EMPTY. A disconnected adapter says OFFLINE or NOT INTEGRATED. A designed-only component says CONCEPT.
- A visually active node does not assert a running service unless heartbeat/state receipts are genuinely available.
- Historic replay gaps appear as gaps. Forecasts, proposals and remembered stories cannot be painted as observations.
- No automatic “verified” badges without trusted receipt validation.
- L33T text is reversible: screenshots may use stylized glyphs, but screen-reader labels, search terms and exported names remain canonical.
- All animation has reduced-motion and low-power equivalents.

## First engineering gate
Build one native IXO read-only projection of a REAL source/project record with CLEAN, HUD, L33T and PROOF toggles. Pass tests that: (a) every view resolves the same canonical ID; (b) a missing source cannot execute; (c) cached scene changes when dependency hash changes; (d) proof labels cannot be spoofed by visual state; (e) offline and no-data states render accurately; (f) no source mutation occurs during read-only navigation. Only then consider World Edit.
