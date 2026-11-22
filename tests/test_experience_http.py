"""Experience web panel routes: exact local token and independent IXO write checks."""
from __future__ import annotations
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from ixo_foundation.desktop import DesktopServer
from ixo_foundation.system import Foundation

class ExperienceHttpTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.app=Foundation(Path(self.temp.name)/'state')
        self.server=DesktopServer(('127.0.0.1',0),self.app,token='local-experience-token')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.app.close()
        self.temp.cleanup()

    def req(self,path,body=None,*,token=True,origin=None):
        headers={'Content-Type':'application/json'}
        if token:headers['X-IXO-Token']='local-experience-token'
        if origin:headers['Origin']=origin
        data=None if body is None else json.dumps(body).encode()
        q=Request(self.base+path,headers=headers,data=data)
        try:
            with urlopen(q,timeout=5) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.loads(e.read())

    def test_panel_is_real_html_and_js(self):
        with urlopen(self.base+'/',timeout=5) as r:
            html=r.read()
            self.assertIn(b'panel-experience',html)
            self.assertIn(b'experience.js',html)
        with urlopen(self.base+'/experience.js',timeout=5) as r:
            self.assertIn(b'refreshExperience',r.read())

    def test_token_required_for_inspection_and_mutation(self):
        self.assertEqual(self.req('/api/experience',token=False)[0],403)
        self.assertEqual(self.req('/api/experience/action',{'action':'sync-ixo'},token=False)[0],403)
        self.assertEqual(self.req('/api/experience/action',{'action':'sync-ixo'},origin='https://other.example')[0],403)
        self.assertEqual(self.req('/api/experience')[0],200)

    def test_capture_and_independent_material_preserve_fact_boundary(self):
        self.app.ixo.moon('observe','Development work')
        c,result=self.req('/api/experience/action',{'action':'sync-ixo'},origin=self.base)
        self.assertEqual(c,200)
        self.assertEqual(result['new_exposures'],1)
        c,result=self.req('/api/experience/action',{'action':'add','content':'Independent Haven document',
                        'project':'Haven','domain':'home_tools','origin':'independent_project',
                        'source_ref':'haven/file.md'},origin=self.base)
        self.assertEqual(c,200)
        self.assertTrue(result['ok'])
        c,report=self.req('/api/experience')
        self.assertEqual(c,200)
        self.assertEqual(report['report']['ixo_development_records'],1)
        self.assertEqual(report['report']['independent_learning_records'],1)
        self.assertEqual(self.app.ixo.status(0)['counts']['facts'],0)
        self.assertEqual(self.app.aixo.state()['dsoe_evidence_count'],0)

if __name__=='__main__':unittest.main()
