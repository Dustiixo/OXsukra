# OX Treasury v0.17: private Seller Hub CSV normalization

**One bounded addition on verified v0.16.** This is a local, offline *own-sales* adapter for **eBay Seller Hub orders CSV**. The existing tracker, ledger, account-statement review and five-way virtual allocations are unchanged. It is **not** a feed of general completed sales, and its output is never automatically treated as verified or as income.

## Use (no account required for fictional demo)

From the extracted project folder on Windows, double-click `run_ebay_demo_windows.bat`. This reads **fictional** examples and writes a narrow `data/ebay_normalized_FICTIONAL.csv` without importing it to any database. Alternatively, in PowerShell:

```powershell
py -3 marketplace_map.py --source samples/ebay_own_orders_FICTIONAL.csv --inspect
py -3 marketplace_map.py --source samples/ebay_own_orders_FICTIONAL.csv --annotations samples/ebay_annotations_FICTIONAL.csv --currency CAD --out data/ebay_normalized_FICTIONAL.csv
```

The output CSV is compatible with the v0.15 offline sale claim importer, **but requires a separate explicit step**:

```powershell
py -3 sold_research.py data/ebay_normalized_FICTIONAL.csv
```

The second step writes only to the tracker evidence database and still records `unverified`, never to investment/treasury balances. Do not import fictional data into a real ledger.

## Legitimate, locally obtained seller exports

An eBay seller can download the **Orders** report in Seller Hub. eBay documents these columns: `Order Number`, `Item Number`, `Transaction ID`, `Item Title`, `Sold For`, `Quantity`, `Sale Date`. Documentation: https://www.ebay.ca/help/selling/selling-tools/seller-hub?id=4095 . Column names and date formatting can vary with export/report type; this exact profile is **not** certified against a real file. Start with a *redacted* CSV and check the column structure using `--inspect` (prints no raw buyer data).

Create a separate annotations CSV with exact columns:

`order_number,item_number,transaction_id,game,name,set_code,collector_number,condition,source_url`

These keys match the report's `Order Number`, `Item Number` and `Transaction ID`. Only explicitly annotated rows are converted. Card game, printing, condition and a **public HTTPS reference without query tokens** must be supplied manually; nothing is guessed from an item title. Source links are references, not evidence of settlement. eBay order reports may contain private buyer names, emails, addresses and tax information; **never upload unredacted exports or include private receipt URLs**. The converter discards all such columns when writing its normalized CSV. It does not encrypt or delete the original CSV already stored on your disk.

Use `--currency CAD` (or NZD, AUD, USD, EUR, GBP, JPY) explicitly; the `$` symbol is not enough to infer a currency. Only single-unit lines are supported. `Sold For` is not net profit and may not reflect cancellations/refunds, platform fees, shipping or taxes. Multi-unit sales, unknown card identities, unsupported dates, ambiguous IDs, inconsistent input and formula-like spreadsheet values fail safely. Unannotated rows are reported as *skipped*, not assumed to be card sales. The exporter uses a deterministic hashed sale ID instead of copying order/transaction IDs; no seller/buyer PII is transferred to the output. An input-file SHA-256 is provided for provenance, but **does not independently certify a completed sale**. Existing output files are never overwritten.

**No API credentials, web scraping, live bets, live trading, payment transfers, brokerage instructions or account creation.** The 15-minute tracker remains opt-in and is not automatically started. Local SQLite is unencrypted. The next important task is testing a redacted example from an actual eligible report, then (if appropriate) adding per-source reconciliation of cancelled/refunded orders.

---

# OX Treasury v0.15: offline claimed-sale evidence register

This is a **bounded extension of verified v0.14**, not a new project. All prior banking, betting-statement reconciliation, crypto/stock snapshots, share-heavy virtual allocations, opt-in 15-minute tracker and Scryfall indicative quotes remain in place. No real-money action is enabled.

## New: completed-sale research **claims**, not verified sales

