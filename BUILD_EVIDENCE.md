# OX Treasury v0.17 — build evidence

- Recovered verified v0.16 checkpoint from Library and container.
- v0.16 source SHA-256: `4e53057a09275ce83def0a64ed6e61cd7623bfcfc596bc2e83eae27c3916d063` (matches v0.16 continuity manifest).
- Baseline `python -m unittest discover -s tests -q`: **84 tests, OK**.
- Final `python -m unittest discover -s tests -q`: **93 tests, OK**.
- Final `python -m compileall -q .`: exit 0.
- Changed source: new `marketplace_map.py`, new test file, new fictional CSVs and Windows demo launcher, README documentation.
- Existing core/ledger/tracker/Scryfall/dashboard/sale research/review files byte-for-byte unchanged: **9 files verified**.
- New adapter is a private, opt-in, offline normalizer for eBay Seller Hub OWN-order CSV, not live market completed-sales feed.
- All prices remain unverified; nothing updates investment balances or automatically executes transactions.
- Demo files fictional, no credentials, no live API requests, no web scraping, no real betting/trading or transfers.
- Adapter not yet tested against user-owned real redacted export; provider may change formats.
- SQLite remains unencrypted; card markets have no independent sale verification; 15-minute tracker requires user-local execution.
- Next: test a redacted official export with safe per-source cancellation/refund reconciliation and provide a guided review UI.
