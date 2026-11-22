"""Offline evidence register for *claimed* completed card sales.

No scraping, network access, account connection or portfolio/ledger mutation.
User-supplied CSV is unverified evidence, never automatically promoted to truth.
"""
import argparse
import csv
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sqlite3
from urllib.parse import urlsplit

from tracker import ClosingConnection, ROOT

FIELDS = ('game', 'name', 'set_code', 'collector_number', 'marketplace',
          'sale_id', 'sold_at', 'price', 'currency', 'condition', 'source_url')
GAMES = {'MTG', 'POKEMON', 'YUGIOH'}
CURRENCIES = {'CAD', 'NZD', 'AUD', 'USD', 'EUR', 'GBP', 'JPY'}
MAX_BYTES = 2_000_000
MAX_ROWS = 2_000


def connect(path):
    return sqlite3.connect(path, timeout=3, factory=ClosingConnection)


def _clean(value, field, max_len=180):
    if not isinstance(value, str):
        raise ValueError(f'{field} is missing')
    value = value.strip()
    if not value or len(value) > max_len or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError(f'invalid {field}')
    return value


def normalize(row):
    r = {key: _clean(row.get(key), key, 300 if key == 'source_url' else 180) for key in FIELDS}
    r['game'] = r['game'].upper()
    r['currency'] = r['currency'].upper()
    if r['game'] not in GAMES or r['currency'] not in CURRENCIES:
        raise ValueError('unsupported game or currency')
    if len(r['sale_id']) > 100 or len(r['marketplace']) > 80:
        raise ValueError('sale identity too long')
    try:
        day = date.fromisoformat(r['sold_at'])
    except ValueError as exc:
        raise ValueError('sold_at must be YYYY-MM-DD') from exc
    if not date(2000, 1, 1) <= day <= date.today():
        raise ValueError('sale date outside supported range')
    r['sold_at'] = day.isoformat()
    try:
        amount = Decimal(r['price'])
        if not amount.is_finite() or not Decimal('0') < amount <= Decimal('1000000'):
            raise ValueError('invalid price')
        if amount.as_tuple().exponent < -2:
            raise ValueError('price must have at most 2 decimal places')
        r['price'] = str(amount.quantize(Decimal('0.01')))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('invalid price') from exc
    parsed = urlsplit(r['source_url'])
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.port not in (None, 443) or parsed.hostname in ('localhost', '127.0.0.1')
            or parsed.hostname.endswith('.local')):
        raise ValueError('source_url must be a public HTTPS reference')
    return r


def _fingerprint(row):
    payload = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def import_csv(db_path, csv_path):
    """Validate all rows first, then write atomically. Never affects treasury balances."""
    csv_path = Path(csv_path)
    if csv_path.stat().st_size > MAX_BYTES:
        raise ValueError('CSV file exceeds 2 MB limit')
    batch_sha256 = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    records = []
    seen = {}
    with csv_path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or not set(FIELDS).issubset(reader.fieldnames):
            raise ValueError('CSV requires: ' + ', '.join(FIELDS))
        for index, row in enumerate(reader):
            if index >= MAX_ROWS:
                raise ValueError('CSV exceeds 2000 rows')
            if None in row:
                raise ValueError('CSV has unexpected extra columns')
            record = normalize(row)
            key = (record['marketplace'].casefold(), record['sale_id'])
            signature = _fingerprint(record)
            if key in seen:
                if seen[key] != signature:
                    raise ValueError('same marketplace/sale_id has conflicting data in CSV')
                continue
            seen[key] = signature
            records.append((record, signature))
    if not records:
        raise ValueError('CSV has no sale rows')
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS sale_evidence(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            marketplace_key TEXT NOT NULL,
            sale_id TEXT NOT NULL,
            fingerprint TEXT NOT NULL,
            record_json TEXT NOT NULL,
            verification_status TEXT NOT NULL CHECK(verification_status='unverified'),
            imported_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            batch_sha256 TEXT NOT NULL,
            UNIQUE(marketplace_key,sale_id))''')
        db.execute('BEGIN IMMEDIATE')
        inserted = 0
        for record, signature in records:
            key = record['marketplace'].casefold()
            old = db.execute('SELECT fingerprint FROM sale_evidence WHERE marketplace_key=? AND sale_id=?',
                             (key,record['sale_id'])).fetchone()
            if old:
                if old[0] != signature:
                    raise ValueError(f'conflict for marketplace/sale_id: {record["marketplace"]} / {record["sale_id"]}')
                continue
            db.execute('INSERT INTO sale_evidence(marketplace_key,sale_id,fingerprint,record_json,verification_status,batch_sha256) VALUES(?,?,?,?,?,?)',
                       (key,record['sale_id'],signature,json.dumps(record,ensure_ascii=False,sort_keys=True),'unverified',batch_sha256))
            inserted += 1
    return {'imported':inserted, 'duplicates':len(records)-inserted, 'source_file_sha256':batch_sha256, 'verification_status':'unverified',
            'warning':'CSV entries are user-supplied claims, not independently verified completed sales.'}


def read_sales(db_path, limit=100, search=''):
    """Read without creating tables. No cross-currency arithmetic."""
    if not isinstance(limit,int) or not 1 <= limit <= 500:
        raise ValueError('limit must be 1..500')
    if len(search) > 100 or any(ord(c) < 32 for c in search):
        raise ValueError('invalid search')
    if not Path(db_path).exists():
        return []
    with connect(db_path) as db:
        exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sale_evidence'").fetchone()
        if not exists:
            return []
        # Bounded scan of 2,000 imported records; filter before slicing so old matches are discoverable.
        rows = db.execute('SELECT id,record_json,verification_status,imported_at,batch_sha256 FROM sale_evidence ORDER BY id DESC LIMIT 20000').fetchall()
        from sale_review import reviews_for
        reviews = reviews_for(db, [row[0] for row in rows])
    result = []
    term = search.strip().casefold()
    for evidence_id, payload, status, imported_at, batch_sha256 in rows:
        record = json.loads(payload)
        if term and term not in ' / '.join(str(record.get(k,'')) for k in ('game','name','set_code','collector_number','marketplace','currency','condition')).casefold():
            continue
        result.append({**record,'verification_status':status,'imported_at':imported_at,'source_file_sha256':batch_sha256,'review':reviews.get(evidence_id)})
        if len(result) >= limit:
            break
    return result


def main():
    parser = argparse.ArgumentParser(description='Import user-supplied, unverified card sale evidence. Offline only.')
    parser.add_argument('csv',type=Path)
    parser.add_argument('--db',type=Path,default=ROOT/'data'/'tracker.db')
    args = parser.parse_args()
    print(json.dumps(import_csv(args.db,args.csv),indent=2))


if __name__ == '__main__':
    main()
