import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen
from watch_dashboard import make_handler, render_trends, series_id


def snap(t, name):
    return {'collected_at': t, 'observation': {'cards': [{'game': 'MTG', 'name': name, 'set_code': 'set', 'collector_number': '1', 'currency': 'CAD', 'source': 'fixture', 'unit_price': '2'}]}}


class HistorySearchTests(unittest.TestCase):
    def test_search_reaches_series_beyond_default_forty(self):
        snapshots = [snap(t, f'Card {n:03d}') for n in range(65) for t in (1000, 1900)]
        self.assertNotIn('Card 064', render_trends(snapshots))
        html = render_trends(snapshots, search='card 064')
        self.assertIn('Card 064', html)
        self.assertEqual(html.count('<polyline'), 1)
        self.assertIn('1 matching series', html)
        self.assertNotIn('Card 063', html)

    def test_search_escapes_input_and_preserves_stable_identity(self):
        snapshots = [snap(t, 'A <script>') for t in (1000, 1900)]
        identity = series_id(('MTG','A <script>','set','1','CAD','fixture'))
        html = render_trends(snapshots, identity, '<SCRIPT>')
        self.assertIn('value="'+identity+'" selected', html)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_http_rejects_oversized_search(self):
        with tempfile.TemporaryDirectory() as d:
            server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(Path(d)/'tracker.db'))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with self.assertRaises(HTTPError) as ctx:
                    urlopen(f'http://127.0.0.1:{server.server_port}/?q='+'x'*101)
                self.assertEqual(ctx.exception.code, 400)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=2)
