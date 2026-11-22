# Actual Self runtime: manual handoff, not yet a live adapter

This folder contains `oxSpliceObject.self`, an **experimental native Self-language object literal** that uses a parent slot and assignable data slots. It is not code running in a Self VM in this package.

Reference source: https://github.com/russellallen/self and https://handbook.selflanguage.org/2024.1/morphic.html. To test: install the **original Self 2024.1 runtime and Morphic world** per the official build/run instructions, then evaluate the object literal in a Self evaluator. It should produce a native Self object which can be inspected with the standard outliner. The exact loading and evaluation procedure depends on the local Self world; this file has not been executed against a Self VM in our test environment.

To pass values back to the running local web projection, enter bounded slot assignments in the **SELF SLOT INPUT** panel, e.g.:

```text
depth: 1.2.
twist: 2.0.
hue: 0.
threshold: 0.18.
```

This is **manual** exchange: it intentionally does not implement Self FFI, arbitrary script execution, continuous IPC, or automatic protected IXO writes. The input parser accepts only the four numeric key names. The web editor's **EXPORT .SELF** button emits a native Self object literal with the chosen mapping values and measurement fingerprint as data, enabling experimentation in the original Self environment once installed.

Next steps for live connection after verifying Self VM: develop a real `applications/` module via Self's Transporter, register only an **unprivileged, read-only** adapter to the RCLL data contract, prove Self-side slot changes can be externally serialized, then expose bounded write requests to the IXO broker with user review. The browser remains isolated from arbitrary Self runtime execution.
