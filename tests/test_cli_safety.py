import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class CliSafetyTests(unittest.TestCase):
    def test_live_adapter_refuses_without_explicit_consent(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.run([sys.executable,'tracker.py','tick','--db',str(Path(tmp)/'x.db'),
                '--provider','scryfall','--watchlist','samples/scryfall_watchlist.example.json'],
                cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('--consent-network',result.stderr)
    def test_legacy_offline_command_remains_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/'tracker.db'
            enable=subprocess.run([sys.executable,'tracker.py','enable','--db',str(db)],cwd=ROOT,capture_output=True,text=True,timeout=10)
            self.assertEqual(enable.returncode,0,enable.stderr)
            tick=subprocess.run([sys.executable,'tracker.py','tick','--db',str(db),'--watchlist','samples/watchlist.json',
                '--catalog','samples/offline_cards.csv'],cwd=ROOT,capture_output=True,text=True,timeout=10)
            self.assertEqual(tick.returncode,0,tick.stderr)
            self.assertIn('offline_catalog_only',tick.stdout)

if __name__=='__main__':unittest.main()
