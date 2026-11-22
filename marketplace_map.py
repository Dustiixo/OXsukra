"""Offline eBay Seller Hub order-export normalizer for *user-owned* sale research.

All seller/order data is read locally. Output is an intentionally narrow CSV of
UNVERIFIED claims, not proof of sales, portfolio value, or a market-wide feed.
No network calls, credentials, wagers, trades, or ledger writes.
"""
import argparse
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from sold_research import FIELDS, MAX_BYTES, MAX_ROWS, normalize

PROFILE = 'ebay_seller_orders_v1'
REQUIRED_EXPORT = ('Order Number', 'Item Number', 'Transaction ID', 'Item Title',
                   'Sold For', 'Quantity', 'Sale Date')
ANNOTATION_FIELDS = ('order_number', 'item_number', 'transaction_id', 'game', 'name',
                     'set_code', 'collector_number', 'condition', 'source_url')
IGNORED_PERSONAL_FIELDS = ('Buyer Username','Buyer Name','Buyer Email','Buyer Address 1',
                           'Buyer Address 2','Ship To Name','Ship To Phone','Ship To Address 1',
                           'Ship To Address 2','Tracking Number','PayPal Transaction ID')


def _load_csv(path, mandatory):
    path = Path(path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('CSV exceeds 2 MB limit')
    rows = []
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not set(mandatory).issubset(headers):
            raise ValueError('missing or duplicated columns: ' + ', '.join(mandatory))
        for index, row in enumerate(reader):
            if index >= MAX_ROWS:
                raise ValueError('CSV exceeds 2000 rows')
            if None in row:
                raise ValueError('CSV has extra unexpected columns')
            rows.append(row)
    if not rows:
        raise ValueError('CSV has no data rows')
    return rows, headers, hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(order, item, transaction):
    fields = (order, item, transaction)
    for v in fields:
        if not isinstance(v, str) or not v.strip() or len(v) > 100 or any(ord(c) < 32 for c in v):
            raise ValueError('order/item/transaction identity must be nonempty, <=100 characters')
    return tuple(v.strip() for v in fields)


def _date(text):
    if not isinstance(text, str):
        raise ValueError('missing Sale Date')
    for fmt in ('%Y-%m-%d', '%b %d, %Y', '%B %d, %Y'):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError('unsupported Sale Date (use YYYY-MM-DD or Mon DD, YYYY)')


def _price(text):
    if not isinstance(text, str):
        raise ValueError('missing Sold For')
    # Symbol parsing is never used to infer currency. --currency is mandatory.
    cleaned = text.strip().replace(',', '')
    if cleaned.startswith('$'):
        cleaned = cleaned[1:]
    if not re.fullmatch(r'\d+(?:\.\d{1,2})?', cleaned):
        raise ValueError('Sold For must contain a positive decimal amount (not a total, range or formula)')
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError('invalid Sold For') from exc
    if not Decimal('0') < value <= Decimal('1000000'):
        raise ValueError('Sold For outside allowed range')
    return str(value.quantize(Decimal('0.01')))


def _fingerprint_id(key):
    encoded = json.dumps(list(key), ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return 'ebay-own-' + hashlib.sha256(encoded).hexdigest()[:32]


def inspect_export(source):
    rows, headers, digest = _load_csv(source, REQUIRED_EXPORT)
    return {
        'profile': PROFILE,
        'row_count': len(rows), 'source_sha256': digest,
        'has_sensitive_columns': bool(set(headers).intersection(IGNORED_PERSONAL_FIELDS)),
        'warning': 'Own-order export only. Buyer/shipping fields will not enter normalized sale CSV.',
    }


def convert(source, annotations, currency):
    """Generate a normalized preview payload; does not write or import anything."""
    if currency not in ('CAD','NZD','AUD','USD','EUR','GBP','JPY'):
        raise ValueError('currency must be one of CAD/NZD/AUD/USD/EUR/GBP/JPY')
    rows, headers, digest = _load_csv(source, REQUIRED_EXPORT)
    notes, _, notes_hash = _load_csv(annotations, ANNOTATION_FIELDS)
    note_map = {}
    for note in notes:
        key = _identity(note['order_number'], note['item_number'], note['transaction_id'])
        if key in note_map:
            raise ValueError('duplicated annotation identity')
        note_map[key] = note
    export_keys = set()
    candidates = []
    skipped = 0
    for index, row in enumerate(rows, start=2):
        key = _identity(row['Order Number'],row['Item Number'],row['Transaction ID'])
        if key in export_keys:
            raise ValueError('repeated order/item/transaction identity in export')
        export_keys.add(key)
        note = note_map.get(key)
        if note is None:
            skipped += 1  # Never guess game / edition from free-form item title.
            continue
        if (row['Quantity'] or '').strip() != '1':
            raise ValueError(f'row {index}: multi-quantity sale needs explicit line-item handling')
        # Protect CSV consumers (including spreadsheets) from formula-like annotations.
        for column in ('name','set_code','collector_number','condition'):
            value = note[column].lstrip()
            if value.startswith(('=','+','-','@','\t','\r')):
                raise ValueError(f'row {index}: spreadsheet formula-like {column} rejected')
        # Ignore private order/receipt links and URLs carrying query tokens.
        ref = urlsplit((note['source_url'] or '').strip())
        if ref.query or ref.fragment:
            raise ValueError(f'row {index}: source_url must be a public link without query or fragment')
        record = normalize({
            'game':note['game'], 'name':note['name'], 'set_code':note['set_code'],
            'collector_number':note['collector_number'], 'marketplace':'eBay Seller Hub own orders',
            'sale_id':_fingerprint_id(key), 'sold_at':_date(row['Sale Date']),
            'price':_price(row['Sold For']), 'currency':currency,
            'condition':note['condition'], 'source_url':note['source_url'],
        })
        candidates.append(record)
    unknown = set(note_map) - export_keys
    if unknown:
        raise ValueError('annotation identity absent from seller report')
    if not candidates:
        raise ValueError('no annotated sale rows; nothing to normalize')
    return candidates, {
        'profile':PROFILE, 'source_export_sha256':digest, 'annotations_sha256':notes_hash,
        'export_rows':len(rows), 'normalized_claims':len(candidates),
        'skipped_unannotated':skipped, 'dropped_columns':len(headers)-len(REQUIRED_EXPORT),
        'currency':currency, 'verification_status':'unverified',
        'warning':'Seller-owned orders are not independent market-wide completed-sale evidence; amounts exclude fees/shipping/tax and may be refunded. Public listing links are not proof of settlement. No PII is copied to normalized CSV.',
    }


def export_normalized(source, annotations, currency, destination):
    records, report = convert(source, annotations, currency)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Explicit no-overwrite behavior: a rerun must not destroy a reviewed file.
    with destination.open('x', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)
    report['normalized_csv_sha256'] = hashlib.sha256(destination.read_bytes()).hexdigest()
    return report


def main():
    parser = argparse.ArgumentParser(description='Offline, private eBay own-order CSV normalizer (not an eBay API).')
    parser.add_argument('--source', type=Path, required=True, help='Seller Hub orders CSV, preferably locally redacted')
    parser.add_argument('--inspect', action='store_true', help='Inspect columns and row count only; no output file')
    parser.add_argument('--annotations', type=Path, help='Manual card identities: order/item/transaction + game/edition/condition/public reference')
    parser.add_argument('--currency', help='Explicit transaction currency; never inferred from $ sign')
    parser.add_argument('--out', type=Path, help='New canonical CSV path; refusing overwrite')
    args = parser.parse_args()
    if args.inspect:
        if args.annotations or args.currency or args.out:
            parser.error('--inspect cannot be combined with mapping options')
        result = inspect_export(args.source)
    else:
        if not args.annotations or not args.currency or not args.out:
            parser.error('--annotations, --currency and --out are required for conversion')
        result = export_normalized(args.source,args.annotations,args.currency,args.out)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
