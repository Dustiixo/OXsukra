# M2.23 — exclusive audition export
Existing destination files are refused even after confirmation in the save dialog. Choose a fresh filename. Exclusive creation prevents truncation of existing media; an encoder failure may leave a partial newly created file. Existing APIs and human approval are unchanged. No other project modified.
Rollback: extract M2.22 to a separate directory. No FID migration.
Linux tests only; Windows hardware, GUI and five-scene acceptance outstanding.
