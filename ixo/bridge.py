"""Explicit read-only IXO -> AIXO capture; source identity is checked in AIXO."""
from __future__ import annotations
import json


def capture(ixo, aixo):
    # Snapshot under IXO lock; AIXO sees committed, ordered source events only.
    with ixo.lock:
        source_id = ixo._get('instance_id')
        rows = [dict(r) for r in ixo.conn.execute('SELECT * FROM events ORDER BY seq')]
    for row in rows:
        row['payload'] = json.loads(row['payload'])
    return aixo.ingest_events(rows, source_id=source_id)
