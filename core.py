"""OX Treasury v0.3: local, review-first financial tracking.

No external account access, order placement, deposits, withdrawals or real money movement.
All monetary ledger values are integer minor currency units (cents).
"""
from __future__ import annotations

import datetime as dt
import re
import sqlite3
import uuid
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

CURRENCIES = {"CAD", "NZD", "AUD", "USD"}
ACCOUNT_KINDS = {"bank", "wallet", "sportsbook", "crypto", "broker", "skins"}
COUNTRIES = {"CA", "NZ", "AU", "US"}
EVENT_KINDS = {"cash_in", "cash_out", "transfer", "fx_transfer", "fee", "profit_sweep"}
BUFFER_PURPOSES = {"betting", "investing", "reserve", "fun", "shares", "crypto"}
BUFFER_ACTIONS = {"hold", "release"}
EVIDENCE = {"unverified", "user_recorded", "statement_matched"}
SEED = [
    ("ca_paypal", "PayPal Canada", "wallet", "CA", "CAD", "active", "unverified"),
    ("ca_bank", "Canada bank (placeholder)", "bank", "CA", "CAD", "active", "unverified"),
    ("ca_sports", "Ontario sportsbook (placeholder)", "sportsbook", "CA", "CAD", "active", "unverified"),
    ("nz_crypto", "NZ crypto account (provider unknown)", "crypto", "NZ", "NZD", "active", "unverified"),
    ("nz_robinhood", "NZ Robinhood-labelled account (provider to verify)", "broker", "NZ", "NZD", "active", "unverified"),
    ("au_bank", "Australia bank (planned)", "bank", "AU", "AUD", "planned", "unverified"),
    ("au_broker", "Australia investments (planned)", "broker", "AU", "AUD", "planned", "unverified"),
]


