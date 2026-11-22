import json
import tempfile
import unittest
from pathlib import Path
from tracker import Tracker
from watch_dashboard import make_handler
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen
from urllib.error import HTTPError

class HistoryTests(unittest.TestCase):
    def test_archive_and_pause(self):
        with tempfile.TemporaryDirectory() as td:
            now=[1000.0]
            t=Tracker(Path(td)/'t.db',clock=lambda:now[0]);t.enable(True)
            self.assertEqual(t.tick(lambda:{'cards':[{'name':'A','unit_price':'1'}]}),'ok')
            now[0]+=900
            self.assertEqual(t.tick(lambda:{'cards':[{'name':'A','unit_price':'2'}]}),'ok')
            self.assertEqual([x['observation']['cards'][0]['unit_price'] for x in t.recent_observations()],['1','2'])
            t.enable(False)
            now[0]+=900
            self.assertEqual(t.tick(lambda:{}),'paused')
            self.assertEqual(len(t.recent_observations()),2)
            self.assertEqual(t.status()['observation']['cards'][0]['unit_price'],'2')

    def test_http_history_and_bad_limit(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/'t.db';t=Tracker(db);t.enable(True);t.tick(lambda:{'mode':'fixture'})
            server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(db))
            thread=Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                with urlopen(base+'/history.json?limit=1') as r:
                    data=json.load(r)
                    self.assertEqual(len(data['snapshots']),1)
                    self.assertIn('not upstream',data['note'])
                with self.assertRaises(HTTPError) as cm:urlopen(base+'/history.json?limit=9999')
                self.assertEqual(cm.exception.code,400)
            finally:server.shutdown();server.server_close();thread.join()

    def test_legacy_latest_only_does_not_invent_archive(self):
        with tempfile.TemporaryDirectory() as td:
            t=Tracker(Path(td)/'t.db')
            with t.connect() as db:db.execute('INSERT INTO observation VALUES(1,?,?)',(100.0,'{}'))
            self.assertEqual(t.recent_observations(),[])

if __name__=='__main__':unittest.main()
