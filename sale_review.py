"""Local, offline analyst annotations for claimed card sales; never certifies a transaction."""
import argparse
import json
from pathlib import Path
from sold_research import connect

DECISIONS = ('needs_review', 'document_seen', 'disputed', 'excluded')


def annotate(db_path, marketplace, sale_id, decision, note):
    if decision not in DECISIONS:
        raise ValueError('invalid review decision')
    for field, value, bound in (('marketplace', marketplace, 80), ('sale_id', sale_id, 100), ('note', note, 500)):
        if not isinstance(value, str) or not value.strip() or len(value) > bound or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise ValueError('invalid ' + field)
    path = Path(db_path)
    if not path.is_file():
        raise ValueError('sale database does not exist')
    with connect(path) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sale_evidence'").fetchone():
            raise ValueError('no imported sale evidence')
        row = db.execute('SELECT id FROM sale_evidence WHERE marketplace_key=? AND sale_id=?',
                         (marketplace.strip().casefold(), sale_id.strip())).fetchone()
        if row is None:
            raise ValueError('sale identity not found')
        db.execute('''CREATE TABLE IF NOT EXISTS sale_review(
            id INTEGER PRIMARY KEY, sale_evidence_id INTEGER NOT NULL,
            decision TEXT NOT NULL CHECK(decision IN ('needs_review','document_seen','disputed','excluded')),
            note TEXT NOT NULL, reviewed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            FOREIGN KEY(sale_evidence_id) REFERENCES sale_evidence(id))''')
        db.execute('INSERT INTO sale_review(sale_evidence_id,decision,note) VALUES(?,?,?)',
                   (row[0], decision, note.strip()))
    return {'decision': decision, 'warning': 'Analyst annotation only; transaction remains unverified.'}


def reviews_for(db, ids):
    if not ids:
        return {}
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='sale_review'").fetchone():
        return {}
    placeholders = ','.join('?' for _ in ids)
    rows = db.execute(f'''SELECT sale_evidence_id,decision,note,reviewed_at FROM sale_review
        WHERE id IN (SELECT MAX(id) FROM sale_review WHERE sale_evidence_id IN ({placeholders}) GROUP BY sale_evidence_id)''', ids).fetchall()
    return {id_: {'decision': decision, 'note': note, 'reviewed_at': timestamp} for id_,decision,note,timestamp in rows}


def main():
    parser = argparse.ArgumentParser(description='Offline analyst review of an imported sale claim. Does not verify sale.')
    parser.add_argument('--db', type=Path, default=Path(__file__).parent/'data'/'tracker.db')
    parser.add_argument('--marketplace', required=True)
    parser.add_argument('--sale-id', required=True)
    parser.add_argument('--decision', required=True, choices=DECISIONS)
    parser.add_argument('--note', required=True)
    args = parser.parse_args()
    print(json.dumps(annotate(args.db,args.marketplace,args.sale_id,args.decision,args.note),indent=2))

if __name__ == '__main__':
    main()
