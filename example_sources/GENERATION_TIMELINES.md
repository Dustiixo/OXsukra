# FlowMesh example research notes: design hypotheses, not outside validation

Generation and prompt timelines are distinct: the first records prepared and generated work, while the second records evolving human instructions. Real program state has its own execution timeline.

Generation branches appear as tabs connected to one generation job rather than three disconnected main timelines. A proposal may be staged before the user supplies additional conditions.

A prompt can arrive after computation has started. Only future, not-yet-committed work can use that prompt without rollback or regeneration. Processing latency is a scheduling opportunity but not a reason to add artificial lag.

Prompt revisions may specify new targets, corrections, constraints, or ambiguous partial ideas. Ambiguous speech cannot be assumed to authorize executable system actions.
