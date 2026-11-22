# Behavioral contract: verifiable fluid scheduling

## Conserved session

- One `session_id` and immutable original `goal` persist across `step`, `spawn`, `park`, `wake`, `focus`, `revise` and source import.
- Root is the main goal address. It can temporarily become dormant if evidence is exhausted; user revision can reactivate it.
- Every input revision is a new event; nothing rewrites the original prompt. The generation timeline contains child branch tabs, not new root timelines.

## Spawn and budget rules

- Default per-cycle `budget_per_tick = 6` bounded work units; `2 <= budget <= 20`.
- At most 12 total branches and 5 active ones.
- `spawn` requires a nonduplicated, bounded question. Automatic *offline* triggers use fixed phrase patterns and are explicitly tagged heuristic.
- Active work allocation uses importance, user focus, evidence gains and recent source gaps; allocation sums never exceed the budget. Max two distinct Ollama requests per tick, parallelized by a bounded thread pool.
- A parked user's branch remains parked until the user wakes or directly revises it. A branch parked due to source exhaustion may wake when a previously unseen relevant excerpt arrives, at most 3 automatic reactivations.
- A duplicate source excerpt links paths without counting as new globally discovered evidence. Old work remains in the ledger.

## Provenance and sources

- Only `.md` / `.txt` up to 256 KiB per file are importable. Symlink files and symlink source directories are rejected. At most 128 source documents are indexed per scan.
- Each source quote carries exact source SHA-256 and paragraph SHA-256. `verify` checks every retained quote against the current copy. The application refuses to mark unverifiable excerpts as valid. Exact textual fidelity is NOT external factual validation.
- The event ledger uses a contiguous sequence, SHA-256 hash chain, atomic state transaction and optimistic revision control. This guards against accidental corruption and some tampering, but cannot authenticate an attacker who rewrites all records and hashes.

## Local LLM behavior

- Local Ollama address is fixed to 127.0.0.1:11434 with HTTP redirects rejected and proxies bypassed. The model produces an `analysis`, `uncertainty`, and optionally specific subquestions. No tool calls are exposed to it.
- Up to two different requests are concurrently issued outside state locks. When the user modifies prompt context during inference, its stale result is rejected. Parking a branch during inference discards its result. No work silently overwrites new user input.
- A model error records `model_unavailable`, parks that path, and does not invent results. Model proposals are a different status from source-verified excerpts.

## Nonclaims

This demonstration does not have a real-time process scheduler, GPU allocator, hidden-thought extractor, multi-host discovery, independent witness signature, arbitrary command runner, internet researcher, or autonomous software editing. `work credits` are a policy model, not an observed physical hardware resource use.
