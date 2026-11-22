import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from email.message import Message

from tracker import Tracker,INTERVAL
from scryfall_watch import observe,load_watchlist,ProviderUnavailable,ProviderRateLimited,_http_get

class ScryfallTests(unittest.TestCase):
    def card(self,number='7',price='1.45'):
        return {'object':'card','set':'dmu','collector_number':number,'name':'Test printing','prices':{'usd':price,'eur':'2.00','usd_foil':None}}
    def entry(self,number='7'):
        return {'game':'MTG','set_code':'DMU','collector_number':number}
    def test_scryfall_exact_lookup_and_provenance(self):
        requests=[]
        result=observe([self.entry()],get=lambda url,timeout:(requests.append((url,timeout)),self.card())[1])
        self.assertEqual(requests,[('https://api.scryfall.com/cards/dmu/7',6)])
        self.assertEqual(result['source'],'Scryfall')
        self.assertFalse(result['completed_sales'])
        card=result['cards'][0]['card']
        self.assertEqual(card['indicative_prices'],{'usd':'1.45','eur':'2.00'})
        self.assertEqual(card['price_as_of'],'not supplied by provider')
        self.assertEqual(card['source_url'],'https://scryfall.com/card/dmu/7')
    def test_404_unmatched_never_invented(self):
        output=observe([self.entry()],get=lambda url,timeout:None)
        self.assertEqual(output['cards'][0]['status'],'unmatched')
        self.assertIsNone(output['cards'][0]['card'])
    def test_invalid_identity_and_card_mismatch(self):
        for entry in ({'game':'POKEMON','set_code':'dmu','collector_number':'7'},
                      {'game':'MTG','set_code':'dmu','collector_number':'../admin'},
                      {'game':'MTG','set_code':'https','collector_number':'x/x'}):
            with self.assertRaises(ValueError): observe([entry],get=lambda u,t:self.card())
        with self.assertRaises(ProviderUnavailable):observe([self.entry()],get=lambda u,t:self.card('8'))
    def test_rate_limiter_between_requests(self):
        clock=[0.0]; slept=[]
        def sleep(sec):slept.append(sec);clock[0]+=sec
        observe([self.entry(),self.entry('8')],get=lambda u,t:self.card('8' if u.endswith('/8') else '7'),sleep=sleep,monotonic=lambda:clock[0])
        self.assertEqual(len(slept),1)
        self.assertGreaterEqual(slept[0],.25)
    def test_watchlist_limits_and_duplicates(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'watch.json'
            p.write_text(json.dumps([self.entry(),self.entry()]),encoding='utf8')
            with self.assertRaisesRegex(ValueError,'duplicate'):load_watchlist(p)
            p.write_text(json.dumps([self.entry(str(n)) for n in range(21)]),encoding='utf8')
            with self.assertRaisesRegex(ValueError,'1-20'):load_watchlist(p)
    def test_http_429_retry_after(self):
        headers=Message();headers.add_header('Retry-After','3600')
        class Opener:
            def open(self,req,timeout):
                raise HTTPError(req.full_url,429,'limit',headers,None)
        with patch('scryfall_watch.build_opener',return_value=Opener()):
            with self.assertRaises(ProviderRateLimited) as caught:
                _http_get('https://api.scryfall.com/cards/dmu/7',6)
        self.assertEqual(caught.exception.retry_after,3600)
    def test_rate_limit_backoff_preserves_previous_observation(self):
        with tempfile.TemporaryDirectory() as td:
            now=[1000]
            t=Tracker(Path(td)/'tracker.db',lambda:now[0]);t.enable(True)
            self.assertEqual(t.tick(lambda:{'cards':['prior']}),'ok')
            now[0]+=INTERVAL
            def limited(): raise ProviderRateLimited(4000)
            self.assertEqual(t.tick(limited),'error')
            status=t.status()
            self.assertEqual(status['next_due'],now[0]+4000)
            self.assertEqual(status['observation'],{'cards':['prior']})
            self.assertEqual(status['history'][0][2],'ProviderRateLimited')
    def test_v05_db_migration(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'old.db'
            with sqlite3.connect(path) as db:
                db.executescript('''CREATE TABLE control(id INTEGER PRIMARY KEY CHECK(id=1), enabled INTEGER NOT NULL, due REAL NOT NULL, failures INTEGER NOT NULL);
                INSERT INTO control VALUES(1,1,0,0);
                CREATE TABLE history(id INTEGER PRIMARY KEY,at REAL NOT NULL,outcome TEXT NOT NULL,detail TEXT NOT NULL);
                CREATE TABLE observation(id INTEGER PRIMARY KEY CHECK(id=1),at REAL NOT NULL,payload TEXT NOT NULL);
                INSERT INTO observation VALUES(1,200,'{"old":true}');''')
            t=Tracker(path,lambda:1000)
            self.assertEqual(t.status()['observation'],{'old':True})
            self.assertEqual(t.tick(lambda:{'new':True}),'ok')
            self.assertEqual(Tracker(path,lambda:1000).tick(lambda:None),'waiting')

if __name__=='__main__': unittest.main()
