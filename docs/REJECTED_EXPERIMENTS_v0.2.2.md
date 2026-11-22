# Rejected / deferred alternatives

- **Replacing the original Self VM with a JavaScript Self-like object graph:** rejected. It cannot prove native semantics, Morphic or the outliner.
- **Accepting arbitrary Transporter/file-out source as a string with regex:** rejected. The Self grammar permits executable expressions and module code; the current bridge only accepts an exact template with one numeric slot changed.
- **Treating an HMAC receipt or an operator `objectOutlinerObserved` boolean as native VM attestation:** rejected. HMAC authenticates a signer; it does not attest execution.
- **Importing slot edits automatically into protected programs:** rejected. Existing manual proposal/commit gate remains required.
- **Calling the empirical entropy-based byte patcher Meta BLT:** rejected. No Meta model/weights were run.
- **Native Self build in this container:** blocked by absence of binary/source and inability to resolve `github.com` with direct `git` in the container. Official handbook instructions and remaining prerequisites documented under `docs/SELF_NATIVE_GATE.md`.
