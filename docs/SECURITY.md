# Security and disclosure

- Default is offline, no API calls, no executable research tools, no shell/code invocation by a model, no privilege escalation, no real trading, no MIDI device operations, and no autonomous coding. The app is **not a sandbox for untrusted code**.
- The GUI can write its new session database and copy explicitly chosen `.md`/`.txt` sources to its own new workspace, and nothing else. The CLI `demo` writes a new directory, refusing to overwrite files.
- Ollama is opt-in through `init --mode ollama --model NAME`; HTTP only to loopback, no bearer tokens or arbitrary URL. Source text is untrusted and may contain prompt injections, so model outputs remain proposals rather than execution authority.
- User-provided sources may contain personal data. Do not distribute a populated session or post the ZIP with real source content to a public Discord server without reviewing it. Example sources are synthesized technical notes grounded in the previous package, not independently verified research citations.
- One SQLite transaction contains snapshot and event receipts. An attacker with full workspace access can replace both state and hashes; this is not a trusted external audit system.
- The tested portability target is Windows Python 3.10+ with Tk, Linux Python 3.10+ with Tk. macOS has not been validated.
- No runtime modification to existing IXO, VELA, Opris, STRAY, APC or Syntra code is performed.
