"""Import an existing v0.1/v0.2 Treasury SQLite ledger via SQLite online backup.

Usage: python migrate.py --source "C:\\path\\to\\OX_Treasury_v0_2"
Or:    python migrate.py --source "C:\\path\\to\\treasury.db"
The destination must not already exist. Does not modify source database.
"""
import argparse
import sqlite3
from contextlib import closing
from pathlib import Path
import core
import imports


def migrate(source, target):
    src=Path(source).expanduser()
    if src.is_dir():src=src/'data'/'treasury.db'
    if not src.is_file():raise ValueError(f'Old ledger not found: {src}')
    dst=Path(target).expanduser()
    if dst.exists():raise ValueError(f'Destination already exists: {dst}. No overwrite attempted.')
    if src.resolve()==dst.resolve():raise ValueError('Source and destination must differ')
    dst.parent.mkdir(parents=True,exist_ok=True)
    try:
        # Consistent SQLite snapshot, even if old ledger uses WAL journaling.
        with closing(sqlite3.connect(src.resolve().as_uri() + '?mode=ro', uri=True)) as old:
            with closing(sqlite3.connect(dst)) as new:
                old.backup(new)
        with closing(core.db_open(dst)) as cx:
            imports.ensure_schema(cx)
            result=cx.execute('PRAGMA integrity_check').fetchone()[0]
            accounts=cx.execute('SELECT count(*) FROM accounts').fetchone()[0]
            events=cx.execute('SELECT count(*) FROM events').fetchone()[0]
        if result!='ok':raise ValueError('Migrated database failed integrity_check')
        return f'Migrated successfully: {accounts} accounts, {events} money movements. New database: {dst}'
    except Exception:
        # Do not leave an incomplete database that could be mistaken for a good migration.
        for file in (dst,Path(str(dst)+'-wal'),Path(str(dst)+'-shm')):
            if file.exists(): file.unlink()
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True,help='Previous extracted app folder or path to treasury.db')
    p.add_argument('--target',default=str(Path(__file__).resolve().parent/'data'/'treasury.db'))
    args=p.parse_args()
    try:print(migrate(args.source,args.target))
    except (ValueError,sqlite3.Error) as e:raise SystemExit('Migration not completed: '+str(e))
