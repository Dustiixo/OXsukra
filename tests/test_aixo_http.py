import json,tempfile,threading,unittest
from http.client import HTTPConnection
from pathlib import Path
from aixo.engine import AIXOEngine
from ixo.runtime import IXORuntime
from ixo.server import IXOServer
class APITests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.i=IXORuntime(root/'ixo.db');self.a=AIXOEngine(root/'aixo.db')
  self.server=IXOServer(('127.0.0.1',0),self.i,self.a,token='test-token')
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.i.close();self.a.close();self.tmp.cleanup()
 def call(self,method,path,payload=None,token='test-token'):
  c=HTTPConnection('127.0.0.1',self.server.server_port)
  headers={'Content-Type':'application/json'}
  if token:headers['X-IXO-Token']=token
  c.request(method,path,json.dumps(payload) if payload else None,headers)
  r=c.getresponse();result=r.status,json.loads(r.read());c.close();return result
 def test_aixo_state(self):self.assertEqual(len(self.call('GET','/api/aixo')[1]['lessons']),11)
 def test_rejected_unauthorized(self):self.assertEqual(self.call('POST','/api/aixo/action',{'action':'capture'},token='wrong')[0],403)
 def test_capture_and_eval(self):
  self.assertEqual(self.call('POST','/api/command',{'command':'/set moon2'})[0],200)
  code,body=self.call('POST','/api/aixo/action',{'action':'capture'});self.assertEqual(code,200);self.assertEqual(body['captured'],1)
  code,body=self.call('POST','/api/aixo/action',{'action':'experiment','title':'Habitat','question':'Workspace?'});self.assertEqual(code,200)
  ex=body['experiment_id'];code,body=self.call('POST','/api/aixo/action',{'action':'evaluate','experiment_id':ex,'assertion':'active_set','expected':'moon2'})
  self.assertTrue(body['passed']);self.assertEqual(code,200)
 def test_bad_evaluation_rejected(self):
  code,_=self.call('POST','/api/aixo/action',{'action':'evaluate','experiment_id':1,'assertion':'delete facts','expected':True});self.assertEqual(code,400)
