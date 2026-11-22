import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from urllib.request import urlopen, Request
from urllib.error import HTTPError

from spatial_lab.export_trace import export
from spatial_lab.live_server import start

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / 'sample_output' / 'SESSION_DEMO'


def checksum_directory(root):
    h = hashlib.sha256()
    for f in sorted(root.rglob('*')):
        if f.is_file():
            h.update(str(f.relative_to(root)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


class SpatialBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.work = Path(cls.tmp.name) / 'session'
        shutil.copytree(DEMO, cls.work)
        cls.before = checksum_directory(cls.work)
        cls.server, cls.token = start(cls.work, 0)
        cls.url = f'http://127.0.0.1:{cls.server.server_address[1]}'
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def test_01_token_required_for_local_trace(self):
        with self.assertRaises(HTTPError) as e:
            urlopen(self.url+'/api/trace',timeout=3)
        self.assertEqual(e.exception.code,403)

    def test_02_proof_payload_real_verified_events(self):
        with urlopen(self.url+'/api/trace?key='+self.token,timeout=5) as res:
            self.assertEqual(res.status,200)
            self.assertEqual(res.headers.get('Access-Control-Allow-Origin'),None)
            self.assertIn('no-store',res.headers['Cache-Control'])
            data=json.loads(res.read())
        self.assertEqual(data['source_integrity'],'PASS')
        self.assertEqual(data['schema'],'ixo.flowmesh.visual-trace.v1')
        self.assertEqual(len(data['events']),72)
        self.assertEqual(len(data['findings']),15)
        self.assertEqual(checksum_directory(self.work),self.before)

    def test_03_no_arbitrary_source_file_serving(self):
        for path in ['/../flowmesh/sources.py','/private/registry.json','/sample_output/SESSION_DEMO/events.sqlite','/random.txt']:
            with self.assertRaises(HTTPError) as e:
                urlopen(self.url+path,timeout=5)
            self.assertIn(e.exception.code,(403,404))

    def test_04_no_write_endpoints(self):
        req=Request(self.url+'/api/trace?key='+self.token,data=b'attack',method='POST')
        with self.assertRaises(HTTPError) as e:
            urlopen(req,timeout=3)
        self.assertEqual(e.exception.code,405)
        self.assertEqual(checksum_directory(self.work),self.before)

    def test_05_integrity_failure_refuses_to_export(self):
        # Copy is a throwaway fixture. The original demo and installed source stay unchanged.
        with tempfile.TemporaryDirectory() as td:
            broken=Path(td)/'broken'
            shutil.copytree(DEMO,broken)
            victim=next(p for p in broken.rglob('*.md') if p.is_file())
            victim.write_bytes(victim.read_bytes()+b'\nTAMPERED')
            with self.assertRaises(Exception):
                export(broken)

    def test_06_local_entry_requires_key(self):
        with self.assertRaises(HTTPError) as e:
            urlopen(self.url+'/',timeout=3)
        self.assertEqual(e.exception.code,403)
        with urlopen(self.url+'/?key='+self.token,timeout=3) as res:
            self.assertEqual(res.status,200)
            self.assertIn(b'SPATIAL CHAMBER',res.read())


if __name__ == '__main__':
    unittest.main()
