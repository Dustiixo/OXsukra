# OpenCode adapter — experimental

`/worker` reports local availability through the existing IXO command surface.

Python API: `EngineeringWorker().run("Inspect tests", "/path/to/workspace")` previews a task without executing it. Add `approve=True` to run.

This adapter does NOT sandbox OpenCode. Execute only in a disposable copy of a workspace, with an explicitly configured provider and reviewed OpenCode permissions. It does not propose Hermes facts or modify Habitat. A model provider may have separate usage costs; there is no mandatory IXO subscription.

This is an integration seam, not a complete REA/ArtCraft integration.
