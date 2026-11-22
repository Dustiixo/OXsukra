import http.client
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from engine import World
from run import make_handler


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.world=World(Path(cls.temp.name)/'world.sqlite3',demo=False)
        # Need actual ephemeral port in handler's Host check
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(cls.world,'secret',0))
        cls.port=cls.server.server_address[1]
        cls.server.RequestHandlerClass=make_handler(cls.world,'secret',cls.port)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.world.close()
        cls.temp.cleanup()

    def req(self, method, route, payload=None, headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=5)
        conn.request(method,route,body=json.dumps(payload).encode() if payload is not None else None,headers=headers or {})
        response=conn.getresponse()
        data=json.loads(response.read().decode())
        status=response.status
        conn.close()
        return status,data

    def test_get_state(self):
        code,state=self.req('GET','/api/state')
        self.assertEqual(code,200)
        self.assertEqual(state['csrf_token'],'secret')

    def test_missing_csrf(self):
        code,_=self.req('POST','/api/mutate',{'op':'create','name':'Bad','reason':'Try fake','expected_revision':0},{'Content-Type':'application/json'})
        self.assertEqual(code,403)

    def test_origin_rejected(self):
        code,_=self.req('POST','/api/mutate',{'op':'create','name':'Bad','reason':'Try fake','expected_revision':0},{'Content-Type':'application/json','X-OX-Token':'secret','Origin':'https://evil.example'})
        self.assertEqual(code,403)

    def test_create_and_state(self):
        _,s=self.req('GET','/api/state')
        code,data=self.req('POST','/api/mutate',{'op':'create','name':'HTTP object','reason':'Test through local API','expected_revision':s['revision']},{'Content-Type':'application/json','X-OX-Token':'secret'})
        self.assertEqual(code,200)
        self.assertEqual(data['world']['objects'][data['result']['object_id']]['name'],'HTTP object')

if __name__=='__main__':
    unittest.main()
