import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core, migrate, imports

class MigrationTests(unittest.TestCase):
    def test_migration_preserves_data_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); old=root/'old'; old.mkdir()
            (old/'data').mkdir()
            source=old/'data'/'treasury.db'
            cx=core.db_open(source)
            core.add_event(cx,{'kind':'cash_in','target':'ca_bank','amount':'500','reference':'original'})
            old_count=cx.execute('SELECT COUNT(*) FROM events').fetchone()[0]
            cx.close()
            dest=root/'new'/'data'/'treasury.db'
            msg=migrate.migrate(old,dest)
            self.assertIn('Migrated successfully',msg)
            upgraded=core.db_open(dest)
            self.assertEqual(upgraded.execute('SELECT count(*) FROM events').fetchone()[0],old_count)
            self.assertEqual(core.balances(upgraded)['ca_bank'],50000)
            self.assertTrue(upgraded.execute("SELECT name FROM sqlite_master WHERE name='import_records'").fetchone())
            upgraded.close()
            with self.assertRaises(ValueError):migrate.migrate(old,dest)
            src=core.db_open(source)
            self.assertEqual(src.execute('SELECT count(*) FROM events').fetchone()[0],old_count)
            src.close()

if __name__=='__main__':unittest.main()
