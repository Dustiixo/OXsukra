import threading
import tempfile
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from run import make_handler
from engine import World
from pathlib import Path

class ByteRoutes(unittest.TestCase):
    def test_byte_assets_from_actual_loopback_http(self):
        with tempfile.TemporaryDirectory() as d:
            world=World(Path(d)/'test.sqlite3',demo=False)
            server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(world,'test-token',0))
            server.RequestHandlerClass=make_handler(world,'test-token',server.server_port)
            runner=threading.Thread(target=server.serve_forever,daemon=True);runner.start()
            url=f'http://127.0.0.1:{server.server_port}'
            try:
                for route,fragment in [('/byte',b'BYTE WORLD'),('/byte.js',b'patchesOf'),('/byte-core.mjs',b'1000'),('/byte.css',b'.barlinks')]:
                    with urllib.request.urlopen(url+route,timeout=2) as response:
                        self.assertEqual(response.status,200)
                        self.assertIn(fragment,response.read())
                request=urllib.request.Request(url+'/api/state',headers={'Host':'attacker.invalid'})
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    urllib.request.urlopen(request,timeout=2)
                self.assertEqual(raised.exception.code,403)
            finally:
                server.shutdown();server.server_close();runner.join(timeout=3);world.close()
