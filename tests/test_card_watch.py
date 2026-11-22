import tempfile
import unittest
from pathlib import Path
from card_watch import load_catalog,observe,from_files
from tracker import Tracker

class CardWatchTests(unittest.TestCase):
    def test_three_games(self):
        root=Path(__file__).resolve().parents[1]
        obs=from_files(root/'samples/watchlist.json',root/'samples/offline_cards.csv')
        self.assertEqual([x['status'] for x in obs['cards']],['matched']*3)
        self.assertFalse(obs['price_data'])
    def test_missing_card_not_invented(self):
        self.assertEqual(observe([{'game':'MTG','set_code':'X','collector_number':'1'}],{})['cards'][0]['status'],'unmatched')
    def test_duplicate_identity_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'c.csv';p.write_text('game,name,set_code,collector_number,source\nMTG,A,X,1,a\nMTG,B,X,1,b\n')
            with self.assertRaisesRegex(ValueError,'duplicate'):load_catalog(p)
    def test_integrated_tick_persists_observation(self):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as d:
            t=Tracker(Path(d)/'tracker.db',clock=lambda:1000)
            t.enable(True)
            self.assertEqual(t.tick(lambda:from_files(root/'samples/watchlist.json',root/'samples/offline_cards.csv')),'ok')
            self.assertEqual(len(t.status()['observation']['cards']),3)
            self.assertEqual(t.tick(lambda:None),'waiting')
    def test_unsupported_game(self):
        with self.assertRaisesRegex(ValueError,'unsupported'):observe([{'game':'OTHER','set_code':'A','collector_number':'1'}],{})
