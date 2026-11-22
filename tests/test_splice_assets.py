import unittest
from pathlib import Path
from run import ASSETS
class SpliceAssets(unittest.TestCase):
    def test_routes_refer_to_real_assets(self):
        for route in ('/splice','/splice.js','/splice-core.mjs','/splice.css'):
            self.assertIn(route, ASSETS)
            self.assertTrue(Path(ASSETS[route][0]).is_file())
    def test_original_source_not_mutated(self):
        self.assertIn('Inspired by Self',Path(__file__).resolve().parents[1].joinpath('engine.py').read_text())