- `sold_research.py` imports a user-supplied CSV of *claimed* completed trading-card sale examples into the **independent tracker SQLite DB**, not the treasury financial ledger. Supports Pokémon, Magic: The Gathering and Yu-Gi-Oh!. No automated web scraping, API access or accounts are required.
- Strict identifiers: game, card name, set code, collector number, marketplace, marketplace sale ID, sale date, price, original currency, condition, source HTTPS URL. Transactions are unique by marketplace + sale ID; idempotent re-imports are skipped, conflicting re-imports reject and roll back the entire batch. Files with malformed rows are rejected before any database writes.
- Every imported record is marked **`unverified`**, including rows that claim to be from a real site. A source URL is only a reference, *not* independent evidence that a sale took place. The example file contains **fictional records** only.
- Read-only dashboard now has a separate “Claimed completed sales” table and `/sales.json` endpoint with safe search and a bounded `limit`. Neither is merged into indicative card price charts; neither calculates investment profit or authorizes a purchase. Data stays in its original currency; no FX conversion or cross-currency totals. Each record includes its input file's SHA-256 and an import timestamp for audit traceability.

### Start with the fictional sample (Windows PowerShell)

```powershell
py -3 sold_research.py samples/claimed_sales_fictional.csv
py -3 watch_dashboard.py --db data/tracker.db --port 8766
```

Visit `http://127.0.0.1:8766` to see a separate **unverified sale-evidence** table, or `http://127.0.0.1:8766/sales.json?limit=100`. To import your own **redacted** export, use `py -3 sold_research.py "C:\\path\\to\\your-file.csv"`. Alternatively drag a CSV onto `import_sales_windows.bat` after extracting the ZIP. Import runs only when explicitly invoked; the 15-minute tracker never crawls or imports sales records autonomously.

**CSV columns (exact names, comma-separated):**

`game,name,set_code,collector_number,marketplace,sale_id,sold_at,price,currency,condition,source_url`

- `game`: MTG / POKEMON / YUGIOH. `sold_at`: ISO YYYY-MM-DD. `price`: positive amount with at most 2 decimal places in an explicitly stated currency (CAD, NZD, AUD, USD, EUR, GBP or JPY). For this research input, decimal-cent precision is used across currencies, including JPY; this is a technical limitation rather than an assertion about minor-unit conventions.
- `source_url`: HTTPS reference supplied by the user. Do not enter account credentials, tokens, private seller messages, personal addresses or private receipt URLs. The app neither visits nor validates the external source URL. A valid URL is *not* proof of a completed sale.
- Imports are bounded to 2 MB / 2,000 rows at a time, with all-or-nothing commit and data fingerprint checks. Imported rows remain in the local unencrypted SQLite DB; secure its storage. Dashboard search scans at most the latest 20,000 imported sale records; pagination is future work.
- **Do not infer market value or net profit from unverified sale examples.** Condition, print variant, fees, tax, shipping, actual offer price and provenance may differ; there is no sale authentication, price aggregation, inventory valuation or account integration in v0.15.

### Why no new live sold-data API?

Official eBay Product Research offers historical sold-price research in Seller Hub, but its existence is not public API authorization. TCGplayer documentation says it is not issuing new API access. This version supports evidence capture from legitimately obtained, user-controlled sources; it does **not** scrape a site or bypass access controls.

- eBay Product Research: https://www.ebay.ca/help/selling/selling-tools/terapeak-research?id=4853
- TCGplayer API getting started: https://docs.tcgplayer.com/docs/getting-started

## v0.15 testing and next step

Run `python -m unittest discover -s tests -q`. Next: selectable evidence details, source-aware export mapping based on a **real authorized redacted sample**, provenance review, and explicit quotes-versus-completed-sales comparison that never declares an unverified sale authoritative. Live read-only provider integration is still not verified and tracker remains opt-in/manual startup.

---
# OX Treasury v0.7 — Read-only Market Watch + Phase 2 Ledger

**A working cross-border personal capital tracker that adds CSV ingestion, ledger matching and manual reconciliation to the v0.2 five-way allocation engine.** Written in Python standard library; no pip install. Runs locally on Windows (Python 3.10+) and Linux. **No PayPal/brokerage/gambling/exchange APIs or authentication; no wagers placed, orders submitted, crypto transfers, auto-withdrawals, or real-money operations.**