def cents(value):
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d < 0:
            raise ValueError("Money must be finite and nonnegative")
        n = int((d * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if n > 10**15:
            raise ValueError("Amount too large")
        return n
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValueError("Invalid money amount") from e


def money(n):
    return f"{Decimal(n) / 100:.2f}"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def db_open(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(str(path), timeout=10)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA foreign_keys=ON")
    cx.execute("PRAGMA journal_mode=WAL")
    cx.executescript("""
    CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY, name TEXT NOT NULL,
        kind TEXT NOT NULL, country TEXT NOT NULL, currency TEXT NOT NULL,
        status TEXT NOT NULL, verified TEXT NOT NULL DEFAULT 'unverified',
        opening_cents INTEGER NOT NULL DEFAULT 0,
        CHECK(opening_cents >= 0)
    );
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        at TEXT NOT NULL, kind TEXT NOT NULL,
        source TEXT REFERENCES accounts(id), target TEXT REFERENCES accounts(id),
        source_cents INTEGER NOT NULL DEFAULT 0, target_cents INTEGER NOT NULL DEFAULT 0,
        source_currency TEXT, target_currency TEXT,
        evidence TEXT NOT NULL, reference TEXT, memo TEXT NOT NULL DEFAULT '',
        UNIQUE(reference)
    );
    CREATE TABLE IF NOT EXISTS bets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT NOT NULL REFERENCES accounts(id),
        category TEXT NOT NULL, stake_cents INTEGER NOT NULL CHECK(stake_cents > 0),
        payout_cents INTEGER CHECK(payout_cents >= 0),
        placed_at TEXT NOT NULL, settled_at TEXT,
        reference TEXT UNIQUE, memo TEXT NOT NULL DEFAULT '',
        evidence TEXT NOT NULL,
        CHECK(payout_cents IS NULL OR settled_at IS NOT NULL)
    );
    CREATE TABLE IF NOT EXISTS positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT NOT NULL REFERENCES accounts(id),
        symbol TEXT NOT NULL, asset_type TEXT NOT NULL,
        quantity TEXT NOT NULL, unit_price TEXT NOT NULL,
        quote_currency TEXT NOT NULL, observed_at TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'manual',
        UNIQUE(account,symbol)
    );
    CREATE TABLE IF NOT EXISTS buffer_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        at TEXT NOT NULL,
        account TEXT NOT NULL REFERENCES accounts(id),
        purpose TEXT NOT NULL CHECK(purpose IN ('betting','investing','reserve','fun','shares','crypto')),
        action TEXT NOT NULL CHECK(action IN ('hold','release')),
        amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
        memo TEXT NOT NULL DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS play_rules (
        account TEXT PRIMARY KEY REFERENCES accounts(id),
        ceiling_cents INTEGER NOT NULL CHECK(ceiling_cents > 0),
        enabled INTEGER NOT NULL DEFAULT 1 CHECK(enabled IN (0,1))
    );
    CREATE TABLE IF NOT EXISTS allocation_commits (
        id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
        account TEXT NOT NULL REFERENCES accounts(id),
        amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
        reserve_cents INTEGER NOT NULL CHECK(reserve_cents >= 0),
        stocks_cents INTEGER NOT NULL CHECK(stocks_cents >= 0),
        crypto_cents INTEGER NOT NULL CHECK(crypto_cents >= 0),
        fun_cents INTEGER NOT NULL CHECK(fun_cents >= 0),
        wager_cents INTEGER NOT NULL CHECK(wager_cents >= 0),
        source_event INTEGER NOT NULL UNIQUE REFERENCES events(id),
        CHECK(amount_cents = reserve_cents + stocks_cents + crypto_cents + fun_cents + wager_cents)
    );
    CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """)
    # Upgrade v0.1 ledgers in-place without rewriting historical allocation amounts.
    # Existing three-way commitments become five-way commitments with 0 fun/wager.
    commit_columns = {r['name'] for r in cx.execute('PRAGMA table_info(allocation_commits)')}
    if 'fun_cents' not in commit_columns:
        cx.executescript("""
        BEGIN;
        ALTER TABLE allocation_commits RENAME TO allocation_commits_old;
        CREATE TABLE allocation_commits (
            id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
            account TEXT NOT NULL REFERENCES accounts(id),
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            reserve_cents INTEGER NOT NULL CHECK(reserve_cents >= 0),
            stocks_cents INTEGER NOT NULL CHECK(stocks_cents >= 0),
            crypto_cents INTEGER NOT NULL CHECK(crypto_cents >= 0),
            fun_cents INTEGER NOT NULL CHECK(fun_cents >= 0),
            wager_cents INTEGER NOT NULL CHECK(wager_cents >= 0),
            source_event INTEGER NOT NULL UNIQUE REFERENCES events(id),
            CHECK(amount_cents = reserve_cents + stocks_cents + crypto_cents + fun_cents + wager_cents)
        );
        INSERT INTO allocation_commits
          (id,at,account,amount_cents,reserve_cents,stocks_cents,crypto_cents,fun_cents,wager_cents,source_event)
        SELECT id,at,account,amount_cents,reserve_cents,stocks_cents,crypto_cents,0,0,source_event
          FROM allocation_commits_old;
        DROP TABLE allocation_commits_old;
        COMMIT;
        """)
    buffer_schema = cx.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='buffer_actions'").fetchone()['sql']
    if "'shares'" not in buffer_schema:
        cx.executescript("""
        BEGIN;
        ALTER TABLE buffer_actions RENAME TO buffer_actions_old;
        CREATE TABLE buffer_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            at TEXT NOT NULL,
            account TEXT NOT NULL REFERENCES accounts(id),
            purpose TEXT NOT NULL CHECK(purpose IN ('betting','investing','reserve','fun','shares','crypto')),
            action TEXT NOT NULL CHECK(action IN ('hold','release')),
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            memo TEXT NOT NULL DEFAULT ''
        );
        INSERT INTO buffer_actions(id,at,account,purpose,action,amount_cents,memo)
        SELECT id,at,account,purpose,action,amount_cents,memo FROM buffer_actions_old;
        DROP TABLE buffer_actions_old;
        COMMIT;
        """)
    # An untouched v0.1 rule gets the new share-focused default.
    old_weights = dict(cx.execute("SELECT key,value FROM settings WHERE key IN ('weight_reserve','weight_stocks','weight_crypto')").fetchall())
    already_five = cx.execute("SELECT 1 FROM settings WHERE key='weight_fun'").fetchone() is not None
    if not already_five:
        if not old_weights or old_weights == {'weight_reserve':'50','weight_stocks':'30','weight_crypto':'20'}:
            new_weights = {'weight_reserve':'20','weight_stocks':'50','weight_crypto':'15','weight_fun':'10','weight_wager':'5'}
        else:
            # Respect customized v0.1 percentages until user edits new categories.
            new_weights = {'weight_fun':'0','weight_wager':'0'}
        for key, value in new_weights.items():
            cx.execute('REPLACE INTO settings(key,value) VALUES (?,?)',(key,value))
    for row in SEED:
        cx.execute("INSERT OR IGNORE INTO accounts(id,name,kind,country,currency,status,verified) VALUES (?,?,?,?,?,?,?)", row)
    for key, value in [
        ("weight_reserve", "20"), ("weight_stocks", "50"), ("weight_crypto", "15"),
        ("weight_fun", "10"), ("weight_wager", "5"),
        ("cash_floor", "0"), ("pool_source", "ca_paypal"), ("auto_earmark", "1")
    ]:
        cx.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))
    cx.commit()
    return cx


def rows(cx, sql, args=()):
    return [dict(x) for x in cx.execute(sql, args)]


def account(cx, acc_id):
    row = cx.execute("SELECT * FROM accounts WHERE id=?", (acc_id,)).fetchone()
    if not row:
        raise ValueError(f"Unknown account: {acc_id}")
    return dict(row)


def add_account(cx, data):
    name = str(data.get("name", "")).strip()[:100]
    kind, country, currency = data.get("kind"), data.get("country"), data.get("currency")
    status = data.get("status", "active")
    if not name or kind not in ACCOUNT_KINDS or country not in COUNTRIES or currency not in CURRENCIES:
        raise ValueError("Valid account name, category, country and currency required")
    if status not in {"active", "planned", "archived"}:
        raise ValueError("Invalid status")
    ident = "u_" + uuid.uuid4().hex[:12]
    with cx:
        cx.execute("INSERT INTO accounts VALUES (?,?,?,?,?,?,?,?)", (ident, name, kind, country, currency, status, "unverified", 0))
    return ident


def balances(cx):
    data = {a['id']: a['opening_cents'] for a in rows(cx, 'SELECT * FROM accounts')}
    for r in rows(cx, "SELECT source,target,source_cents,target_cents FROM events"):
        if r['source']:
            data[r['source']] -= r['source_cents']
        if r['target']:
            data[r['target']] += r['target_cents']
    for b in rows(cx, "SELECT account,stake_cents,payout_cents FROM bets"):
        data[b['account']] -= b['stake_cents']
        if b['payout_cents'] is not None:
            data[b['account']] += b['payout_cents']
    return data


def buffer_totals(cx):
    """Virtual earmarks only: never moves or creates cash in the underlying account."""
    totals = {}
    for r in rows(cx, """SELECT account,purpose,
              SUM(CASE WHEN action='hold' THEN amount_cents ELSE -amount_cents END) AS held
              FROM buffer_actions GROUP BY account,purpose"""):
        totals[(r['account'], r['purpose'])] = r['held']
    return totals


def buffer_held(cx, account_id):
    return sum(n for (a, _), n in buffer_totals(cx).items() if a == account_id)


def buffer_action(cx, d):
    account_id = d.get('account')
    a = account(cx, account_id)
    if a['kind'] not in {'bank', 'wallet'} or a['status'] != 'active':
        raise ValueError('Buffer needs an active bank or wallet account')
    purpose, action = d.get('purpose'), d.get('action')
    if purpose not in BUFFER_PURPOSES or action not in BUFFER_ACTIONS:
        raise ValueError('Invalid buffer purpose or action')
    amount = cents(d.get('amount'))
    if amount <= 0:
        raise ValueError('Amount must be positive')
    with cx:
        # State change is ledger-only. No PayPal, bank, sportsbook or crypto API call.
        if action == 'hold':
            available = balances(cx)[account_id] - buffer_held(cx, account_id)
            if amount > available:
                raise ValueError('Insufficient unheld balance for buffer')
        else:
            held = buffer_totals(cx).get((account_id, purpose), 0)
            if amount > held:
                raise ValueError('Cannot release more than the buffer holds')
        cx.execute("""INSERT INTO buffer_actions(at,account,purpose,action,amount_cents,memo)
                      VALUES (?,?,?,?,?,?)""", (now(), account_id, purpose, action, amount,
                                                   str(d.get('memo',''))[:300]))


def set_play_rule(cx, d):
    """A self-declared ceiling, not a real betting-site deposit limit."""
    a = account(cx, d.get('account'))
    if a['kind'] != 'sportsbook' or a['status'] != 'active':
        raise ValueError('Choose an active sportsbook')
    ceiling = cents(d.get('ceiling'))
    if ceiling <= 0:
        raise ValueError('Play balance ceiling must be greater than zero')
    enabled = 1 if str(d.get('enabled', '1')).lower() in ('1', 'true', 'on') else 0
    with cx:
        cx.execute("""INSERT INTO play_rules(account,ceiling_cents,enabled) VALUES(?,?,?)
              ON CONFLICT(account) DO UPDATE SET ceiling_cents=excluded.ceiling_cents,
              enabled=excluded.enabled""", (a['id'], ceiling, enabled))


def net_betting_profit(cx, sportsbook_id):
    return cx.execute("""SELECT COALESCE(SUM(payout_cents - stake_cents),0)
            FROM bets WHERE account=? AND payout_cents IS NOT NULL""",
            (sportsbook_id,)).fetchone()[0]


def recorded_sweeps(cx, sportsbook_id):
    return cx.execute("""SELECT COALESCE(SUM(source_cents),0) FROM events
            WHERE kind='profit_sweep' AND source=?""", (sportsbook_id,)).fetchone()[0]


def sweep_candidate(cx, sportsbook_id):
    """Never sweeps wage deposits or counts previously swept profits twice."""
    rule = cx.execute("SELECT * FROM play_rules WHERE account=?", (sportsbook_id,)).fetchone()
    if not rule or not rule['enabled']:
        return 0
    bal = balances(cx)[sportsbook_id]
    above_ceiling = max(0, bal - rule['ceiling_cents'])
    realized_unswept_profit = max(0, net_betting_profit(cx, sportsbook_id)
                                     - recorded_sweeps(cx, sportsbook_id))
    return min(above_ceiling, realized_unswept_profit)


def _split_allocations(total, settings):
    """Preserve cents and zero weights; send rounding remainder to largest bucket."""
    keys = ('stocks', 'crypto', 'reserve', 'fun', 'wager')
    weights = {key: int(settings[f'weight_{key}']) for key in keys}
    allocation = {key: total * weights[key] // 100 for key in keys}
    anchor = max(keys, key=lambda key: weights[key])  # shares win equal-weight ties
    allocation[anchor] += total - sum(allocation.values())
    return allocation


def add_event(cx, d):
    kind = d.get('kind')
    if kind not in EVENT_KINDS:
        raise ValueError('Invalid transaction kind')
    src = d.get('source') or None
    dst = d.get('target') or None
    if src and src == dst:
        raise ValueError('Source and destination must differ')
    a = account(cx, src) if src else None
    b = account(cx, dst) if dst else None
    val = cents(d.get('amount'))
    if val <= 0:
        raise ValueError('Amount must be greater than zero')
    val_dst = cents(d.get('target_amount', d.get('amount')))
    if kind == 'cash_in' and (a or not b):
        raise ValueError('Cash in needs destination only')
    if kind in {'cash_out', 'fee'} and (not a or b):
        raise ValueError('Cash out/fee needs source only')
    if kind in {'transfer', 'fx_transfer', 'profit_sweep'} and (not a or not b):
        raise ValueError('Transfer needs both accounts')
    if kind in {'transfer','profit_sweep'} and (a['currency'] != b['currency'] or val != val_dst):
        raise ValueError('Same-currency transfer must have equal amounts')
    if kind == 'fx_transfer' and (a['currency'] == b['currency'] or val_dst <= 0):
        raise ValueError('FX transfer needs different currencies and explicit received amount')
    if kind == 'fx_transfer' and 'target_amount' not in d:
        raise ValueError('Explicit received amount required for FX transfer')
    if kind == 'profit_sweep':
        if a['kind'] != 'sportsbook' or b['kind'] not in {'wallet', 'bank'}:
            raise ValueError('Profit sweep must go from sportsbook to bank/wallet')
        if val > sweep_candidate(cx, a['id']):
            raise ValueError('Sweep exceeds settled unswept profit above the play ceiling')
    if a and balances(cx)[a['id']] - buffer_held(cx, a['id']) < val:
        raise ValueError('Insufficient unheld source balance; release a buffer first or reconcile')
    ev = d.get('evidence', 'user_recorded')
    if ev not in EVIDENCE:
        raise ValueError('Invalid evidence flag')
    memo = str(d.get('memo', ''))[:300]
    ref = str(d['reference']).strip()[:100] if d.get('reference') else None
    with cx:
        cur = cx.execute("""INSERT INTO events(at,kind,source,target,source_cents,target_cents,
            source_currency,target_currency,evidence,reference,memo) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (now(), kind, src, dst, val if src else 0,
             val_dst if dst else 0, a['currency'] if a else None,
             b['currency'] if b else None, ev, ref, memo))
        if kind == 'profit_sweep':
            settings = dict(cx.execute('SELECT key,value FROM settings').fetchall())
            if settings.get('auto_earmark') == '1' and dst == settings['pool_source']:
                # Apply the cash floor to this newly confirmed transfer. No real
                # shares/crypto are purchased; only virtual earmarks are created.
                free_cash = balances(cx)[dst] - buffer_held(cx, dst)
                floor = cents(settings['cash_floor'])
                already_allocated = cx.execute("""SELECT COALESCE(SUM(amount_cents),0)
                       FROM allocation_commits WHERE account=?""", (dst,)).fetchone()[0]
                total_sweeps = cx.execute("""SELECT COALESCE(SUM(target_cents),0)
                       FROM events WHERE kind='profit_sweep' AND target=?""", (dst,)).fetchone()[0]
                cap = min(val, max(0, free_cash - floor), max(0, total_sweeps-already_allocated))
                if cap:
                    alloc = _split_allocations(cap, settings)
                    cx.execute("""INSERT INTO allocation_commits
                       (at,account,amount_cents,reserve_cents,stocks_cents,crypto_cents,fun_cents,wager_cents,source_event)
                       VALUES(?,?,?,?,?,?,?,?,?)""", (now(),dst,cap,alloc['reserve'],
                           alloc['stocks'],alloc['crypto'],alloc['fun'],alloc['wager'],cur.lastrowid))
                    for purpose, amt in [
                        ('reserve', alloc['reserve']),
                        ('shares', alloc['stocks']),
                        ('crypto', alloc['crypto']),
                        ('fun', alloc['fun']),
                        ('betting', alloc['wager'])
                    ]:
                        if amt:
                            cx.execute("""INSERT INTO buffer_actions
                               (at,account,purpose,action,amount_cents,memo)
                               VALUES(?,?,?,?,?,?)""",
                               (now(),dst,purpose,'hold',amt,'Auto earmark from profit sweep #'+str(cur.lastrowid)))


def add_bet(cx, d):
    a = account(cx, d.get('account'))
    if a['kind'] != 'sportsbook':
        raise ValueError('Wager must be on a sportsbook ledger account')
    if a['status'] != 'active':
        raise ValueError('Account is not active')
    stake = cents(d.get('stake'))
    if stake <= 0:
        raise ValueError('Stake must be positive')
    if balances(cx)[a['id']] < stake:
        raise ValueError('Insufficient recorded sportsbook balance')
    category = str(d.get('category','')).strip()[:50]
    if not category:
        raise ValueError('Category required')
    evidence = d.get('evidence', 'user_recorded')
    if evidence not in EVIDENCE:
        raise ValueError('Invalid evidence')
    ref = str(d.get('reference','')).strip()[:100] or None
    with cx:
        cur = cx.execute("""INSERT INTO bets(account,category,stake_cents,payout_cents,placed_at,
            settled_at,reference,memo,evidence) VALUES (?,?,?,?,?,?,?,?,?)""",
            (a['id'],category,stake,None,now(),None,ref,str(d.get('memo',''))[:300],evidence))
    return cur.lastrowid


def settle_bet(cx, bet_id, payout, evidence='user_recorded'):
    r = cx.execute("SELECT * FROM bets WHERE id=?", (bet_id,)).fetchone()
    if not r:
        raise ValueError('Unknown bet')
    if r['payout_cents'] is not None:
        raise ValueError('Bet is already settled')
    if evidence not in EVIDENCE:
        raise ValueError('Invalid evidence')
    val = cents(payout)
    with cx:
        cx.execute("UPDATE bets SET payout_cents=?,settled_at=?,evidence=? WHERE id=?",(val, now(),evidence,bet_id))


def add_position(cx, d):
    a = account(cx, d.get('account'))
    if a['kind'] not in {'crypto','broker','skins'}:
        raise ValueError('Positions need crypto, brokerage or skins account')
    symbol = str(d.get('symbol','')).strip().upper()[:36]
    asset_type = str(d.get('asset_type','')).strip()[:40]
    curr = d.get('quote_currency')
    if not symbol or not asset_type or curr not in CURRENCIES:
        raise ValueError('Symbol, asset type and quote currency required')
    try:
        quantity = Decimal(str(d.get('quantity')))
        price = Decimal(str(d.get('unit_price')))
        if not all(x.is_finite() and x >= 0 for x in (quantity, price)):
            raise ValueError('Quantity and price must be nonnegative and finite')
        if quantity > Decimal('1e15') or price > Decimal('1e15'):
            raise ValueError('Too large')
    except (InvalidOperation, TypeError) as e:
        raise ValueError('Invalid quantity or price') from e
    with cx:
        cx.execute("""INSERT INTO positions(account,symbol,asset_type,quantity,unit_price,quote_currency,observed_at)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(account,symbol) DO UPDATE SET
            asset_type=excluded.asset_type,quantity=excluded.quantity,unit_price=excluded.unit_price,
            quote_currency=excluded.quote_currency,observed_at=excluded.observed_at,source='manual'""",
            (a['id'],symbol,asset_type,str(quantity),str(price),curr,now()))


def update_settings(cx, d):
    values = [int(d.get(f'weight_{k}',-1)) for k in ('stocks','crypto','reserve','fun','wager')]
    if min(values) < 0 or max(values) > 100 or sum(values) != 100:
        raise ValueError('Weights must be 0-100 and total 100%')
    floor = cents(d.get('cash_floor', '0'))
    a = account(cx,d.get('pool_source'))
    if a['kind'] not in {'wallet','bank'} or a['status'] != 'active':
        raise ValueError('Choose an active bank or wallet for the pool')
    for k, v in zip(('weight_stocks','weight_crypto','weight_reserve','weight_fun','weight_wager'), values):
        cx.execute('REPLACE INTO settings VALUES (?,?)',(k,str(v)))
    cx.execute('REPLACE INTO settings VALUES (?,?)',('cash_floor',money(floor)))
    cx.execute('REPLACE INTO settings VALUES (?,?)',('pool_source',a['id']))
    auto = str(d.get('auto_earmark', '1')).lower() in ('1','true','on')
    cx.execute('REPLACE INTO settings VALUES (?,?)',('auto_earmark','1' if auto else '0'))
    cx.commit()


def dashboard(cx):
    accounts = rows(cx,'SELECT * FROM accounts ORDER BY country,name')
    b = balances(cx)
    holds = buffer_totals(cx)
    for a in accounts:
        a['balance'] = money(b[a['id']])
        held = sum(n for (acct, _), n in holds.items() if acct == a['id'])
        a['held'] = money(held)
        a['available'] = money(b[a['id']]-held)
    evs = rows(cx, 'SELECT * FROM events ORDER BY id DESC LIMIT 150')
    for e in evs:
        e['source_amount'] = money(e['source_cents'])
        e['target_amount'] = money(e['target_cents'])
    bets = rows(cx,'SELECT * FROM bets ORDER BY id DESC LIMIT 150')
    pnl = {c: 0 for c in CURRENCIES}
    open_risk = {c: 0 for c in CURRENCIES}
    for x in bets:
        a = account(cx, x['account'])
        curr = a['currency']
        x['currency'] = curr
        x['stake'] = money(x['stake_cents'])
        x['payout'] = money(x['payout_cents']) if x['payout_cents'] is not None else None
        x['pnl'] = money(x['payout_cents'] - x['stake_cents']) if x['payout_cents'] is not None else None
        if x['payout_cents'] is None:
            open_risk[curr] += x['stake_cents']
        else:
            pnl[curr] += x['payout_cents'] - x['stake_cents']
    positions = rows(cx, 'SELECT * FROM positions ORDER BY account,symbol')
    for p in positions:
        p['market_value'] = str((Decimal(p['quantity']) * Decimal(p['unit_price'])).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP))
    settings = dict(cx.execute('SELECT key,value FROM settings').fetchall())
    source = account(cx, settings['pool_source'])
    floor = cents(settings['cash_floor'])
    # Only manually confirmed, explicitly marked profit sweeps are eligible.
    # Generic deposits, FX movements and historical unswept bets cannot fund the pool.
    available_cash = b[source['id']] - buffer_held(cx, source['id'])
    total_sweeps = cx.execute("""SELECT COALESCE(SUM(target_cents),0) FROM events
                     WHERE kind='profit_sweep' AND target=?""", (source['id'],)).fetchone()[0]
    committed = cx.execute("""SELECT COALESCE(SUM(amount_cents),0) FROM allocation_commits
                     WHERE account=?""", (source['id'],)).fetchone()[0]
    eligible = min(max(0, available_cash-floor), max(0, total_sweeps-committed))
    allocation = _split_allocations(eligible, settings)
    rules = []
    for r in rows(cx, 'SELECT * FROM play_rules ORDER BY account'):
        ac = account(cx, r['account'])
        bal = b[r['account']]
        pnl_site = net_betting_profit(cx, r['account'])
        swept = recorded_sweeps(cx, r['account'])
        rules.append({'account':ac['id'], 'currency':ac['currency'],
                      'enabled':bool(r['enabled']), 'ceiling':money(r['ceiling_cents']),
                      'balance':money(bal), 'settled_net_pnl':money(pnl_site),
                      'already_swept':money(swept),
                      'suggested_sweep':money(sweep_candidate(cx, r['account']))})
    committed_rows = rows(cx, 'SELECT * FROM allocation_commits ORDER BY id DESC LIMIT 150')
    for r in committed_rows:
        for key in ('amount','reserve','stocks','crypto','fun','wager'):
            r[key] = money(r[key+'_cents'])
    result = {
        'accounts':accounts, 'events':evs, 'bets':bets, 'positions':positions,
        'buffer_actions': [dict(r, amount=money(r['amount_cents'])) for r in
            rows(cx, 'SELECT * FROM buffer_actions ORDER BY id DESC LIMIT 150')],
        'play_rules': rules, 'allocation_commits': committed_rows,
        'buffers': [dict(account=a, purpose=p, held=money(n)) for (a,p),n in sorted(holds.items()) if n > 0],
        'settings':settings, 'pnl':{k:money(v) for k,v in sorted(pnl.items())},
        'open_risk':{k:money(v) for k,v in sorted(open_risk.items())},
        'pool':{'source':source['id'], 'currency':source['currency'],
                'balance':money(b[source['id']]), 'buffer_held':money(buffer_held(cx, source['id'])),
                'available':money(available_cash), 'protected_floor':money(floor),
                'confirmed_profit_sweeps':money(total_sweeps),
                'already_earmarked':money(committed),
                'proposed_max':money(eligible),
                'allocations':{k:money(v) for k,v in allocation.items()},
                'warning':'Only recorded profit sweeps qualify. Five destinations are virtual holds: not share/crypto buys, cash payouts, or automated wagers. No funds move outside this app.'},
        'notice':'Unverified providers and manual holdings are not independently authenticated. No live prices or FX feeds.'
    }
    return result


def seed_demo(cx):
    if cx.execute('SELECT COUNT(*) FROM events').fetchone()[0]:
        return
    add_event(cx, {'kind':'cash_in','target':'ca_bank','amount':'500','memo':'Illustrative opening transfer (demo)'})
    add_event(cx, {'kind':'transfer','source':'ca_bank','target':'ca_sports','amount':'100'})
    add_bet(cx, {'account':'ca_sports','category':'Basketball', 'stake':'20','memo':'Sample only'})
    settle_bet(cx, 1, '35')
    set_play_rule(cx, {'account':'ca_sports','ceiling':'100','enabled':'1'})
    add_event(cx, {'kind':'profit_sweep','source':'ca_sports','target':'ca_paypal','amount':'15', 'memo':'Fictional demo profit sweep'})
    buffer_action(cx, {'account':'ca_bank','action':'hold','purpose':'reserve','amount':'50','memo':'Demo protected cash'})
    buffer_action(cx, {'account':'ca_bank','action':'hold','purpose':'betting','amount':'25','memo':'Demo optional betting allowance'})
    add_position(cx, {'account':'nz_crypto','symbol':'BTC','asset_type':'crypto','quantity':'0.002', 'unit_price':'100000','quote_currency':'NZD'})
