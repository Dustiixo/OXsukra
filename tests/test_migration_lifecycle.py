"""Regression: migration closes backup connections and handles URI-escaped paths."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core
import migrate


class MigrationLifecycleTests(unittest.TestCase):
    def test_special_characters_in_source_path(self):
        with tempfile.TemporaryDirectory() as temp:
            src = Path(temp) / 'source # 100% ü' / 'ledger.db'
            src.parent.mkdir()
            db = core.db_open(src)
            try:
                core.add_event(db, {'kind': 'cash_in', 'target': 'ca_bank', 'amount': '13.50', 'reference': 'uri-test'})
            finally:
                db.close()
            dst = Path(temp) / 'destination' / 'treasury.db'
            self.assertIn('Migrated successfully', migrate.migrate(src, dst))
            with sqlite3.connect(dst) as check:
                self.assertEqual(check.execute("SELECT target_cents FROM events WHERE reference='uri-test'").fetchone()[0], 1350)
            # The original must remain available for a new exclusive write transaction.
            with sqlite3.connect(src, timeout=0.2) as original:
                original.execute('BEGIN EXCLUSIVE')
                original.execute('ROLLBACK')

    def test_missing_source_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            dst = Path(temp) / 'new' / 'treasury.db'
            with self.assertRaises(ValueError):
                migrate.migrate(Path(temp) / 'missing.db', dst)
            self.assertFalse(dst.exists())

if __name__ == '__main__':
    unittest.main()