## Start on Windows

1. Extract all files in the ZIP into a folder (do not launch directly from inside the ZIP).
2. Double-click `run_demo_windows.bat` for a **fictional** ledger. Double-click `run_windows.bat` for the separate, initially blank live-record ledger.
3. Open `http://127.0.0.1:8765` if your browser does not open automatically. The app binds only to loopback (your PC).
4. Click **CSV imports & review**. Choose an existing account, select *Cash / Bets / Holdings*, and select a local CSV export. If needed, add an account first in **Accounts**.
5. Click **Preview file and detect columns**. Review or correct the column mappings, especially **signed NET amount** and currency. Click **Stage rows**.
6. Review each row; choose **Post cash in / Post cash out / Post fee / Record bet / Update holding**, **Match reference** if already recorded, or **Ignore**. Nothing changes the ledger until you explicitly review and approve a row. Pending/failed/reversed cash transactions cannot be posted.
7. Close the command window to stop. For backup, shut down the app and copy the whole `data` folder; its SQLite `treasury.db` is sensitive, unencrypted personal financial data.

### Example files

The `samples/` directory contains **fictional exports** that can be loaded into the *demo* ledger:

| CSV | Import type | Select account |
|---|---|---|
| `sample_wallet_cash.csv` | Cash | `PayPal Canada` (placeholder) |
| `sample_sportsbook_bets.csv` | Bets | `Ontario sportsbook` (placeholder) |
| `sample_crypto_holdings.csv` | Holdings | `NZ crypto account` (provider unknown) |

The generic column mapping is *not* a guarantee that PayPal, an NZ crypto platform, Robinhood or any sportsbook offers that exact CSV shape. Use the real exported headers and adjust the mapping. If you use a broker with a different base currency, record the **asset's quoted currency**, not automatically the account's base currency.

## Update your existing v0.2 database

If you have **actual records** in v0.2, do not throw them away. Stop both Treasury instances, then in v0.3 double-click `migrate_from_v0_2_windows.bat` and paste your previous extracted folder path (or the full path to `data/treasury.db`).

This uses SQLite's backup mechanism to copy/migrate your old ledger into v0.3's `data/treasury.db` and retains v0.2 transactions, holdings, five-way weights and buffers. It **never modifies the old DB and refuses to overwrite an existing v0.3 DB**. If you already launched v0.3 with the empty real ledger, a `data/treasury.db` exists: back it up and move it out of the folder before migration, or use a fresh v0.3 extraction.

On Linux: `python3 migrate.py --source /path/to/OX_Treasury_v0_2` then `python3 app.py`.

## What Phase 2 now does

- Preview and parse UTF-8 CSV exports, up to 2 MB / 5,000 rows / 60 columns; configure mappings rather than assume a specific provider's format.
- **Cash**: signed transaction amount, optional provider ID/date/status/description/currency. A positive signed NET amount can be posted as *cash in*; negative can be *cash out* or *fee* after review. An internal transfer is **not income**: record the paired transfer once in Money movements and match the imported side(s) against its shared reference.
- **Wagers**: import stake, gross payout (including 0 for settled loss), status, sportsbook reference, date. Historical open-bet rows can later be reconciled against a separate settled version with the same provider bet ID; that updates the same ledger bet instead of double-counting it. A bet can only be posted if the tracked sportsbook balance covers its stake. No wager is placed.
- **Holdings**: inspect and approve snapshots for stocks, ETFs, crypto, or skins. Importing a snapshot does **not** create a share purchase or cash, and an older ISO-dated snapshot cannot overwrite a newer recorded position. Dates use ISO 8601 when available; ambiguous locale dates are not guessed.
- Provider ID + profile + account deduplication; rows with conflicting values are flagged. **Without external transaction IDs, only reimports of the identical file are deduped reliably**; overlapping files must be manually checked. Imported records preserve normalized values, statement file SHA-256 and mapping metadata for audit (not the complete original file).
- Per-batch reconciliation: counts for staged/applied/matched/ignored, rejected rows, observed cash movement totals, observed stake/payout/settled P&L, and per-currency holdings valuations. Totals are **per batch**, not a verified complete account statement. Nothing gets marked independently verified merely because the source is CSV.
- JSON export includes the import history and audit issues. Existing manual accounts, currency separation, betting limits, buffers, profit-sweep controls, and **50% shares / 15% crypto / 20% reserve / 10% fun money / 5% wager budget** weights remain intact.

