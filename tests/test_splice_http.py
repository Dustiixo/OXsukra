import json
import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from engine import World
from run import make_handler
class IntegrationHTTP(unittest.TestCase):
  def test_splice_files_and_revisioned_slot_bridge(self):
    with tempfile.TemporaryDirectory() as tmp:
      world=World(Path(tmp)/'world.sqlite3',demo=False)
      server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(world,'integration-token',0))
      port=server.server_address[1]
      server.RequestHandlerClass=make_handler(world,'integration-token',port)
      thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
      try:
        conn=http.client.HTTPConnection('127.0.0.1',port)
        conn.request('GET','/splice');res=conn.getresponse();html=res.read();self.assertEqual(res.status,200);self.assertIn(b'ONE',html.upper())
        conn.request('GET','/splice-core.mjs');res=conn.getresponse();script=res.read();self.assertEqual(res.status,200);self.assertIn(b'analyzeSignalAsync',script)
        conn.request('GET','/api/state');res=conn.getresponse();state=json.loads(res.read());self.assertTrue(state['verified'])
        uid=world.create('Spatial study',reason='HTTP integration test',expected_revision=state['revision'])['object_id']
        for k,v in [('Depth',1.2),('Twist',2.),('Hue',42.),('Threshold',.33)]:
          payload={'op':'set_slot','object_id':uid,'slot_name':'rcll'+k,'slot':{'kind':'value','value':v},'reason':'Integration test mutation','expected_revision':world.state()['revision']}
          conn.request('POST','/api/mutate',body=json.dumps(payload),headers={'Content-Type':'application/json','X-OX-Token':'integration-token','Host':f'127.0.0.1:{port}'})
          res=conn.getresponse();data=json.loads(res.read());self.assertEqual(res.status,200,str(data))
        loaded=world.state();self.assertEqual(loaded['objects'][uid]['resolved']['rcllHue']['value'],42.)
        self.assertEqual(loaded['revision'],5)
        self.assertEqual(len(loaded['events']),5)
        conn.close()
      finally:
        server.shutdown();server.server_close();world.close()
