# Reconstructable example flow

1. `session_created`: goal enters the prompt timeline.
2. `source_imported`: three bundled local reference documents copied into a new workspace.
3. `resource_allocation`: first cycle gives the original goal up to six work units; initial sources are examined.
4. `probe_launched`: explicit heuristics identify research questions about MIDI timing, generation and agent resource scheduling. Each is a branch **tab** on one generation timeline.
5. `source_excerpt_verified`: one exact source paragraph is quoted with its content hash. This is evidence of what a particular document says, not external truth.
6. `resource_allocation`: the next cycles distribute credits across active branches, not a permanent fixed set.
7. `branch_parked`: a user can stop any active probe without deleting its evidence or ongoing goal.
8. `prompt_revision`: a new instruction is added without rewriting the original.
9. `branch_reactivated`: the parked branch is resumed, returning its accumulated research context.
10. `tick_finished`: continued observed work; `verify` checks event order, snapshot and retained source hashes.

**How to challenge the experiment:** change a source file inside `sample_output/SESSION_DEMO/sources/` or alter a SQLite event payload in a disposable copy. `verify` must fail rather than inventing a clean receipt. Restore from the untouched ZIP afterward.

**What concurrency means here:** in offline mode the same worker engine retrieves source paragraphs deterministically. In Ollama mode two distinct local-model requests are allowed to overlap on separate Python threads while the desktop stays responsive. This does **not** reserve GPU cores, preempt model inference, or spin up a cluster.
