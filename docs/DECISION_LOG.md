# Engineering decisions (not story canon)

- 2026-11-03: Audit found prior conversation-provided UNDERBYTE HTML experiments, no native Godot source in mounted files; user directed full implementation. Work isolated in new `/mnt/data/UNDERBYTE_NATIVE_GODOT` project. Prior files preserved unchanged.
- 2026-11-03: Selected Godot 4.7.2 stable for a native Windows-first core and later Android reuse. Not assumed installed. No GitHub production changes made.
- 2026-11-03: Original programmatically generated pixel assets/audio, avoiding external uncertain licensing.
- 2026-11-03: Implemented direct-control first and excluded autonomous desktop, real file/program access until separately gated.
- 2026-11-03: Content uses provisional quest names and deliberately leaves protagonist's actual mission unknown.
- 2026-11-03: Project is not promoted to verified native game until Godot import, real graphical control/reload tests and Windows packaging pass.
