import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tracker import Tracker
from watch_dashboard import make_handler, render

class DashboardTests(unittest.TestCase):
    def test_html_escape_and_quote_uncertainty(self):
        s={'enabled':True,'stale':False,'observation_age_seconds':10,'observed_at':100,'next_due':1000,
           'observation':{'cards':[{'name':'<script>alert(1)</script>','currency':'CAD','unit_price':'3.50'}]}}
        page=render(s)
        self.assertIn('&lt;script&gt;',page)
        self.assertNotIn('<script>',page)
        self.assertIn('Upstream quote time',page)
        self.assertIn('indicative',page)
    def test_http_read_only_status_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'tracker.db'; tracker=Tracker(db); tracker.enable(True)
            self.assertEqual(tracker.tick(lambda:{'mode':'fictional fixture','cards':[{'name':'Sample','currency':'CAD','unit_price':'2'}]}),'ok')
            before=tracker.status()
            server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(db))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/') as r:
                    self.assertEqual(r.status,200);self.assertIn(b'Sample',r.read())
                    self.assertEqual(r.headers['Cache-Control'],'no-store')
                with urlopen(base+'/status.json') as r:
                    status=json.load(r);self.assertEqual(status['observation']['cards'][0]['name'],'Sample')
                with self.assertRaises(HTTPError) as cm:urlopen(Request(base+'/',data=b'{}',method='POST'))
                self.assertEqual(cm.exception.code,405)
                with self.assertRaises(HTTPError) as cm:urlopen(base+'/ledger')
                self.assertEqual(cm.exception.code,404)
                self.assertEqual(tracker.status()['history'],before['history'])
            finally:
                server.shutdown();server.server_close();thread.join(timeout=2)
    def test_stale_and_empty(self):
        page=render({'stale':True,'observation':None})
        self.assertIn('STALE',page)
        self.assertIn('Observed cards (0)',page)
