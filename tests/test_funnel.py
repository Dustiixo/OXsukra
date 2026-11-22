import hashlib
import io
import json
import os
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from funnel import client as local_client
from pathlib import Path

from funnel.common import init_data,safe_name,safe_project
from funnel.hub import FunnelServer,db_open,process_one


class FunnelIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        credentials=init_data(self.root)
        self.member=credentials[0][2]
        self.other=credentials[1][2]
        self.bot=credentials[4][2]
        self.admin=credentials[5][2]
        self.server=FunnelServer('127.0.0.1',0,self.root)
        self.base='http://127.0.0.1:'+str(self.server.server_port)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def call(self,path,method='GET',body=None,token=None,raw=False):
        headers={}
        if token is not False:
            headers['Authorization']='Bearer '+(token if token is not None else self.member)
        if body is not None and not raw:
            body=json.dumps(body).encode()
            headers['Content-Type']='application/json'
        request=urllib.request.Request(self.base+path,data=body,headers=headers,method=method)
        try:
            with urllib.request.urlopen(request,timeout=8) as resp:
                if path.endswith('/download'):
                    return resp.read()
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            with exc:
                try:detail=json.load(exc)
                except Exception:detail={}
                return {'http_error':exc.code,**detail}

    def create(self,name,data,project='shared',digest=None):
        sha=digest or hashlib.sha256(data).hexdigest()
        v=self.call('/api/v1/uploads','POST',{'name':name,'size':len(data),'sha256':sha,'project':project})
        self.assertIn('upload_id',v,v)
        return v['upload_id']

    def finish(self,ident,data):
        position=0
        for block in [data[:3],data[3:]]:
            if not block:continue
            out=self.call(f'/api/v1/uploads/{ident}/chunk?offset={position}','PATCH',block,raw=True)
            self.assertIn('offset',out,out)
            position=out['offset']
        return self.call(f'/api/v1/uploads/{ident}/complete','POST',{})

    def wait_job(self,id,timeout=5):
        until=time.time()+timeout
        while time.time()<until:
            jobs=self.call('/api/v1/jobs')['jobs']
            match=[j for j in jobs if j['id']==id]
            if match and match[0]['status'] in ('done','failed'):
                return match[0]
            time.sleep(.05)
        self.fail('Job did not finish')

    def test_authorization_and_health(self):
        self.assertTrue(self.call('/health',token=False)['ok'])
        self.assertEqual(self.call('/api/v1/items',token=False)['http_error'],401)
        self.assertEqual(self.call('/api/v1/items',token='bad')['http_error'],401)
        self.assertEqual(self.call('/api/v1/jobs/missing/retry','POST',{},token=self.bot)['http_error'],403)
        self.assertEqual(self.call('/api/v1/uploads','POST',{'name':'x.txt','size':26*1024*1024,'sha256':'0'*64},token=self.bot)['http_error'],413)

    def test_resume_checksum_index_download_and_search(self):
        payload=b'# IXO\nMoon2 reflection; a traceable prototype.\n'
        ident=self.create('../architecture.md',payload,project='ixo')
        first=self.call(f'/api/v1/uploads/{ident}/chunk?offset=0','PATCH',payload[:11],raw=True)
        self.assertEqual(first['offset'],11)
        self.assertEqual(self.call(f'/api/v1/uploads/{ident}')['offset'],11)
        self.assertEqual(self.call(f'/api/v1/uploads/{ident}',token=self.other)['http_error'],403)
        collision=self.call(f'/api/v1/uploads/{ident}/chunk?offset=0','PATCH',b'bad',raw=True)
        self.assertEqual(collision['http_error'],409)
        second=self.call(f'/api/v1/uploads/{ident}/chunk?offset=11','PATCH',payload[11:],raw=True)
        self.assertEqual(second['offset'],len(payload))
        out=self.call(f'/api/v1/uploads/{ident}/complete','POST',{})
        self.assertEqual(out['status'],'queued')
        self.assertEqual(self.call(f"/api/v1/items/{out['item_id']}/download"),payload)
        job=self.wait_job(out['job_id'])
        self.assertEqual(job['status'],'done',job)
        self.assertEqual(job['mirror'],'not-configured')
        results=self.call('/api/v1/search?q=Moon2')
        self.assertEqual(len(results['items']),1)
        self.assertEqual(results['items'][0]['project'],'ixo')
        self.assertEqual(self.call('/api/v1/items')['items'][0]['name'],'architecture.md')
        self.assertEqual(self.call(f'/api/v1/uploads/{ident}/complete','POST',{})['http_error'],409)

    def test_wrong_digest_does_not_admit_file(self):
        ident=self.create('bad.txt',b'correct',digest='0'*64)
        self.call(f'/api/v1/uploads/{ident}/chunk?offset=0','PATCH',b'correct',raw=True)
        done=self.call(f'/api/v1/uploads/{ident}/complete','POST',{})
        self.assertEqual(done['http_error'],422)
        self.assertEqual(len(self.call('/api/v1/items')['items']),0)

    def test_deduplication_and_notes(self):
        data=b'Syntra and Opris cross-reference'
        first=self.finish(self.create('one.txt',data),data)
        second=self.finish(self.create('two.txt',data),data)
        self.assertNotEqual(first['item_id'],second['item_id'])
        self.assertEqual(len(list((self.root/'blobs').rglob(hashlib.sha256(data).hexdigest()))),1)
        bad=self.call('/api/v1/notes','POST',{'title':'x','body':'y','project':'shared','item_id':'missing'})
        self.assertEqual(bad['http_error'],400)
        note=self.call('/api/v1/notes','POST',{'title':'Alchemy test','body':'Different models compare evidence.','project':'ixo','item_id':first['item_id']})
        self.assertIn('note_id',note)
        req=urllib.request.Request(self.base+f"/api/v1/notes/{note['note_id']}/markdown",headers={'Authorization':'Bearer '+self.member})
        with urllib.request.urlopen(req) as response:
            exported=response.read().decode()
        self.assertIn('Alchemy test',exported)
        self.assertIn('proposed',exported)
        self.assertEqual(len(self.call('/api/v1/search?q=Alchemy')['notes']),1)
        # v0.5: private proposals cannot leave the hub via Obsidian until
        # the author submits them and an admin explicitly approves.
        req=urllib.request.Request(self.base+'/api/v1/obsidian-export',headers={'Authorization':'Bearer '+self.member})
        with urllib.request.urlopen(req) as response:
            with zipfile.ZipFile(io.BytesIO(response.read())) as archive:
                self.assertEqual(archive.namelist(),[])
        self.assertEqual(self.call(f"/api/v1/items/{first['item_id']}/share",'POST',
                                   {'visibility':'team','acknowledged':True})['visibility'],'team')
        self.assertEqual(self.call(f"/api/v1/notes/{note['note_id']}/submit",'POST',
                                   {'acknowledged':True})['state'],'submitted')
        self.assertEqual(self.call(f"/api/v1/notes/{note['note_id']}/review",'POST',
                                   {'decision':'approve'},token=self.admin)['state'],'approved')
        req=urllib.request.Request(self.base+'/api/v1/obsidian-export',headers={'Authorization':'Bearer '+self.member})
        with urllib.request.urlopen(req) as response:
            archive=response.read()
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            files=z.namelist()
            self.assertEqual(len(files),1)
            self.assertIn('Alchemy test',z.read(files[0]).decode())

    def test_completion_recovery_after_blob_move(self):
        data=b'Crash-safe transfer state'; ident=self.create('recovered.txt',data)
        self.call(f'/api/v1/uploads/{ident}/chunk?offset=0','PATCH',data,raw=True)
        digest=hashlib.sha256(data).hexdigest()
        target=self.root/'blobs'/digest[:2]/digest
        target.parent.mkdir(exist_ok=True)
        (self.root/'partials'/ident).replace(target) # Simulated crash after blob move
        result=self.call(f'/api/v1/uploads/{ident}/complete','POST',{})
        self.assertEqual(result['status'],'queued')
        self.assertEqual(self.call(f"/api/v1/items/{result['item_id']}/download"),data)

    def test_zip_never_extracts(self):
        memory=io.BytesIO()
        with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('../../evil.py','print("never run")')
            z.writestr('readme.md','hello')
        data=memory.getvalue()
        out=self.finish(self.create('incoming.zip',data),data)
        self.wait_job(out['job_id'])
        with db_open(self.root) as c:
            text=c.execute('SELECT preview FROM items WHERE id=?',(out['item_id'],)).fetchone()[0]
        self.assertIn('evil.py',text)
        self.assertFalse((self.root/'evil.py').exists())
        self.assertFalse((self.root/'partials'/'evil.py').exists())

    def test_real_client_chunking_and_bounded_local_llm_retrieval(self):
        # This runs the actual local uploader against the actual hub with a >4 MiB file.
        data=(b'ALCHEMY protocol: compare evidence, retain provenance.\n'*100000)
        src=self.root/'large-research.md'
        src.write_bytes(data)
        with patch.object(local_client,'config_get',return_value=(self.base,self.member)), \
             patch.object(local_client,'SESSIONS',self.root/'client-sessions.json'):
            receipt=local_client.upload(src,'alchemy',progress=lambda _:None)
            self.assertEqual(self.call(f"/api/v1/items/{receipt['item_id']}/download"),data)
            self.assertEqual(self.wait_job(receipt['job_id'])['status'],'done')
            self.assertEqual(local_client.read_json(self.root/'client-sessions.json'),{})

            class LocalOllama(BaseHTTPRequestHandler):
                seen=[]
                def do_POST(self):
                    body=self.rfile.read(int(self.headers['Content-Length']))
                    self.__class__.seen.append(json.loads(body))
                    result=json.dumps({'response':'Found the proposal; verify before promotion.'}).encode()
                    self.send_response(200)
                    self.send_header('Content-Type','application/json')
                    self.send_header('Content-Length',str(len(result)))
                    self.end_headers()
                    self.wfile.write(result)
                def log_message(self,*a):pass
            model_server=ThreadingHTTPServer(('127.0.0.1',0),LocalOllama)
            model_thread=threading.Thread(target=model_server.serve_forever,daemon=True)
            model_thread.start()
            try:
                with patch.dict(os.environ,{'FUNNEL_OLLAMA_URL':f'http://127.0.0.1:{model_server.server_port}/api/generate'}):
                    answer=local_client.ask('ALCHEMY','dummy-local-model',project='alchemy',progress=lambda _:None)
                self.assertIn('verify',answer['answer'])
                self.assertIn('artifact:'+receipt['item_id'],answer['sources'])
                self.assertIn(receipt['item_id'],LocalOllama.seen[-1]['prompt'])
                self.assertEqual(LocalOllama.seen[-1]['model'],'dummy-local-model')
            finally:
                model_server.shutdown()
                model_server.server_close()
                model_thread.join(timeout=2)

    def test_mocked_rclone_mirror_and_failure_visibility(self):
        from types import SimpleNamespace
        import funnel.hub as h
        self.server.stop_event.set()
        self.server.worker.join(timeout=2)
        payload=b'Safe metadata only'
        digest=hashlib.sha256(payload).hexdigest()
        dest=self.root/'blobs'/digest[:2]/digest
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(payload)
        item='a'*24;job='b'*24
        with db_open(self.root) as c:
            c.execute('INSERT INTO items(id,actor,name,project,size,sha256,created,visibility,mirror_approved) VALUES (?,?,?,?,?,?,?,?,?)',
                      (item,'dev-1','data.txt','alchemy',len(payload),digest,time.time(),'team',1))
            c.execute('INSERT INTO jobs(id,item_id,created,updated) VALUES (?,?,?,?)',(job,item,time.time(),time.time()))
        with patch.dict(os.environ,{'FUNNEL_RCLONE_REMOTE':'teamdrive:OX_Funnel'}), \
             patch.object(h.subprocess,'run',return_value=SimpleNamespace(returncode=0,stderr='')) as fake:
            self.assertTrue(h.process_one(self.root))
        args=fake.call_args.args[0]
        self.assertEqual(args[:2],['rclone','copyto'])
        self.assertEqual(args[-1],f'teamdrive:OX_Funnel/alchemy/{item}/data.txt')
        with db_open(self.root) as c:
            row=c.execute('SELECT status,mirror FROM jobs WHERE id=?',(job,)).fetchone()
        self.assertEqual(row['status'],'done')
        self.assertIn('teamdrive:',row['mirror'])
        # A remote error must be visible; the locally indexed artifact survives.
        with db_open(self.root) as c:
            c.execute("UPDATE jobs SET status='queued' WHERE id=?",(job,))
        with patch.dict(os.environ,{'FUNNEL_RCLONE_REMOTE':'teamdrive:OX_Funnel'}), \
             patch.object(h.subprocess,'run',return_value=SimpleNamespace(returncode=2,stderr='Test Drive unavailable')):
            h.process_one(self.root)
        with db_open(self.root) as c:
            row=c.execute('SELECT status,error FROM jobs WHERE id=?',(job,)).fetchone()
            preview=c.execute('SELECT preview FROM items WHERE id=?',(item,)).fetchone()[0]
        self.assertEqual(row['status'],'failed')
        self.assertIn('unavailable',row['error'])
        self.assertIn('Safe metadata only',preview)

    def test_invalid_project_and_roles(self):
        payload=b'data'
        invalid=self.call('/api/v1/uploads','POST',{'name':'file.txt','size':4,'sha256':hashlib.sha256(payload).hexdigest(),'project':'../../private'})
        self.assertEqual(invalid['http_error'],400)
        self.assertEqual(safe_name(r'c:\temp\hello.txt'),'hello.txt')
        self.assertEqual(self.call('/api/v1/jobs/missing/retry','POST',{},token=self.member)['http_error'],403)
        self.assertFalse(self.call('/api/v1/jobs/missing/retry','POST',{},token=self.admin)['queued'])


if __name__=='__main__':unittest.main()
