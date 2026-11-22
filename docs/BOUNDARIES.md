# Underbyte boundary decisions

## Gate 1 — foreground only (current source)
- The game window owns its input. Keyboard and pointer events are handled only when the game is in focus; no global hooks or OS key capture.
- Mouse grab/drop affects a game-owned sprite only, never the desktop cursor or another application's files/window state.
- World simulation pauses when any in-game menu is open. No offscreen automation, background processes, system agents or timed external behavior.
- World data is fixed bundled JSON. The only write is the versioned game save under Godot's user-data directory, with pending write and previous-save backup.
- No trusted app identities, accounts, cloud services, network calls, telemetry or background desktop overlay.

## Gate 2 — future Windows living desktop mode (not authorized or built here)
Required: opt-in interaction scope; non-interfering input pass-through; focus-loss and emergency reset; pause/quiet limits; window-clipping/DPI tests; read-only source adapters; explicit audit; kill switch; privacy review; real-host verification. No blanket permission to control processes.

## Gate 3 — future authorized program-as-instrument mode (not built)
A source adapter can consume only user-selected files/folders/program APIs under least privilege; gameplay operates on copies/interpretations. Real writes require separate, revocable approvals. No injection, surveillance, automatic code execution or indiscriminate filesystem scan.

## Gate 4 — Android (not verified)
Reuse the foreground simulation and explicitly test orientation, scaling, input, save location, audio and battery/thermal performance before calling it a mobile build.
