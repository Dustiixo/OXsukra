import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from urllib.error import HTTPError
from watch_dashboard import render_trends, make_handler


def snap(t, name, price):
    return {'collected_at':t,'observation':{'cards':[{'game':'MTG','name':name,'set_code':'abc','collector_number':'1','currency':'CAD','source':'fixture','unit_price':price}]}}


class SeriesSelectionTests(unittest.TestCase):
    def test_filter_and_escaped_options(self):
        data=[snap(1000,'A<script>','1'),snap(1900,'A<script>','2'),snap(1000,'B','3'),snap(1900,'B','4')]
        all_html=render_trends(data)
        self.assertEqual(all_html.count('<polyline'),2)
        self.assertIn('&lt;script&gt;',all_html)
        self.assertNotIn('<script>',all_html)
        selected=render_trends(data,1)
        self.assertEqual(selected.count('<polyline'),1)
        self.assertIn('B /',selected)
        self.assertIn('<title>',selected)
        self.assertIn('<desc>',selected)
    def test_invalid_series_http_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(Path(d)/'tracker.db'))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                for invalid in ('-1','40','abc','999999'):
                    with self.assertRaises(HTTPError) as ctx:urlopen(base+'/?series='+invalid)
                    self.assertEqual(ctx.exception.code,400)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=2)