## Accounting warnings and hard limitations

- **No live site integration:** this is *local CSV import + review*, not an authorized PayPal, bank, crypto, betting site or brokerage API integration. There are no automated transactions.
- **A CSV file is not verification.** It could be incomplete, wrong, duplicate, unposted, pending or manipulated. Confirm against the original site's settled/exported records. The app doesn't have an independent statement balance/feed, and cannot prove complete profit or final tax liability.
- **No auto-profit:** cash deposits, withdrawals, transfers and account market values do not automatically create gambling profit. A bet's P&L is payout minus stake, but *partial histories* can still misstate cumulative results. The pool only considers explicitly confirmed existing profit-sweep ledger movements; it is still simulated/virtual.
- **Do not import trades as cash.** Crypto/stock trades may have a cash leg, asset leg and fees; Phase 2 only handles cash movements, sportsbook bets and holdings *snapshots*. Trade/cost-basis lots and corporate actions are Phase 3 candidates.
- **Currency is not fungible.** CAD, NZD, AUD and USD remain separate. A USD stock price in an NZD-based account is reported in USD, never added to NZD without a real FX rate. Forex conversion must be manually posted with actual sent and received amounts.
- **Unmatched transfers may inflate apparent inflows/outflows.** The app never infers that a sportsbook withdrawal also reached PayPal. Use a single explicit transfer if both accounts are tracked.
- **Local data is plaintext** in SQLite; keep backups, secure the computer/disk, and do not upload a personal DB or real account statements to public repositories. No provider credentials or API keys are requested.
- Site legality and eligibility depend on residence and actual provider registration in Canada, NZ and Australia. A labelled `NZ Robinhood` account remains unverified until the legal provider and product are confirmed.

## Test it

Run from the extracted directory:

```sh
python -m unittest discover -s tests -v
```

See `tests/test_core.py` for all 16 retained v0.2 ledger tests and `tests/test_imports.py` for import, duplicate, review, currency, P&L, snapshot and migration-adjacent invariants.

## What Phase 3 should address

1. Obtain **redacted** sample exports from the real sites you actually use (without personal identifiers, tokens or passwords) to write accurate provider adapters and statement-balance reconciliation.
2. Add cost-basis/trade histories, account-level opening/closing statement balances and currency-specific performance reports.
3. For accounts with explicit official API permission, add opt-in **read-only** balance/transaction feeds and reconciliation tests. Never circumvent provider restrictions.
4. Keep execution permissions distinct and off by default. No investment or betting automation should be enabled merely because read-only imports work.

## v0.4 fixture tracker (separate CLI)

From this directory, run `python tracker.py status`, then `python tracker.py enable` and `python tracker.py run`. In another terminal run `python tracker.py pause` to persistently pause; Ctrl+C stops the process without changing opt-in. Restart `run` manually after reboot. `tick` performs at most one due iteration. The default database is `data/tracker.db`, independent of the financial ledger. Successful observations repeat after 900 seconds; failed attempts back off up to four hours. Observations become stale after 30 minutes. The only adapter is a fictional fixture, not a live market feed. No network requests or financial writes are made. No GUI or OS startup installation is included. Existing v0.3 app and ledger schema are unchanged; keep your original database backed up.

## v0.5 offline card discovery slice

