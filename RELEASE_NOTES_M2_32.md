# M2.32 | A/B audition keyboard controls

One improvement: while the modal A/B audition window has focus, A plays original, B plays edited, Space stops, Escape closes. Existing mouse controls, sample cue, and media provenance unchanged.

Verification: Linux automated tests and Python compileall passed; keyboard binding regression is source-level only. No physical Windows driver/audio acceptance, and no native Tk key-event smoke in this run.

Rollback: extract immutable M2.31 separately. Do not overwrite FID or source recordings.
