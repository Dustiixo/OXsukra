# Native Self G1 gate: real VM/Morphic evidence, not surrogate execution

## What has been verified in v0.2.2

An original-byte, representation-print, revision and ledger-head-bound Self object **literal** is produced by `self-export`. A byte-identical copy with **exactly one bounded numeric slot edit** can be checked by `self-stage`, authenticated using an operator-held HMAC key, and imported via the existing review-only Self receipt intake. A separate `commit --approve` changes only the mapping and produces a new versioned geometric render. The complete loop is exercised with a **controlled edited text fixture, not the native Self VM**.

The changed file must be a line-for-line copy of the generated object literal, differing in just one `depth`, `twist`, `hue` or `threshold` numeric value. It does not accept arbitrary Transporter module source, standalone `fileOut` forms, or Self expressions. No Self code is parsed as executable code.

## Gate G1: independently execute the original language

Reference: [Self 2024.1 build instructions](https://handbook.selflanguage.org/2024.1/build.html) and [Morphic/outliner procedures](https://handbook.selflanguage.org/2024.1/howtoprg.html). Use actual `https://github.com/russellallen/self` VM **and** Self world. The 2024.1 handbook describes a traditionally 32-bit build and X libraries; recent 64-bit work may change this, so pin the actual source commit and build dependencies. Do not guess an executable's provenance from its name.

1. On a network-capable scratch system, acquire upstream Self from its official repository; record source commit and the exact build commands/logs, binary hash and world image hash. Do not copy it into protected IXO/VELA repos.
2. Build/launch VM with a world that loads Morphic. The historical handbook documents `Self -f /path/to/Self/objects/worldBuilder.self -b /path/to/Self/objects -o morphic,ui1`, then `desktop open` at the Self prompt. Capture VM startup and Morphic launch evidence; do not substitute a screenshot of browser Morph Lab.
3. Create a scratch OX byte world using `bytebridge.cli ingest`, then `self-export`. Copy `world/self_exchange/rev00000/baseline.self` **outside the world**. Evaluate that generated expression using the native Self evaluator, and inspect it in a live Morphic outliner. This is a provisional parsing recipe, not a confirmed tested command for that runtime.
4. Edit *one* assignable numeric slot in the live object (e.g. `depth`), inspect new value and capture a repeatable way to serialize the **same allowed literal text**. Standard Self Transporter file-out may reformat the object and is not accepted by v0.2.2's strict checker. Provide a known-good serializer or a separate typed extractor only after native examination. Record a real runtime transcript, not an operator-typed claim.
5. Compare the serialized object to the exported source. Use `self-stage` and `self-import` only if it differs in exactly one allowed numeric literal, then inspect and explicitly approve the proposal. Capture commit, render and source hash identities.
6. Independently reproduce under a pinned Self VM binary and world snapshot. Only then change the native Self gate from BLOCKED to VERIFIED. Keep a distinct `runtimeVerified` assertion signed by an independently trusted runner if authentication rather than operator attestation is required.

## Current blocker

On 2026-11-21 the current execution container had no `Self`/`self` binary. `git ls-remote https://github.com/russellallen/self.git` failed with `Could not resolve host: github.com`. The machine has GCC and Xvfb but a native Self runtime/source checkout and tested world are absent. Therefore **G1 has NOT passed**. The generated object expression is an export candidate, not a verified native object.

## Why the file-out gate remains real work

Self is a live object system. Its Transporter serializes modules and program structures, which may not be a byte-for-byte copy of a restricted source expression. A successful source-diff test is a deterministic interchange contract, not proof that a Self object was ever created in the VM. A future runtime-backed adapter must distinguish such observations from synthetic/manual source edits.