The tracker can now read a local CSV catalog and JSON watchlist for MTG, Pokémon and Yu-Gi-Oh, matching only exact game/set/collector-number identities. It does not query live marketplaces, infer prices, or alter the financial ledger. The bundled catalog is **fictional**, for tests only. Supply your own lawful, sourced CSV for real catalog matching. Source labels are retained per row; validate data rights before importing provider exports.

Example (Windows terminal in extracted folder):

```
python tracker.py enable
python tracker.py tick --watchlist samples/watchlist.json --catalog samples/offline_cards.csv
python tracker.py status
python tracker.py pause
```

For ongoing refresh, use `python tracker.py run --watchlist ... --catalog ...` instead of `tick`. This loop must be started locally; it is not a Windows service. The default tracker still uses fictional data. The tracker database is independent of the financial ledger. Its current single-run lock is SQLite BEGIN IMMEDIATE held during fetch, so long fetches may block other tracker commands; network adapters are intentionally not enabled. For catalog data freshness, `stale` measures last local observation time, not age of the source CSV. No actual market prices are provided.

## v0.6 tracker lease safety
The tracker now reserves a 120-second lease in a short SQLite transaction, releases the
transaction before calling a data provider, and commits observations only if the lease
still belongs to that worker. Pause cancels the lease. After a crash, another worker can
recover an expired lease. Existing tracker.db files are migrated in place with two
nullable/defaulted control columns. `status` exposes `in_flight` and `lease_expires_at`.
Provider calls are still synchronous and **not** forcibly timed out; future network
adapters must set their own bounded HTTP timeout and rate limits. A blocked provider
may outlive its lease but cannot overwrite a newer worker's result. No network provider
or live market price feed is included. Python 3.13 may report sqlite ResourceWarnings
from legacy connection handling; these are tracked for follow-up.

## v0.7 — opt-in Scryfall exact-card connector + safer tracker

This section supersedes older tracker sections above where they differ. **Do not put passwords, API keys, personal card collection values or financial statements in a watchlist.** The local financial ledger is still entirely separate. No bets, investment trades, wallet movements or payouts are ever performed by the tracker.

**What changed:** The tracked job reserves a **180-second lease** in SQLite, closes the write transaction before provider I/O, and discards stale in-flight results if paused or superseded. It avoids multiple workers running the same cycle and respects a 15-minute interval. The file-based v0.5 CSV adapter continues to work. Closing the tracker SQLite transaction now also closes its connection to eliminate its own connection warnings.

