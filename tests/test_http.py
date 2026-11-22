import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path
from ixo.runtime import IXORuntime
from ixo.server import IXOServer
from aixo.engine import AIXOEngine

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.runtime=IXORuntime(Path(self.tmp.name)/'db.sqlite3')
        self.aixo=AIXOEngine(Path(self.tmp.name)/'aixo.sqlite3')
        self.server=IXOServer(('127.0.0.1',0),self.runtime,self.aixo,token='test-only-token')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.runtime.close();self.aixo.close();self.tmp.cleanup()
    def get(self,path):
        c=HTTPConnection('127.0.0.1',self.server.server_port)
        c.request('GET',path);r=c.getresponse();body=r.read();status=r.status;c.close();return status,body
    def post(self,obj,token='test-only-token',origin=None):
        c=HTTPConnection('127.0.0.1',self.server.server_port)
        headers={'Content-Type':'application/json','X-IXO-Token':token}
        if origin:headers['Origin']=origin
        c.request('POST','/api/command',json.dumps(obj),headers)
        r=c.getresponse();status=r.status;body=json.loads(r.read());c.close();return status,body
    def test_html_boot(self):
        s,body=self.get('/');self.assertEqual(s,200);self.assertIn(b'IXO',body)
    def test_assets(self):
        for p in ('/app.js','/style.css'):
            with self.subTest(p=p):self.assertEqual(self.get(p)[0],200)
    def test_health(self):self.assertTrue(json.loads(self.get('/api/health')[1])['ok'])
    def test_state(self):self.assertEqual(json.loads(self.get('/api/status')[1])['active_set'],'main')
    def test_command_roundtrip(self):
        self.assertEqual(self.post({'command':'/set moon2'})[0],200)
        self.assertEqual(json.loads(self.get('/api/status')[1])['active_set'],'moon2')
    def test_reject_without_token(self):self.assertEqual(self.post({'command':'/set moon2'},token='no')[0],403)
    def test_reject_cross_origin(self):self.assertEqual(self.post({'command':'/set moon2'},origin='http://attacker.invalid')[0],403)
    def test_bad_commands_are_400(self):self.assertEqual(self.post({'command':'/unknown'})[0],400)
    def test_missing_static_404(self):self.assertEqual(self.get('/something')[0],404)

if __name__=='__main__':unittest.main()
