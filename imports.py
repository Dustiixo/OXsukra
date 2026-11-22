"""OX Treasury v0.3 - local CSV statement intake, review and reconciliation.

No credentials, provider APIs, wagers, trades or actual transfers. CSV is untrusted
user-supplied data, not independent verification of a provider or its balances.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import re
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import core

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000
MAX_COLUMNS = 60
MAX_FIELD = 1024
PROFILES = {
    'cash': ('amount',),
    'bets': ('stake',),
    'holdings': ('symbol', 'quantity', 'unit_price'),
}
FIELDS = {
    'cash': ('date', 'reference', 'description', 'amount', 'currency', 'status'),
    'bets': ('reference', 'date', 'settled_at', 'category', 'stake', 'payout', 'status', 'currency'),
    'holdings': ('reference', 'date', 'symbol', 'asset_type', 'quantity', 'unit_price', 'currency'),
}
ALIASES = {
    'date': ('date', 'transaction date', 'transaction_date', 'timestamp', 'time', 'activity date', 'created at', 'placed at', 'trade date', 'as of', 'observed at'),
    'settled_at': ('settled at', 'settlement date', 'date settled', 'resolved at'),
    'reference': ('transaction id', 'transaction_id', 'reference', 'reference id', 'bet id', 'order id', 'id', 'txid', 'hash', 'activity id'),
    'description': ('description', 'details', 'memo', 'note', 'type', 'transaction type'),
    'amount': ('net amount', 'net', 'amount', 'signed amount', 'change'),
    'currency': ('currency', 'currency code', 'ccy', 'quote currency', 'price currency', 'fiat currency'),
    'status': ('status', 'state', 'result', 'outcome'),
    'category': ('category', 'sport', 'market', 'event', 'bet type', 'type'),
    'stake': ('stake', 'wager', 'bet amount', 'risk', 'amount wagered'),
    'payout': ('payout', 'return', 'gross payout', 'total return', 'winnings', 'settlement amount'),
    'symbol': ('symbol', 'ticker', 'asset', 'coin', 'instrument', 'asset symbol'),
    'asset_type': ('asset type', 'asset_type', 'security type', 'class'),
    'quantity': ('quantity', 'qty', 'units', 'balance', 'holdings'),
    'unit_price': ('unit price', 'market price', 'price', 'price per unit', 'last price', 'quote'),
}
BLOCKED_STATUS = {'pending', 'processing', 'on hold', 'held', 'failed', 'cancelled', 'canceled', 'reversed', 'void', 'declined', 'rejected'}
OPEN_BET_STATUS = {'open', 'pending', 'unsettled', 'active', 'in progress', 'void', 'cancelled', 'canceled'}


def ensure_schema(cx):
    cx.executescript('''
    CREATE TABLE IF NOT EXISTS import_batches (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       imported_at TEXT NOT NULL,
       account TEXT NOT NULL REFERENCES accounts(id),
       profile TEXT NOT NULL,
       filename TEXT NOT NULL,
       file_sha256 TEXT NOT NULL,
       mapping_json TEXT NOT NULL,
       total_rows INTEGER NOT NULL,
       new_rows INTEGER NOT NULL,
       duplicate_rows INTEGER NOT NULL,
       rejected_rows INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS import_records (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       batch_id INTEGER NOT NULL REFERENCES import_batches(id),
       account TEXT NOT NULL REFERENCES accounts(id),
       profile TEXT NOT NULL,
       external_key TEXT NOT NULL,
       digest TEXT NOT NULL,
       data_json TEXT NOT NULL,
       review_state TEXT NOT NULL DEFAULT 'staged',
       ledger_type TEXT,
       ledger_id INTEGER,
       reviewed_at TEXT,
       UNIQUE(account,profile,external_key)
    );
    CREATE TABLE IF NOT EXISTS import_issues (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       batch_id INTEGER NOT NULL REFERENCES import_batches(id),
       csv_row INTEGER NOT NULL,
       severity TEXT NOT NULL,
       message TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_import_records_batch ON import_records(batch_id);
    CREATE INDEX IF NOT EXISTS idx_import_records_account ON import_records(account,review_state);
    ''')
    cx.commit()


def load_csv(text):
    if not isinstance(text, str):
        raise ValueError('CSV data must be text')
    if '\x00' in text or len(text.encode('utf-8')) > MAX_BYTES:
        raise ValueError('CSV must be UTF-8 and no larger than 2 MB')
    try:
        raw = list(csv.reader(io.StringIO(text.lstrip('\ufeff'), newline=''), strict=True))
    except csv.Error as exc:
        raise ValueError('Malformed CSV: ' + str(exc)) from exc
    if not raw or not raw[0] or len(raw[0]) > MAX_COLUMNS:
        raise ValueError('CSV needs a header with at most 60 columns')
    if len(raw) - 1 > MAX_ROWS:
        raise ValueError('CSV has more than 5,000 data rows; split the export')
    headers = [h.strip().lstrip('\ufeff') for h in raw[0]]
    if not all(headers) or len(set(headers)) != len(headers):
        raise ValueError('CSV headers must be nonblank and unique')
    result = []
    for row_index, line in enumerate(raw[1:], start=2):
        if not any(cell.strip() for cell in line):
            continue
        if len(line) != len(headers):
            raise ValueError(f'CSV row {row_index} has {len(line)} cells; expected {len(headers)}')
        if any(len(cell) > MAX_FIELD for cell in line):
            raise ValueError(f'CSV row {row_index} has a cell exceeding 1,024 characters')
        result.append((row_index, dict(zip(headers, line))))
    return headers, result


def suggest_mapping(headers, profile):
    if profile not in PROFILES:
        raise ValueError('Unknown import profile')
    normalized = {re.sub(r'[^a-z0-9]', '', h.lower()): h for h in headers}
    choices = {}
    for field in FIELDS[profile]:
        for alias in ALIASES[field]:
            key = re.sub(r'[^a-z0-9]', '', alias.lower())
            if key in normalized:
                choices[field] = normalized[key]
                break
    return choices


def preview(csv_text, profile):
    headers, lines = load_csv(csv_text)
    if profile not in PROFILES:
        raise ValueError('Invalid import profile')
    return {'headers': headers, 'mapping': suggest_mapping(headers, profile),
            'fields': FIELDS[profile], 'required': PROFILES[profile],
            'sample': [v for _, v in lines[:3]], 'rows': len(lines),
            'warning': 'Generic CSV format, not a verified provider integration. Review column mapping and use signed NET movements for cash.'}


def amount(value, signed=False):
    s = str(value).strip()
    if not s:
        raise ValueError('Missing amount')
    # Recognize simple US-style numeric exports. Never guess EU decimal conventions.
    neg = s.startswith('(') and s.endswith(')')
    if neg:
        s = s[1:-1].strip()
    s = re.sub(r'^(?:CAD|AUD|NZD|USD|\$)\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s*(?:CAD|AUD|NZD|USD)$', '', s, flags=re.IGNORECASE).strip()
    if not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,8})?', s):
        raise ValueError('Expected decimal number using a dot, optional thousands commas')
    try:
        d = Decimal(s.replace(',', ''))
        if neg:
            d = -d
        if not signed and d < 0:
            raise ValueError('Amount cannot be negative')
        if not d.is_finite() or abs(d) > Decimal('10000000000000'):
            raise ValueError('Amount outside supported range')
        return d
    except InvalidOperation as exc:
        raise ValueError('Invalid decimal amount') from exc


def minor(d):
    return int((d * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def normalized(row, mapping, profile, currency):
    fields = FIELDS[profile]
    data = {field: str(row.get(mapping.get(field, ''), '')).strip() for field in fields}
    quoted = data.get('currency', '').upper() or currency
    if quoted not in core.CURRENCIES:
        raise ValueError('Unsupported or missing currency')
    data['currency'] = quoted
    data['reference'] = data.get('reference', '')[:200]
    data['date'] = data.get('date', '')[:80]
    if 'settled_at' in data: data['settled_at'] = data['settled_at'][:80]
    if profile == 'cash':
        data['amount_cents'] = minor(amount(data['amount'], signed=True))
        if data['amount_cents'] == 0:
            raise ValueError('Zero signed movement is not a transaction')
        data['description'] = data.get('description', '')[:250]
        data['status'] = data.get('status', '').lower()[:50]
    elif profile == 'bets':
        data['stake_cents'] = minor(amount(data['stake']))
        if data['stake_cents'] <= 0:
            raise ValueError('Stake must be positive')
        data['payout_cents'] = None if not data['payout'] else minor(amount(data['payout']))
        data['status'] = data.get('status', '').lower()[:50]
        if data['status'] in {'won', 'lost', 'settled', 'complete', 'completed', 'paid', 'cashed out'} and data['payout_cents'] is None:
            raise ValueError('Settled bet is missing a payout amount (use 0 for a loss)')
        data['category'] = data.get('category', '')[:60] or 'Other'
    else:
        symbol = data['symbol'].upper()[:36]
        if not re.fullmatch(r'[A-Z0-9._:/\-]{1,36}', symbol):
            raise ValueError('Asset symbol contains unsupported characters')
        data['symbol'] = symbol
        qty = amount(data['quantity'])
        price = amount(data['unit_price'])
        if qty > Decimal('1000000000000000') or price > Decimal('1000000000000000'):
            raise ValueError('Position too large')
        data['quantity'] = str(qty)
        data['unit_price'] = str(price)
        data['asset_type'] = data.get('asset_type', '')[:40] or 'unspecified'
    return data


def stage(cx, payload):
    ensure_schema(cx)
    a = core.account(cx, payload.get('account'))
    profile = payload.get('profile')
    if profile not in PROFILES:
        raise ValueError('Invalid profile')
    if profile == 'bets' and a['kind'] != 'sportsbook':
        raise ValueError('Bet exports require sportsbook account')
    if profile == 'holdings' and a['kind'] not in {'crypto', 'broker', 'skins'}:
        raise ValueError('Holdings exports require crypto, broker or skins account')
    filename = str(payload.get('filename', 'statement.csv')).replace('\\', '/').split('/')[-1][:120]
    csv_text = payload.get('csv_text')
    headers, lines = load_csv(csv_text)
    mapping = payload.get('mapping')
    if not isinstance(mapping, dict):
        raise ValueError('Choose a column mapping')
    for key, column in mapping.items():
        if key not in FIELDS[profile] or (column and column not in headers):
            raise ValueError('Mapping includes unknown field or CSV column')
    for field in PROFILES[profile]:
        if not mapping.get(field):
            raise ValueError('Map required column: ' + field)
    sha = hashlib.sha256(csv_text.encode('utf-8')).hexdigest()
    new_count, dupe_count, rejected_count = 0, 0, 0
    with cx:
        c = cx.execute('''INSERT INTO import_batches
           (imported_at,account,profile,filename,file_sha256,mapping_json,total_rows,new_rows,duplicate_rows,rejected_rows)
           VALUES(?,?,?,?,?,?,?,?,?,?)''', (core.now(),a['id'],profile,filename,sha,json.dumps(mapping),len(lines),0,0,0))
        bid = c.lastrowid
        for row_number, row in lines:
            try:
                data = normalized(row, mapping, profile, a['currency'])
                if data['currency'] != a['currency'] and profile != 'holdings':
                    raise ValueError(f'Row currency {data["currency"]} differs from account {a["currency"]}; use correct account/currency')
                digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                explicit_ref = data.get('reference', '').strip()
                if explicit_ref and profile == 'holdings':
                    ext_key = 'asset-ref:' + hashlib.sha256((explicit_ref+'|'+data['symbol']+'|'+data.get('date','')).encode()).hexdigest()
                elif explicit_ref:
                    ext_key = 'ref:' + hashlib.sha256(explicit_ref.encode()).hexdigest()
                elif profile == 'holdings' and data.get('date'):
                    ext_key = 'snapshot:' + hashlib.sha256((data['symbol']+'|'+data['date']+'|'+digest).encode()).hexdigest()
                else:
                    # Without stable external IDs, never collapse two identical
                    # transactions within the SAME statement. Re-importing exactly
                    # the same file skips duplicates, but overlapping DIFFERENT files
                    # require manual reconciliation.
                    ext_key = 'file-row:' + sha[:24]+':'+str(row_number)+':'+digest[:24]
                if not explicit_ref and profile != 'holdings':
                    cx.execute('INSERT INTO import_issues(batch_id,csv_row,severity,message) VALUES(?,?,?,?)',
                               (bid,row_number,'warning','No external ID: dedupe only within identical re-imports; inspect overlapping statements'))
                old = cx.execute('SELECT digest FROM import_records WHERE account=? AND profile=? AND external_key=?',
                                 (a['id'],profile,ext_key)).fetchone()
                if old and old['digest'] != digest and profile == 'bets' and explicit_ref:
                    # Sportsbooks may re-export an open bet after it settles.
                    # Preserve both statements; the review path must link to the same bet.
                    ext_key += ':revision:' + digest[:24]
                    old = cx.execute('SELECT digest FROM import_records WHERE account=? AND profile=? AND external_key=?',
                                     (a['id'],profile,ext_key)).fetchone()
                if old:
                    dupe_count += 1
                    if old['digest'] != digest:
                        cx.execute('INSERT INTO import_issues(batch_id,csv_row,severity,message) VALUES(?,?,?,?)',
                                   (bid,row_number,'conflict','Same external ID has different values; existing cash/holding record preserved'))
                    continue
                cx.execute('''INSERT INTO import_records
                   (batch_id,account,profile,external_key,digest,data_json)
                   VALUES(?,?,?,?,?,?)''', (bid,a['id'],profile,ext_key,digest,json.dumps(data,sort_keys=True)))
                new_count += 1
            except (ValueError, KeyError) as exc:
                rejected_count += 1
                cx.execute('INSERT INTO import_issues(batch_id,csv_row,severity,message) VALUES(?,?,?,?)',
                           (bid,row_number,'rejected',str(exc)[:250]))
        cx.execute('UPDATE import_batches SET new_rows=?,duplicate_rows=?,rejected_rows=? WHERE id=?',
                   (new_count,dupe_count,rejected_count,bid))
    return {'batch_id':bid,'total_rows':len(lines),'new_rows':new_count,
            'duplicate_rows':dupe_count,'rejected_rows':rejected_count,
            'message':'Staged locally. No account balances, bets or holdings changed; review each row.'}


def _entry(cx, rec_id):
    record = cx.execute('SELECT * FROM import_records WHERE id=?',(rec_id,)).fetchone()
    if not record:
        raise ValueError('Unknown imported row')
    return record, json.loads(record['data_json'])


def parse_utc_date(raw):
    """Parse unambiguous ISO timestamps only; never guess day/month order."""
    if not raw:
        return None
    try:
        v = dt.datetime.fromisoformat(str(raw).replace('Z','+00:00'))
        if v.tzinfo is None:
            v = v.replace(tzinfo=dt.timezone.utc)
        return v.astimezone(dt.timezone.utc).isoformat(timespec='seconds')
    except (TypeError, ValueError):
        return None


def review(cx, record_id, action):
    ensure_schema(cx)
    record, data = _entry(cx, record_id)
    if record['review_state'] in {'applied','matched'}:
        raise ValueError('This imported row is already linked to a ledger entry')
    if action == 'ignore':
        with cx:
            cx.execute('UPDATE import_records SET review_state=?,reviewed_at=? WHERE id=?', ('ignored',core.now(),record_id))
        return {'state':'ignored'}
    if action == 'restore':
        with cx:
            cx.execute('UPDATE import_records SET review_state=?,reviewed_at=? WHERE id=?', ('staged',core.now(),record_id))
        return {'state':'staged'}
    a = core.account(cx, record['account'])
    state = data.get('status','').lower().strip()
    if state in BLOCKED_STATUS and record['profile'] != 'bets':
        raise ValueError('Pending/failed/reversed statement rows cannot be posted to the ledger')
    if action == 'match':
        ref = data.get('reference','')
        if not ref:
            raise ValueError('Match requires an explicit external reference ID')
        if record['profile'] == 'cash':
            matches = core.rows(cx,'SELECT * FROM events WHERE reference=?',(ref,))
            signed = data['amount_cents']
            matches = [r for r in matches if
              ((signed > 0 and r['target']==a['id'] and r['target_cents']==signed) or
               (signed < 0 and r['source']==a['id'] and r['source_cents']==-signed))]
            kind = 'event'
        elif record['profile'] == 'bets':
            matches = core.rows(cx,'SELECT * FROM bets WHERE reference=? AND account=? AND stake_cents=?',
                                (ref,a['id'],data['stake_cents']))
            matches = [r for r in matches if (data['payout_cents'] is None or r['payout_cents']==data['payout_cents'])]
            kind = 'bet'
        else:
            raise ValueError('Holdings snapshots have no independent trade ID match; use Update holding')
        if len(matches)!=1:
            raise ValueError('No single exact matching ledger entry by reference, amount and account')
        state_new = 'matched'; linked_id = matches[0]['id']
    elif record['profile'] == 'cash' and action in {'cash_in','cash_out','fee'}:
        signed = data['amount_cents']
        if (signed > 0 and action!='cash_in') or (signed < 0 and action=='cash_in'):
            raise ValueError('Chosen action disagrees with signed amount')
        # Import reference is namespaced to avoid mixing accounts and sources.
        ref = 'csv:'+str(record['id'])+':'+record['digest'][:16]
        d = {'kind':action,'amount':core.money(abs(signed)), 'evidence':'user_recorded',
             'reference':ref,'memo':'CSV reviewed: '+data.get('description','')[:180]}
        if action=='cash_in':d['target']=a['id']
        else:d['source']=a['id']
        # Commit posting and review state together (core supports outer transactions).
        with cx:
            core.add_event(cx,d)
            linked_id=cx.execute('SELECT id FROM events WHERE reference=?',(ref,)).fetchone()[0]
            cx.execute('UPDATE import_records SET review_state=?,ledger_type=?,ledger_id=?,reviewed_at=? WHERE id=?',
                       ('applied','event',linked_id,core.now(),record_id))
        return {'state':'applied','ledger_type':'event','ledger_id':linked_id}
    elif record['profile'] == 'bets' and action=='record_bet':
        if state in {'void','cancelled','canceled'}:
            raise ValueError('Voided/cancelled bets need manual correction, not a new bet')
        external_ref = data.get('reference','')
        prior = cx.execute('''SELECT r.ledger_id,b.* FROM import_records r
            JOIN bets b ON b.id=r.ledger_id
            WHERE r.account=? AND r.profile='bets' AND r.review_state IN ('applied','matched')
              AND json_extract(r.data_json,'$.reference')=? AND r.ledger_type='bet'
            ORDER BY r.id DESC LIMIT 1''', (a['id'], external_ref)).fetchone() if external_ref else None
        if prior and prior['stake_cents']!=data['stake_cents']:
            raise ValueError('A previously imported bet has the same reference but different stake; review manually')
        ref = 'csv:'+str(record['id'])+':'+record['digest'][:16]
        with cx:
            if prior:
                linked_id = prior['ledger_id']
                if prior['payout_cents'] is not None:
                    if data['payout_cents'] is None or prior['payout_cents']==data['payout_cents']:
                        action_state = 'matched'
                    else:
                        raise ValueError('Already settled bet changed payout; cannot automatically revise it')
                elif data['payout_cents'] is not None and state not in OPEN_BET_STATUS:
                    core.settle_bet(cx,linked_id,core.money(data['payout_cents']), 'user_recorded')
                    stamp = parse_utc_date(data.get('settled_at',''))
                    if stamp:cx.execute('UPDATE bets SET settled_at=? WHERE id=?',(stamp,linked_id))
                    action_state = 'applied'
                else:
                    action_state = 'matched'
            else:
                linked_id=core.add_bet(cx,{'account':a['id'],'category':data['category'],
                    'stake':core.money(data['stake_cents']),'reference':ref,
                    'evidence':'user_recorded','memo':'CSV reviewed: '+external_ref[:110]})
                stamp = parse_utc_date(data.get('date',''))
                if stamp:cx.execute('UPDATE bets SET placed_at=? WHERE id=?',(stamp,linked_id))
                if data['payout_cents'] is not None and state not in OPEN_BET_STATUS:
                    core.settle_bet(cx,linked_id,core.money(data['payout_cents']), 'user_recorded')
                    stamp=parse_utc_date(data.get('settled_at',''))
                    if stamp:cx.execute('UPDATE bets SET settled_at=? WHERE id=?',(stamp,linked_id))
                action_state = 'applied'
            cx.execute('UPDATE import_records SET review_state=?,ledger_type=?,ledger_id=?,reviewed_at=? WHERE id=?',
                       (action_state,'bet',linked_id,core.now(),record_id))
        return {'state':action_state,'ledger_type':'bet','ledger_id':linked_id}
    elif record['profile'] == 'holdings' and action=='update_holding':
        # This is a snapshot, not a buy/sell. Require explicit confirmation.
        with cx:
            stamp = parse_utc_date(data.get('date',''))
            existing = cx.execute('SELECT observed_at FROM positions WHERE account=? AND symbol=?',
                                  (a['id'],data['symbol'])).fetchone()
            if stamp and existing and stamp < existing['observed_at']:
                raise ValueError('Imported snapshot is older than current holding; leave staged as history')
            core.add_position(cx,{'account':a['id'],'symbol':data['symbol'],
                'asset_type':data['asset_type'],'quantity':data['quantity'],
                'unit_price':data['unit_price'],'quote_currency':data['currency']})
            cx.execute("UPDATE positions SET source='statement_csv',observed_at=? WHERE account=? AND symbol=?",
                       (stamp or core.now(),a['id'],data['symbol']))
            linked_id=cx.execute('SELECT id FROM positions WHERE account=? AND symbol=?',
                                 (a['id'],data['symbol'])).fetchone()[0]
            cx.execute('UPDATE import_records SET review_state=?,ledger_type=?,ledger_id=?,reviewed_at=? WHERE id=?',
                       ('applied','position',linked_id,core.now(),record_id))
        return {'state':'applied','ledger_type':'position','ledger_id':linked_id}
    else:
        raise ValueError('Action not allowed for this import profile')
    with cx:
        cx.execute('UPDATE import_records SET review_state=?,ledger_type=?,ledger_id=?,reviewed_at=? WHERE id=?',
                   (state_new,kind,linked_id,core.now(),record_id))
    return {'state':state_new,'ledger_type':kind,'ledger_id':linked_id}


def report(cx):
    ensure_schema(cx)
    batches = core.rows(cx, '''SELECT b.*,a.name AS account_name,a.currency AS account_currency
        FROM import_batches b JOIN accounts a ON a.id=b.account ORDER BY b.id DESC LIMIT 60''')
    records = core.rows(cx, '''SELECT r.*,a.name AS account_name,a.currency AS account_currency
        FROM import_records r JOIN accounts a ON a.id=r.account ORDER BY r.id DESC LIMIT 300''')
    for r in records:
        r['data']=json.loads(r.pop('data_json'))
        r.pop('digest',None)
        r.pop('external_key',None)
    issues=core.rows(cx, 'SELECT * FROM import_issues ORDER BY id DESC LIMIT 150')
    summaries=[]
    for b in batches:
        entries=core.rows(cx,'SELECT data_json,review_state FROM import_records WHERE batch_id=?',(b['id'],))
        counts={'staged':0,'applied':0,'matched':0,'ignored':0}
        totals={'in_cents':0,'out_cents':0,'stakes_cents':0,'payout_cents':0,'settled_pnl_cents':0,'open_bets':0,'holdings_value':'0'}
        latest_positions={}
        for r in entries:
            counts[r['review_state']]=counts.get(r['review_state'],0)+1
            d=json.loads(r['data_json'])
            if b['profile']=='cash':
                signed=d['amount_cents']
                totals['in_cents']+=max(signed,0);totals['out_cents']+=max(-signed,0)
            elif b['profile']=='bets':
                totals['stakes_cents']+=d['stake_cents']
                if d['payout_cents'] is None: totals['open_bets']+=1
                else:
                    totals['payout_cents']+=d['payout_cents']
                    totals['settled_pnl_cents']+=d['payout_cents']-d['stake_cents']
            else:
                # Most recent row per symbol and quote currency in this batch.
                # Older snapshots are history, NOT extra holdings.
                key=(d['symbol'],d['currency'])
                if key not in latest_positions or (d.get('date',''),r['data_json'])>(latest_positions[key].get('date',''),json.dumps(latest_positions[key])):
                    latest_positions[key]=d
        by_currency={}
        for d in latest_positions.values():
            by_currency[d['currency']]=by_currency.get(d['currency'],Decimal('0'))+Decimal(d['quantity'])*Decimal(d['unit_price'])
        totals.pop('holdings_value',None)
        b['summary']={**counts,**{k:core.money(v) if k.endswith('_cents') else v for k,v in totals.items()},
            'holdings_by_currency':{curr:str(val.quantize(Decimal('.01'),rounding=ROUND_HALF_UP)) for curr,val in sorted(by_currency.items())},
            'holding_symbols':len(latest_positions)}
        b.pop('mapping_json',None)
    return {'batches':batches,'records':records,'issues':issues,
            'notice':'CSV values are user-supplied, not independently verified. Imports may overlap. Summary totals are per batch; do not add repeated snapshots or count deposits as profit. Ledger balances change only after row-by-row approval.'}
