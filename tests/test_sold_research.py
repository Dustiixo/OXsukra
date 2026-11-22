"""Provenance-safe offline claimed-sale import and read-only dashboard contract."""
import csv
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

from sold_research import FIELDS, import_csv, read_sales
from tracker import Tracker
from watch_dashboard import make_handler, render


def example(**overrides):
    row = dict(game='MTG', name='Fictional Example', set_code='TST', collector_number='3',
               marketplace='Demo Only', sale_id='demo-1', sold_at='2026-01-01',price='15.00',
               currency='CAD', condition='Near Mint',source_url='https://example.com/fictional-sale')
    row.update(overrides)
    return row


def write_csv(path, records):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS)
        writer.writeheader();writer.writerows(records)


class SoldResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root/'tracker.db'
        self.csv = self.root/'sales.csv'

    def test_three_games_currencies_and_unverified(self):
        write_csv(self.csv,[example(),example(game='POKEMON',currency='NZD',sale_id='demo-2'),
                            example(game='YUGIOH',currency='AUD',sale_id='demo-3')])
        result=import_csv(self.db,self.csv)
        self.assertEqual(result['imported'],3)
        sales=read_sales(self.db)
        self.assertEqual({x['currency'] for x in sales},{'CAD','NZD','AUD'})
        self.assertTrue(all(x['verification_status']=='unverified' for x in sales))
        self.assertTrue(all(len(x['source_file_sha256'])==64 and x['imported_at'].endswith('Z') for x in sales))
        self.assertEqual(read_sales(self.db,search='pokemon')[0]['game'],'POKEMON')

    def test_repeat_import_is_idempotent(self):
        write_csv(self.csv,[example()])
        self.assertEqual(import_csv(self.db,self.csv)['imported'],1)
        result=import_csv(self.db,self.csv)
        self.assertEqual((result['imported'],result['duplicates']),(0,1))
        self.assertEqual(len(read_sales(self.db)),1)

    def test_conflicting_record_rolls_back_all_new_rows(self):
        write_csv(self.csv,[example()]);import_csv(self.db,self.csv)
        write_csv(self.csv,[example(sale_id='another'),example(price='999.00')])
        with self.assertRaisesRegex(ValueError,'conflict'):
            import_csv(self.db,self.csv)
        self.assertEqual(len(read_sales(self.db)),1)

    def test_validation_is_atomic_before_database_touch(self):
        write_csv(self.csv,[example(),example(sale_id='x',price='NaN')])
        with self.assertRaises(ValueError):import_csv(self.db,self.csv)
        self.assertFalse(self.db.exists())
        for broken in [example(price='-1'),example(sold_at='2099-01-01'),
                       example(source_url='http://example.com/a'),example(game='NOT_A_CARD_GAME')]:
            write_csv(self.csv,[broken])
            with self.assertRaises(ValueError):import_csv(self.db,self.csv)

    def test_duplicate_id_conflict_inside_one_csv(self):
        write_csv(self.csv,[example(),example(price='16.00')])
        with self.assertRaisesRegex(ValueError,'conflicting data'):
            import_csv(self.db,self.csv)
        self.assertFalse(self.db.exists())

    def test_empty_read_is_nonmutating(self):
        self.assertEqual(read_sales(self.db),[])
        self.assertFalse(self.db.exists())
        with self.assertRaises(ValueError):read_sales(self.db,search='a\x00b')
        with self.assertRaises(ValueError):read_sales(self.db,limit=999)

    def test_dashboard_separates_imported_sales_from_indicative_chart(self):
        tracker=Tracker(self.db);tracker.enable(True)
        self.assertEqual(tracker.tick(lambda:{'source':'fictional quote', 'cards':[{'game':'MTG','name':'Other Quote', 'set_code':'TST','collector_number':'2','unit_price':'8','currency':'USD'}]}),'ok')
        original=tracker.status()['observation']
        write_csv(self.csv,[example(name='<script>alert(1)</script>')]);import_csv(self.db,self.csv)
        page=render(tracker.status(),sales=read_sales(self.db))
        self.assertIn('Claimed completed sales (1)',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertNotIn('<script>',page)
        self.assertIn('UNVERIFIED',page)
        self.assertIn('Indicative price history',page)
        self.assertEqual(tracker.status()['observation'],original)

    def test_sales_json_is_read_only_and_rejects_invalid_limits(self):
        write_csv(self.csv,[example()]);import_csv(self.db,self.csv)
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.db))
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            with urlopen(base+'/sales.json?limit=1&q=fictional') as r:
                payload=json.load(r)
                self.assertEqual(r.headers['Cache-Control'],'no-store')
                self.assertEqual(payload['records'][0]['verification_status'],'unverified')
            for suffix in ('?limit=0','?limit=501','?q='+'x'*101):
                with self.assertRaises(HTTPError) as e:urlopen(base+'/sales.json'+suffix)
                self.assertEqual(e.exception.code,400)
            self.assertEqual(len(read_sales(self.db)),1)
        finally:
            server.shutdown();server.server_close();thread.join(timeout=2)

if __name__ == '__main__':unittest.main()
