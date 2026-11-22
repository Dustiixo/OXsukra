"""Local-only IXO + AIXO process; clients access guarded command and evidence APIs."""
from __future__ import annotations
import json,secrets
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .runtime import IXORuntime,IXOError
from .bridge import capture
from aixo.engine import AIXOEngine,AIXOError
WEB=Path(__file__).resolve().parents[1]/'web'
class IXOServer(ThreadingHTTPServer):
 daemon_threads=True
 allow_reuse_address=True
 def __init__(self,address,runtime,aixo,token=None):
  self.runtime=runtime;self.aixo=aixo;self.token=token or secrets.token_urlsafe(32)
  super().__init__(address,Handler)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args):pass
 def reply(self,code,obj):
  body=json.dumps(obj,ensure_ascii=False).encode()
  self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/api/status':return self.reply(200,self.server.runtime.status())
  if path=='/api/aixo':return self.reply(200,self.server.aixo.state())
  if path=='/api/health':return self.reply(200,{'ok':True,'service':'ixo-aixo','scope':'localhost'})
  mapping={'/':'index.html','/index.html':'index.html','/app.js':'app.js','/style.css':'style.css'}
  if path not in mapping:return self.reply(404,{'error':'Not found'})
  content=(WEB/mapping[path]).read_bytes()
  kind='text/html' if mapping[path].endswith('.html') else 'text/javascript' if path.endswith('.js') else 'text/css'
  self.send_response(200);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'");self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
 def do_POST(self):
  path=urlsplit(self.path).path
  if path not in ('/api/command','/api/aixo/action'):return self.reply(404,{'error':'Not found'})
  if self.headers.get('X-IXO-Token')!=self.server.token:return self.reply(403,{'error':'Invalid local token'})
  origin=self.headers.get('Origin')
  if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'):
   return self.reply(403,{'error':'Cross-origin write rejected'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=12000:raise IXOError('Invalid request size')
   data=json.loads(self.rfile.read(size))
   if not isinstance(data,dict):raise IXOError('Expected object')
   if path=='/api/command':result=self.server.runtime.command(data.get('command'))
   else:
    action=data.get('action');a=self.server.aixo
    if action=='capture':result={'ok':True,'captured':capture(self.server.runtime,a)}
    elif action=='experiment':result=a.create_experiment(data.get('title'),data.get('question'))
    elif action=='lesson':result=a.complete_lesson(data.get('lesson'),data.get('artifact'))
    elif action=='evaluate':result=a.evaluate(data.get('experiment_id'),data.get('assertion'),data.get('expected'),self.server.runtime.status(0))
    else:raise AIXOError('Unknown action')
   return self.reply(200,result)
  except (ValueError,TypeError,KeyError,IXOError,AIXOError) as exc:return self.reply(400,{'ok':False,'error':str(exc)})
 def do_HEAD(self):self.send_error(405)
def serve(db,port=0,launch=True):
 import webbrowser
 ixo=IXORuntime(db)
 aixo=AIXOEngine(str(Path(db).with_name('aixo.sqlite3')))
 server=IXOServer(('127.0.0.1',port),ixo,aixo)
 url=f'http://127.0.0.1:{server.server_port}/?token={server.token}'
 print('IXO local application:',url,flush=True)
 if launch:webbrowser.open(url)
 try:server.serve_forever(poll_interval=.2)
 except KeyboardInterrupt:pass
 finally:server.server_close();ixo.close();aixo.close()