There is now an **optional live, read-only MTG card lookup adapter** using [Scryfall](https://scryfall.com/docs/api). It performs exact set-code + collector-number lookups for **up to 20 cards** per cycle. It uses only the fixed HTTPS API origin, custom User-Agent / Accept headers, 6-second per-request timeout, 256 KB response cap, at least 250 milliseconds between requests and a 429 pause respecting Retry-After. Do not scale to bulk collection lookups; Scryfall recommends bulk data for that use case. Provider daily price estimates are not historical completed sales, actual execution prices, nor certified profit. `price_as_of` is explicitly unknown; `observed_at` is when **your computer** collected the observation.

### Windows commands (inside extracted directory)

Enable the independent tracker database (no network access yet):

```powershell
py -3 tracker.py enable
```

Run **one** real read-only MTG lookup only if you choose to connect to Scryfall:

```powershell
py -3 tracker.py tick --provider scryfall --watchlist samples/scryfall_watchlist.example.json --consent-network
```

Or run the opt-in 15-minute local loop:

```powershell
py -3 tracker.py run --provider scryfall --watchlist samples/scryfall_watchlist.example.json --consent-network
```

Inspect and pause from another terminal:

```powershell
py -3 tracker.py status
py -3 tracker.py pause
```

The following v0.5 offline command **still works** (it does not send network requests):

```powershell
py -3 tracker.py tick --watchlist samples/watchlist.json --catalog samples/offline_cards.csv
```

`run` is a foreground process, **not installed as a Windows service or scheduled task**. It must be started manually each time the computer restarts. The default `fixture` mode is fictional; no network requests. Python 3.10+ with the standard library is sufficient. Scryfall requests require internet access. The adapter is coded and tested with mocked responses; a live network response was **not verified** in this build environment.

### Provider limitations and permitted use

- Cards are matched by exact set + collector number only. Pokémon and Yu-Gi-Oh remain **offline CSV only**.
- A 404 records unmatched; malformed or mismatched provider identities are rejected. Last successful observation is retained on error and marked stale after 30 minutes. Failures back off automatically.
- `USD`, `EUR` and MTGO `tix` fields stay separate. Never convert or sum them into CAD/NZD/AUD without a verified exchange-rate source.
- Published Scryfall prices are **estimates**, not sold-comparable transactions. No buy/sell recommendations are produced.
- 429 responses must not be retried repeatedly. The scheduler pauses up to four hours, using the provider's numeric `Retry-After` when available. For sustained restrictions, stop the tracker and switch to licensed/bulk data.
- Network access is explicit with both `--provider scryfall` and `--consent-network` and is unavailable in default mode. These controls are for personal research, not merchant automation.

### Verify

```powershell
py -3 -m unittest discover -s tests -q
```

## v0.8 read-only Card Watch dashboard

The tracker must be enabled and run independently. In a second terminal:

```sh
python watch_dashboard.py --db data/tracker.db --port 8766
```

Visit http://127.0.0.1:8766 . Only localhost is bound. The dashboard reads the existing tracker SQLite observations, auto-refreshes the browser once a minute, displays source/currency/collection age and labels upstream quote timestamps unknown unless supplied by the observation. It does not fetch provider data, place orders, alter the ledger or enable the tracker. JSON status is available at `/status.json`; POST is rejected. Do not expose this local server through port forwarding or a public reverse proxy. Card prices are indicative, not verified completed sales.

### v0.9 observation history
Successful tracker ticks now append up to 500 historical snapshots to `observation_archive` in the tracker database. This is distinct from the existing latest observation and from the financial ledger. The localhost dashboard exposes read-only `GET /history.json?limit=100` (limit 1–500). Historical collection times are **not** upstream quote times and indicative prices are **not** confirmed sold prices. Existing latest-only databases migrate without fabricating past observations. No network requests are made by the dashboard.

### v0.10 local history trends
The read-only Card Watch dashboard now renders SVG price histories from archived observations. Trends are separated by game, card name, set, collector number, currency, and provider source. Collection gaps exceeding 30 minutes are shown as disconnected segments. This does not validate provider quote freshness or represent confirmed sales. Run `python watch_dashboard.py --db data/tracker.db --port 8766` after the tracker has collected observations.

### Card Watch series selection (v0.11)
The local read-only dashboard now includes a server-rendered **Price series** selector. Use the dropdown or `/?series=0` through `/?series=39` to display one indexed series; `/?series=all` displays all available series. Series are sorted by card identity, currency and provider. Indices are temporary display positions, not stable card identifiers. SVG charts include text titles and descriptions; quote timestamps remain distinct from local collection times.

### v0.12 dashboard selection
Card history selection now uses a stable 24-character identity hash across game, card name, set, collector number, currency and provider. Existing numeric `?series=1` URLs still work but are not stable. SVG includes visible UTC endpoint labels and price extrema. No network fetch is triggered by dashboard navigation.

## v0.14 searchable historical series
Dashboard search `q` filters all historical card/source/currency identities before display capping; no network requests. Unfiltered display remains limited to 40, filtered to 100.

### v0.16 offline sale-evidence review
After importing a sale CSV, attach a local analyst note to an existing sale ID:

```powershell
py -3 sale_review.py --marketplace "Demo Only" --sale-id "demo-1" --decision needs_review --note "Check original receipt"
```

Allowed decisions: `needs_review`, `document_seen`, `disputed`, `excluded`. The latest annotation is returned in `read_sales()` and `/sales.json`, and earlier annotations remain in the local `sale_review` table. `document_seen` only records a human observation: **every sale remains `unverified`**, including after review. No sales evidence changes the portfolio ledger, market-price series, or allocations. No external source is fetched. The sample CSV is fictional; use the exact marketplace and sale ID in your own imported file.
