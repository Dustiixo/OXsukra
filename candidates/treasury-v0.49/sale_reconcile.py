"""Offline, fail-closed reconciliation of fictional or seller-owned order statuses.

Only explicitly settled and unreversed rows may proceed to unverified research.
No financial ledger writes or network access.
"""
from marketplace_map import _load_csv, _identity
from datetime import date

FIELDS = ('order_number', 'item_number', 'transaction_id', 'status')
STATUSES = frozenset(('settled', 'cancelled', 'refunded', 'partially_refunded', 'pending', 'disputed'))


def load_reconciliation(path, as_of=None, max_age_days=None):
    rows, headers, digest = _load_csv(path, FIELDS)
    if max_age_days is not None:
        if not isinstance(max_age_days, int) or not 0 <= max_age_days <= 365:
            raise ValueError('max status age must be 0..365 days')
        if as_of is None:
            raise ValueError('as_of date required for freshness check')
        as_of = date.fromisoformat(as_of) if isinstance(as_of, str) else as_of
        if 'observed_at' not in headers:
            raise ValueError('observed_at column required for freshness check')
    indexed = {}
    for row in rows:
        key = _identity(row['order_number'], row['item_number'], row['transaction_id'])
        status = (row['status'] or '').strip().lower()
        if status not in STATUSES:
            raise ValueError('unknown reconciliation status; use settled/cancelled/refunded/partially_refunded/pending/disputed')
        if key in indexed:
            raise ValueError('duplicate reconciliation identity')
        if max_age_days is not None:
            try:
                observed = date.fromisoformat((row.get('observed_at') or '').strip())
            except ValueError as exc:
                raise ValueError('invalid observed_at date') from exc
            age = (as_of - observed).days
            if age < 0 or age > max_age_days:
                raise ValueError('stale or future reconciliation status; refresh source before conversion')
        indexed[key] = status
    return indexed, digest
