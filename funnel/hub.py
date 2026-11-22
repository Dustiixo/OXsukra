"""OX Funnel hub: Python standard library HTTP + SQLite, no file execution."""
import hashlib
import io
from contextlib import contextmanager
import hmac
import json
import mimetypes
import os
import shutil
import sqlite3
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .common import MAX_CHUNK, MAX_JSON, MAX_FILE, safe_name, safe_project, safe_digest, short_id, json_dumps, sha256_file
from .ui import HTML
from .purpose_ui import extend_ui
from .automation import capability_catalog, DISCLOSURE, DISCLOSURE_VERSION, event_types, route_preview, validate_explicit_event
from .purpose import CONTRACT as PURPOSE_CONTRACT, create_schema as create_purpose_schema, taxonomy, classify, request_data, approved_rule_term

SCHEMA = '''
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS uploads(id TEXT PRIMARY KEY, actor TEXT, name TEXT, project TEXT, size INTEGER, sha256 TEXT, offset INTEGER DEFAULT 0, state TEXT DEFAULT 'open', annotation TEXT DEFAULT '', created REAL);
CREATE TABLE IF NOT EXISTS items(id TEXT PRIMARY KEY, actor TEXT, name TEXT, project TEXT, size INTEGER, sha256 TEXT, annotation TEXT DEFAULT '', created REAL, preview TEXT DEFAULT '');
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, item_id TEXT, status TEXT DEFAULT 'queued', error TEXT DEFAULT '', mirror TEXT DEFAULT '', created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS notes(id TEXT PRIMARY KEY, author TEXT, title TEXT, body TEXT, project TEXT, item_id TEXT DEFAULT '', state TEXT DEFAULT 'proposed', created REAL);
CREATE TABLE IF NOT EXISTS automation_events(id TEXT PRIMARY KEY, actor TEXT NOT NULL, event_type TEXT NOT NULL, project TEXT NOT NULL, summary TEXT NOT NULL, disclosure_version TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'recorded_unexecuted', created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS audit_events(id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, subject_type TEXT NOT NULL, subject_id TEXT NOT NULL, details TEXT NOT NULL DEFAULT '{}', created REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_automation_events_created ON automation_events(created);
CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created);
CREATE INDEX IF NOT EXISTS idx_items_project ON items(project,created);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status,created);
'''


@contextmanager
def db_open(root):
    con = sqlite3.connect(str(Path(root) / 'funnel.sqlite3'), timeout=15, isolation_level=None)
    try:
        con.row_factory = sqlite3.Row
        con.execute('PRAGMA busy_timeout=15000')
        with con:
            yield con
    finally:
        con.close()


def setup_db(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for folder in ('partials', 'blobs'):
        (root / folder).mkdir(parents=True, exist_ok=True)
    with db_open(root) as c:
        c.executescript(SCHEMA)
        create_purpose_schema(c)
        # v0.5 migration: existing shared-by-default prototype data becomes private.
        for table, column, definition in (
            ('items', 'visibility', "TEXT NOT NULL DEFAULT 'private'"),
            ('items', 'mirror_approved', 'INTEGER NOT NULL DEFAULT 0'),
            ('notes', 'visibility', "TEXT NOT NULL DEFAULT 'private'"),
        ):
            present = {r['name'] for r in c.execute(f'PRAGMA table_info({table})')}
            if column not in present:
                c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
        # Can work without FTS5; search falls back to simple SQL in this prototype.


def can_read(principal, row, *, note=False):
    """Private by default; bots never obtain ambient team read access."""
    if principal['role'] == 'admin' or row['actor' if not note else 'author'] == principal['name']:
        return True
    return (principal['role'] == 'member' and row['visibility'] == 'team'
            and (not note or row['state'] == 'approved'))


def visibility_where(principal, prefix='', *, note=False):
    """SQL fragment + parameter tuple matching can_read for collection queries."""
    name = 'author' if note else 'actor'
    p = prefix + '.' if prefix else ''
    if principal['role'] == 'admin':
        return '1=1', ()
    if principal['role'] == 'bot':
        return f'{p}{name}=?', (principal['name'],)
    if note:
        return f"({p}{name}=? OR ({p}visibility='team' AND {p}state='approved'))", (principal['name'],)
    return f"({p}{name}=? OR {p}visibility='team')", (principal['name'],)


def audit(c, actor, action, subject_type, subject_id, details=None):
    c.execute('INSERT INTO audit_events VALUES (?,?,?,?,?,?,?)',
              (short_id(), actor, action, subject_type, subject_id,
               json.dumps(details or {}, sort_keys=True), now()))


def dict_row(row):
    return dict(row) if row is not None else None


def now():
    return round(time.time(), 3)


def blob_path(root, digest):
    if not safe_digest(digest):
        raise ValueError('Invalid SHA256')
    return Path(root) / 'blobs' / digest[:2] / digest


def blob_preview(path, name):
    ext = Path(name).suffix.lower()
    text_exts = {'.txt', '.md', '.rst', '.py', '.json', '.yaml', '.yml', '.toml', '.js', '.ts', '.css', '.html', '.xml', '.csv', '.ini', '.sh', '.bat', '.ps1'}
    if ext in text_exts:
        with open(path, 'rb') as f:
            buf = f.read(64 * 1024)
        if b'\x00' in buf:
            return 'Binary content, not indexed'
        return buf.decode('utf-8', errors='replace')[:32000]
    if ext == '.zip':
        # ZIP metadata only; no extraction, decompression or execution.
        try:
            with zipfile.ZipFile(path) as z:
                names = [safe_name(n) for n in z.namelist()[:200]]
                return f'ZIP archive containing {len(z.infolist())} entries (first 200 names):\n' + '\n'.join(names)
        except (zipfile.BadZipFile, OSError, ValueError):
            return 'ZIP archive could not be inspected'
    return f'Binary or unsupported preview: {name}'


def discord_event(message):
    url = os.environ.get('FUNNEL_DISCORD_WEBHOOK_URL', '').strip()
    if not url:
        return
    payload = json_dumps({'content': message[:1800], 'allowed_mentions': {'parse': []}})
    req = urllib.request.Request(url, payload, {'Content-Type':'application/json', 'User-Agent':'OX-Funnel/0.2'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=7) as response:
            response.read()
    except Exception as exc:
        print(f'[webhook warning] {type(exc).__name__}: {exc}', flush=True)


def process_one(root):
    """Claim one job atomically; no external code execution except configured rclone executable."""
    root = Path(root)
    with db_open(root) as c:
        c.execute('BEGIN IMMEDIATE')
        row = c.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
        if not row:
            c.execute('COMMIT')
            return False
        job_id = row['id']
        c.execute("UPDATE jobs SET status='processing', updated=? WHERE id=?", (now(), job_id))
        c.execute('COMMIT')
    try:
        with db_open(root) as c:
            item = c.execute('SELECT * FROM items WHERE id=?', (row['item_id'],)).fetchone()
        if not item:
            raise RuntimeError('Missing item record')
        blob = blob_path(root, item['sha256'])
        if not blob.exists() or sha256_file(blob) != item['sha256']:
            raise RuntimeError('Missing or modified blob, SHA256 check failed')
        preview = blob_preview(blob, item['name'])
        # Index safely before external mirroring; Drive outages do not erase local search.
        with db_open(root) as c:
            c.execute('UPDATE items SET preview=? WHERE id=?', (preview, item['id']))
        mirror_result = 'not-configured'
        remote = os.getenv('FUNNEL_RCLONE_REMOTE', '').strip()
        if remote and item['visibility'] == 'team' and item['mirror_approved']:
            if not remote.endswith(':') and ':' not in remote:
                raise RuntimeError('FUNNEL_RCLONE_REMOTE needs a named rclone remote, e.g. teamdrive:OX_Funnel')
            remote_path = remote.rstrip('/') + '/' + item['project'] + '/' + item['id'] + '/' + item['name']
            # Never shell=True; payload content is never run. rclone itself must be trusted.
            outcome = subprocess.run(['rclone', 'copyto', str(blob), remote_path], text=True,
                                     capture_output=True, timeout=3600, check=False)
            if outcome.returncode:
                raise RuntimeError('rclone copyto failed: ' + (outcome.stderr or '')[-400:])
            mirror_result = remote_path
        elif remote:
            mirror_result = 'not-authorized'
        with db_open(root) as c:
            c.execute("UPDATE jobs SET status='done',mirror=?,error='',updated=? WHERE id=?", (mirror_result, now(), job_id))
        if item['visibility'] == 'team':
            discord_event(f"OX Funnel processed approved team item `{item['id']}`. Job `{job_id}`.")
    except Exception as exc:
        with db_open(root) as c:
            c.execute("UPDATE jobs SET status='failed',error=?,updated=? WHERE id=?", (str(exc)[:1000],now(),job_id))
        # Failures are only shown in the authenticated queue to avoid external data leaks.
    return True


def worker_loop(root, stop_event):
    # Recover a job interrupted by process crash.
    with db_open(root) as c:
        c.execute("UPDATE jobs SET status='queued', updated=? WHERE status='processing'", (now(),))
    while not stop_event.is_set():
        if not process_one(root):
            stop_event.wait(0.5)


class FunnelHandler(BaseHTTPRequestHandler):
    server_version = 'OXFunnel/0.5'
    protocol_version = 'HTTP/1.1'

    def log_message(self, fmt, *args):
        # Do not log Authorization header/token contents.
        print('%s - %s' % (self.address_string(), fmt % args), flush=True)

    def send_bytes(self, code, payload, mime='application/json'):
        self.send_response(code)
        self.send_header('Content-Type', mime + ('; charset=utf-8' if mime.startswith('text/') else ''))
        self.send_header('Cache-Control','no-store')
        self.send_header('Connection','close')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Length',str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def reply(self, code, obj):
        self.send_bytes(code, json_dumps(obj))

    def fail(self, code, error):
        self.reply(code, {'error':error})

    def body(self, max_len=MAX_JSON):
        try:
            count=int(self.headers.get('Content-Length','-1'))
        except ValueError:
            raise ValueError('Missing/invalid Content-Length')
        if count < 0 or count > max_len:
            raise ValueError('Body too large or invalid Content-Length')
        raw=self.rfile.read(count)
        if len(raw)!=count:
            raise ValueError('Incomplete request body')
        return raw

    def json_body(self):
        result=json.loads(self.body())
        if not isinstance(result, dict):
            raise ValueError('Expected JSON object')
        return result

    def principal(self):
        header=self.headers.get('Authorization','')
        if not header.startswith('Bearer '):
            return None
        token=header[7:].strip()
        if len(token)>200:
            return None
        digest=hashlib.sha256(token.encode('utf-8')).hexdigest()
        # Authenticate digest keys without disclosing any token data.
        for key, value in self.server.auth.items():
            if hmac.compare_digest(key,digest):
                return value
        return None

    def handle_route(self, method):
        parsed=urllib.parse.urlsplit(self.path)
        path=parsed.path.rstrip('/') or '/'
        qs=urllib.parse.parse_qs(parsed.query)
        if method=='GET' and path in ('/','/ui'):
            return self.send_bytes(200,extend_ui(HTML).encode(), 'text/html')
        if method=='GET' and path=='/health':
            return self.reply(200, {'ok':True,'name':'OX Funnel','version':'0.5.0'})
        actor=self.principal()
        if not actor:
            return self.fail(401,'Bearer authorization required')
        root=self.server.root
        role=actor['role']
        if method in ('POST','PATCH') and role=='bot' and not (path in ('/api/v1/notes','/api/v1/automation/preview','/api/v1/route/preview') or path.startswith('/api/v1/uploads')):
            return self.fail(403,'Bot token can only ingest authorized attachments or propose notes')
        if method=='GET' and path=='/api/v1/purposes':
            with db_open(root) as c:
                purposes=taxonomy(c)
            return self.reply(200,{'contract':PURPOSE_CONTRACT,'purposes':purposes,
                                  'disclaimer':'Labels are NOT access controls or Discord categories'})
        if method=='POST' and path=='/api/v1/route/preview':
            data=self.json_body()
            with db_open(root) as c:
                result=classify(c,data.get('name',''),data.get('description',''),data.get('project','shared'))
            return self.reply(200,result)
        if method=='GET' and path=='/api/v1/purpose-requests':
            if role=='bot':
                return self.fail(403,'Bot cannot browse team requests')
            with db_open(root) as c:
                if role=='admin':
                    rows=c.execute('SELECT * FROM purpose_requests ORDER BY created DESC LIMIT 150').fetchall()
                else:
                    rows=c.execute('SELECT * FROM purpose_requests WHERE actor=? ORDER BY created DESC LIMIT 150',
                                   (actor['name'],)).fetchall()
            return self.reply(200,{'contract':PURPOSE_CONTRACT,'requests':[
                {**dict_row(r),'keywords':json.loads(r['keywords'])} for r in rows]})
        if method=='POST' and path=='/api/v1/purpose-requests':
            data=self.json_body()
            kind,title,reason,slug,terms,item_id=request_data(data)
            with db_open(root) as c:
                if item_id:
                    linked=c.execute('SELECT * FROM items WHERE id=?',(item_id,)).fetchone()
                    if not linked or not can_read(actor,linked):
                        return self.fail(404,'Referenced item not found')
                if kind=='new_purpose' and c.execute('SELECT 1 FROM purposes WHERE slug=?',(slug,)).fetchone():
                    return self.fail(409,'Purpose already exists')
                ticket=short_id()
                c.execute('INSERT INTO purpose_requests(id,kind,actor,title,reason,proposed_slug,keywords,item_id,status,created) VALUES(?,?,?,?,?,?,?,?,?,?)',
                          (ticket,kind,actor['name'],title,reason,slug,json.dumps(terms),item_id,'open',now()))
                audit(c,actor['name'],'purpose.request','purpose_request',ticket)
            return self.reply(201,{'request_id':ticket,'status':'open','executed':False,
                                   'note':'No category, file transfer, or Discord channel was created'})
        match=path.split('/')
        if method=='POST' and len(match)==6 and match[:4]==['','api','v1','purpose-requests'] and match[5]=='resolve':
            if role!='admin':
                return self.fail(403,'Admin approval required')
            data=self.json_body()
            decision=data.get('decision')
            if decision not in ('approve','reject'):
                return self.fail(400,'decision must be approve or reject')
            with db_open(root) as c:
                c.execute('BEGIN IMMEDIATE')
                ticket=c.execute('SELECT * FROM purpose_requests WHERE id=?',(match[4],)).fetchone()
                if not ticket:
                    return self.fail(404,'Request not found')
                if ticket['status']!='open':
                    return self.fail(409,'Request already resolved')
                if decision=='approve' and ticket['kind']=='new_purpose':
                    if c.execute('SELECT 1 FROM purposes WHERE slug=?',(ticket['proposed_slug'],)).fetchone():
                        return self.fail(409,'Purpose already exists')
                    terms=json.loads(ticket['keywords'])
                    # Never turn a new purpose into privileged or confidential storage.
                    sensitive={'business','invoice','contract','revenue','budget','payroll'}
                    restricted=int(bool(sensitive.intersection(terms)))
                    c.execute('INSERT INTO purposes(slug,title,description,channel_hint,restricted,created_by,created) VALUES(?,?,?,?,?,?,?)',
                              (ticket['proposed_slug'],ticket['title'],ticket['reason'],'#file-drop',restricted,actor['name'],now()))
                    for term in terms:
                        c.execute('INSERT INTO purpose_rules VALUES(?,?,?,?,?,?)',
                                  (short_id(),ticket['proposed_slug'],term,5,actor['name'],now()))
                new_status='approved' if decision=='approve' else 'rejected'
                c.execute('UPDATE purpose_requests SET status=?,resolved_by=?,resolved=? WHERE id=?',
                          (new_status,actor['name'],now(),match[4]))
                audit(c,actor['name'],'purpose.resolve','purpose_request',match[4],{'decision':decision})
            return self.reply(200,{'request_id':match[4],'status':new_status,'discord_action':'none',
                                   'storage_action':'none'})
        if method=='POST' and len(match)==6 and match[:4]==['','api','v1','items'] and match[5]=='purpose':
            if role!='admin':
                return self.fail(403,'Admin approval required')
            data=self.json_body()
            slug=safe_project(data.get('purpose',''))
            term=data.get('learn_term','')
            if term:
                term=approved_rule_term(term)
            with db_open(root) as c:
                c.execute('BEGIN IMMEDIATE')
                item=c.execute('SELECT id FROM items WHERE id=?',(match[4],)).fetchone()
                purpose=c.execute('SELECT * FROM purposes WHERE slug=?',(slug,)).fetchone()
                if not item or not purpose:
                    return self.fail(404,'Artifact or purpose not found')
                if purpose['restricted']:
                    return self.fail(403,'Restricted purposes require a separate protected hub')
                c.execute("UPDATE items SET purpose_slug=?,route_state='approved_by_admin' WHERE id=?",(slug,match[4]))
                if term:
                    c.execute('INSERT OR IGNORE INTO purpose_rules VALUES(?,?,?,?,?,?)',
                              (short_id(),slug,term,5,actor['name'],now()))
                c.execute('INSERT INTO purpose_events VALUES(?,?,?,?,?,?,?)',
                          (short_id(),match[4],actor['name'],slug,'approved_by_admin',
                           json.dumps({'learn_term':term}),now()))
                audit(c,actor['name'],'purpose.correct','item',match[4],{'purpose':slug})
                c.execute("UPDATE purpose_requests SET status='resolved' WHERE item_id=? AND status='open' AND kind='triage'",(match[4],))
            return self.reply(200,{'item_id':match[4],'purpose':slug,'status':'approved_by_admin',
                                   'trained_term':term,'discord_action':'none'})
        # HERMES automation control plane: inspection + durable metadata-only proposals.
        # No callable side effects or third-party bot access from this interface.
        if method=='GET' and path=='/api/v1/integrations':
            return self.reply(200, capability_catalog())
        if method=='GET' and path=='/api/v1/disclosure':
            return self.reply(200, DISCLOSURE)
        if method=='GET' and path=='/api/v1/automation/types':
            return self.reply(200, {'types':event_types(),'execution':'none'})
        if method=='POST' and path=='/api/v1/automation/preview':
            data=self.json_body()
            return self.reply(200, route_preview(data.get('event_type')))
        if method=='GET' and path=='/api/v1/automation/events':
            if role=='bot':
                return self.fail(403,'Bot role cannot list other members automation events')
            limit=min(max(int(qs.get('limit',['50'])[0]),1),100)
            with db_open(root) as c:
                if role=='admin':
                    rows=c.execute('SELECT * FROM automation_events ORDER BY created DESC LIMIT ?',(limit,)).fetchall()
                else:
                    rows=c.execute('SELECT * FROM automation_events WHERE actor=? ORDER BY created DESC LIMIT ?',
                                   (actor['name'],limit)).fetchall()
            return self.reply(200, {'events':[dict_row(r) for r in rows]})
        if method=='POST' and path=='/api/v1/automation/events':
            # v0.2 event recording, NOT dispatching, and explicit disclosure required.
            try:
                data=self.json_body()
                event_type,summary=validate_explicit_event(data)
            except PermissionError as exc:
                return self.fail(412,str(exc))
            project=safe_project(data.get('project','shared'))
            eid=short_id()
            with db_open(root) as c:
                c.execute('INSERT INTO automation_events(id,actor,event_type,project,summary,disclosure_version,created) VALUES(?,?,?,?,?,?,?)',
                          (eid,actor['name'],event_type,project,summary,DISCLOSURE_VERSION,now()))
            return self.reply(201, {'event_id':eid,'state':'recorded_unexecuted','preview':route_preview(event_type)})
        if method=='GET' and path=='/api/v1/status':
            visible,params=visibility_where(actor)
            note_visible,nparams=visibility_where(actor,note=True)
            with db_open(root) as c:
                items=c.execute(f'SELECT count(*) FROM items WHERE {visible}',params).fetchone()[0]
                jobs={r['status']:r['c'] for r in c.execute(
                    f'SELECT j.status,count(*) c FROM jobs j JOIN items i ON i.id=j.item_id WHERE {visibility_where(actor,"i")[0]} GROUP BY j.status',params)}
                notes=c.execute(f'SELECT count(*) FROM notes WHERE {note_visible}',nparams).fetchone()[0]
            return self.reply(200,{'items':items,'jobs':jobs,'notes':notes,'mirror_enabled':bool(os.getenv('FUNNEL_RCLONE_REMOTE')),
                                   'actor':actor['name'],'role':role})
        if method=='POST' and path=='/api/v1/uploads':
            data=self.json_body()
            name=safe_name(data['name'])
            project=safe_project(data.get('project','shared'))
            size=data['size']
            digest=data['sha256']
            if type(size) is not int or not (0<=size<=MAX_FILE) or not safe_digest(digest):
                return self.fail(400,'Invalid size or SHA256')
            if role=='bot' and size>25*1024*1024:
                return self.fail(413,'Discord bot intake limit is 25 MiB')
            annotation=str(data.get('annotation',''))[:5000]
            with db_open(root) as c:
                preview=classify(c,name,'',project)
            if preview['decision']=='restricted':
                return self.fail(403,'This filename/project appears business-sensitive: use a separately protected hub')
            ident=short_id()
            with db_open(root) as c:
                c.execute('INSERT INTO uploads(id,actor,name,project,size,sha256,annotation,created) VALUES (?,?,?,?,?,?,?,?)',
                          (ident,actor['name'],name,project,size,digest,annotation,now()))
            (root/'partials'/ident).touch(exist_ok=False)
            return self.reply(201,{'upload_id':ident,'offset':0,'max_chunk':MAX_CHUNK})
        up_match=path.split('/')
        if len(up_match)>=5 and up_match[:4]==['','api','v1','uploads']:
            upload_id=up_match[4]
            with db_open(root) as c:
                upload=c.execute('SELECT * FROM uploads WHERE id=?',(upload_id,)).fetchone()
            if not upload:
                return self.fail(404,'Upload not found')
            if role!='admin' and upload['actor']!=actor['name']:
                return self.fail(403,'Only uploader or admin can resume/complete upload')
            partial=root/'partials'/upload_id
            if method=='GET' and len(up_match)==5:
                offset=partial.stat().st_size if partial.exists() else upload['offset']
                return self.reply(200,{'upload_id':upload_id,'offset':offset,'size':upload['size'],'state':upload['state']})
            if method=='PATCH' and len(up_match)==6 and up_match[5]=='chunk':
                if upload['state']!='open':
                    return self.fail(409,'Upload already completed')
                expected=int(qs.get('offset',['-1'])[0])
                data=self.body(MAX_CHUNK)
                with self.server.upload_lock:
                    current=partial.stat().st_size
                    if expected!=current:
                        return self.reply(409,{'error':'Offset conflict','offset':current})
                    if current+len(data)>upload['size'] or len(data)==0:
                        return self.fail(400,'Chunk exceeds declared size or is empty')
                    with open(partial,'ab') as f:
                        f.write(data)
                        f.flush()
                        os.fsync(f.fileno())
                    with db_open(root) as c:
                        c.execute('UPDATE uploads SET offset=? WHERE id=?',(current+len(data),upload_id))
                return self.reply(200,{'upload_id':upload_id,'offset':current+len(data)})
            if method=='POST' and len(up_match)==6 and up_match[5]=='complete':
                if upload['state']!='open':
                    return self.fail(409,'Upload already completed')
                with self.server.upload_lock:
                    target=blob_path(root,upload['sha256'])
                    if partial.exists():
                        if partial.stat().st_size!=upload['size']:
                            return self.fail(409,'Upload incomplete')
                        calculated=sha256_file(partial)
                        if calculated!=upload['sha256']:
                            return self.fail(422,'SHA256 mismatch; upload not admitted')
                        target.parent.mkdir(exist_ok=True)
                        if target.exists():
                            if sha256_file(target)!=calculated:
                                return self.fail(500,'Corrupt existing hash-addressed blob')
                            partial.unlink()
                        else:
                            os.replace(partial,target)
                    elif target.is_file() and target.stat().st_size==upload['size'] and sha256_file(target)==upload['sha256']:
                        # Crash recovery: a previous completion moved the blob before its DB commit.
                        calculated=upload['sha256']
                    else:
                        return self.fail(409,'Upload partial missing or incomplete')
                    item_id=short_id()
                    job_id=short_id()
                    with db_open(root) as c:
                        c.execute('BEGIN IMMEDIATE')
                        plan=classify(c,upload['name'],'',upload['project'])
                        purpose=plan['purpose'] if plan['decision']=='suggested' else 'dump_inbox'
                        route_state='provisional' if plan['decision']=='suggested' else 'needs_review'
                        c.execute('INSERT INTO items(id,actor,name,project,size,sha256,annotation,created,purpose_slug,route_state) VALUES (?,?,?,?,?,?,?,?,?,?)',
                                  (item_id, upload['actor'],upload['name'],upload['project'],upload['size'],calculated,upload['annotation'],now(),purpose,route_state))
                        c.execute('INSERT INTO jobs(id,item_id,created,updated) VALUES (?,?,?,?)',(job_id,item_id,now(),now()))
                        c.execute('INSERT INTO purpose_events VALUES(?,?,?,?,?,?,?)',
                                  (short_id(),item_id,'system-rule-engine',purpose,route_state,
                                   json.dumps(plan,sort_keys=True),now()))
                        audit(c,upload['actor'],'item.received','item',item_id,
                              {'sha256':calculated,'purpose':purpose,'visibility':'private'})
                        if route_state=='needs_review':
                            c.execute('INSERT INTO purpose_requests(id,kind,actor,title,reason,proposed_slug,keywords,item_id,status,created) VALUES(?,?,?,?,?,?,?,?,?,?)',
                                      (short_id(),'triage',upload['actor'],upload['name'],
                                       'Automatic metadata classification could not choose a purpose',
                                       '', '[]',item_id,'open',now()))
                        c.execute("UPDATE uploads SET state='complete',offset=? WHERE id=?",(upload['size'],upload_id))
                        c.execute('COMMIT')
                # All newly ingested files are private. No outbound Discord event.
                return self.reply(201,{'item_id':item_id,'job_id':job_id,'sha256':calculated,'status':'queued',
                                       'purpose':purpose,'route_state':route_state,'visibility':'private'})
        if method=='POST' and len(up_match)==6 and up_match[:4]==['','api','v1','items'] and up_match[5]=='share':
            data=self.json_body()
            desired=data.get('visibility')
            if desired not in ('private','team'):
                return self.fail(400,'visibility must be private or team')
            with db_open(root) as c:
                c.execute('BEGIN IMMEDIATE')
                item=c.execute('SELECT * FROM items WHERE id=?',(up_match[4],)).fetchone()
                if not item or (item['actor']!=actor['name'] and role!='admin'):
                    return self.fail(404,'Item not found or not owned')
                if desired=='team' and (item['actor']!=actor['name'] or data.get('acknowledged') is not True):
                    return self.fail(412,'Owner must explicitly acknowledge team sharing')
                if desired=='private' and item['mirror_approved']:
                    return self.fail(409,'External mirror was authorized; remove remote copies before revoking team access')
                c.execute('UPDATE items SET visibility=? WHERE id=?',(desired,up_match[4]))
                audit(c,actor['name'],'item.visibility','item',up_match[4],{'from':item['visibility'],'to':desired})
            if desired=='team' and item['visibility']!='team':
                discord_event(f"OX Funnel: item `{up_match[4]}` was explicitly shared with the team.")
            return self.reply(200,{'item_id':up_match[4],'visibility':desired,
                                   'mirror_authorized':bool(item['mirror_approved'])})
        if method=='POST' and len(up_match)==6 and up_match[:4]==['','api','v1','items'] and up_match[5]=='authorize-mirror':
            data=self.json_body()
            if data.get('acknowledged') is not True:
                return self.fail(412,'Explicit remote-storage consent required')
            with db_open(root) as c:
                c.execute('BEGIN IMMEDIATE')
                item=c.execute('SELECT * FROM items WHERE id=?',(up_match[4],)).fetchone()
                if not item or item['actor']!=actor['name']:
                    return self.fail(404,'Only owner can authorize mirror')
                if item['visibility']!='team':
                    return self.fail(409,'Share item with the team before authorizing remote mirror')
                if not item['mirror_approved']:
                    c.execute('UPDATE items SET mirror_approved=1 WHERE id=?',(up_match[4],))
                    if not c.execute("SELECT 1 FROM jobs WHERE item_id=? AND status IN ('queued','processing')",(up_match[4],)).fetchone():
                        c.execute('INSERT INTO jobs(id,item_id,created,updated) VALUES (?,?,?,?)',
                                  (short_id(),up_match[4],now(),now()))
                    audit(c,actor['name'],'item.mirror_authorized','item',up_match[4])
            return self.reply(200,{'item_id':up_match[4],'mirror_authorized':True,
                                   'note':'Worker will mirror only if FUNNEL_RCLONE_REMOTE is configured'})
        if method=='GET' and path=='/api/v1/audit':
            if role!='admin':
                return self.fail(403,'Admin audit access required')
            limit=min(max(int(qs.get('limit',['100'])[0]),1),300)
            with db_open(root) as c:
                rows=c.execute('SELECT * FROM audit_events ORDER BY created DESC LIMIT ?',(limit,)).fetchall()
            return self.reply(200,{'events':[dict_row(r) for r in rows]})
        if method=='GET' and path=='/api/v1/items':
            limit=min(max(int(qs.get('limit',['50'])[0]),1),200)
            requested=qs.get('purpose',[''])[0]
            where,params=visibility_where(actor)
            with db_open(root) as c:
                if requested:
                    rows=c.execute(f'SELECT id,actor,name,project,size,sha256,annotation,created,purpose_slug,route_state,visibility FROM items WHERE {where} AND purpose_slug=? ORDER BY created DESC LIMIT ?',(*params,safe_project(requested),limit)).fetchall()
                else:
                    rows=c.execute(f'SELECT id,actor,name,project,size,sha256,annotation,created,purpose_slug,route_state,visibility FROM items WHERE {where} ORDER BY created DESC LIMIT ?',(*params,limit)).fetchall()
            return self.reply(200,{'items':[dict_row(r) for r in rows]})
        if method=='GET' and len(up_match)==5 and up_match[:4]==['','api','v1','items']:
            with db_open(root) as c:
                item=c.execute('SELECT * FROM items WHERE id=?',(up_match[4],)).fetchone()
            if not item or not can_read(actor,item):
                return self.fail(404,'Item not found')
            return self.reply(200,{'item':dict_row(item)})
        if method=='GET' and len(up_match)==6 and up_match[:4]==['','api','v1','items'] and up_match[5]=='download':
            with db_open(root) as c:
                item=c.execute('SELECT * FROM items WHERE id=?',(up_match[4],)).fetchone()
            if not item or not can_read(actor,item):
                return self.fail(404,'Item not found')
            blob=blob_path(root,item['sha256'])
            if not blob.is_file():
                return self.fail(404,'Blob missing')
            self.send_response(200)
            self.send_header('Content-Type','application/octet-stream')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Connection','close')
            self.send_header('Content-Disposition',f'attachment; filename="{item["id"]}.bin"')
            self.send_header('Content-Length',str(blob.stat().st_size))
            self.end_headers()
            with open(blob,'rb') as f:
                shutil.copyfileobj(f,self.wfile,length=1024*1024)
            return
        if method=='GET' and path=='/api/v1/jobs':
            limit=min(max(int(qs.get('limit',['50'])[0]),1),200)
            where,params=visibility_where(actor,'i')
            with db_open(root) as c:
                rows=c.execute(f'''SELECT j.*,i.name,i.project,i.actor FROM jobs j JOIN items i ON i.id=j.item_id WHERE {where} ORDER BY j.created DESC LIMIT ?''',(*params,limit)).fetchall()
            return self.reply(200,{'jobs':[dict_row(r) for r in rows]})
        if method=='POST' and len(up_match)==6 and up_match[:4]==['','api','v1','jobs'] and up_match[5]=='retry':
            if role!='admin':
                return self.fail(403,'Admin token required')
            with db_open(root) as c:
                update=c.execute("UPDATE jobs SET status='queued',error='',updated=? WHERE id=? AND status='failed'",(now(),up_match[4]))
            return self.reply(200,{'queued':update.rowcount==1})
        if method=='GET' and path=='/api/v1/search':
            query=qs.get('q',[''])[0].strip()[:100]
            if not query:
                return self.reply(200,{'items':[],'notes':[]})
            term='%'+query.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')+'%'
            item_where,iparams=visibility_where(actor)
            note_where,nparams=visibility_where(actor,note=True)
            with db_open(root) as c:
                items=c.execute(f"SELECT id,name,project,actor,created FROM items WHERE ({item_where}) AND (name LIKE ? ESCAPE '\\' OR annotation LIKE ? ESCAPE '\\' OR preview LIKE ? ESCAPE '\\') ORDER BY created DESC LIMIT 40",(*iparams,term,term,term)).fetchall()
                notes=c.execute(f"SELECT id,title,project,state,created FROM notes WHERE ({note_where}) AND (title LIKE ? ESCAPE '\\' OR body LIKE ? ESCAPE '\\') ORDER BY created DESC LIMIT 40",(*nparams,term,term)).fetchall()
            return self.reply(200,{'items':[dict_row(r) for r in items],'notes':[dict_row(r) for r in notes]})
        if method=='GET' and path=='/api/v1/obsidian-export':
            note_where,params=visibility_where(actor,note=True)
            with db_open(root) as c:
                notes=c.execute(f"SELECT * FROM notes WHERE ({note_where}) AND state='approved' ORDER BY created DESC LIMIT 1000",params).fetchall()
            stream=io.BytesIO()
            with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
                for n in notes:
                    yaml=lambda v:json.dumps(str(v),ensure_ascii=False)
                    doc=(f'---\nid: {yaml(n["id"])}\nproject: {yaml(n["project"])}\n'
                         f'author: {yaml(n["author"])}\nstate: {yaml(n["state"])}\n'
                         f'artifact_id: {yaml(n["item_id"])}\n---\n\n# {n["title"]}\n\n{n["body"]}\n')
                    bundle.writestr(f'{n["project"]}/{n["id"]}.md',doc)
            return self.send_bytes(200,stream.getvalue(),'application/zip')
        if method=='GET' and path=='/api/v1/notes':
            note_where,params=visibility_where(actor,note=True)
            with db_open(root) as c:
                rows=c.execute(f'SELECT * FROM notes WHERE {note_where} ORDER BY created DESC LIMIT 100',params).fetchall()
            return self.reply(200,{'notes':[dict_row(r) for r in rows]})
        if method=='POST' and path=='/api/v1/notes':
            data=self.json_body()
            title=str(data.get('title','')).strip()[:160]
            body=str(data.get('body','')).strip()[:10000]
            project=safe_project(data.get('project','shared'))
            if not title or not body:
                return self.fail(400,'Note requires title and body')
            item_id=str(data.get('item_id',''))[:60]
            if item_id:
                with db_open(root) as c:
                    linked=c.execute('SELECT * FROM items WHERE id=?',(item_id,)).fetchone()
                    if not linked or not can_read(actor,linked):
                        return self.fail(400,'Referenced item not found or not visible')
            nid=short_id()
            with db_open(root) as c:
                c.execute('INSERT INTO notes(id,author,title,body,project,item_id,created) VALUES (?,?,?,?,?,?,?)',
                          (nid,actor['name'],title,body,project,item_id,now()))
                audit(c,actor['name'],'note.create','note',nid)
            return self.reply(201,{'note_id':nid,'state':'proposed','visibility':'private'})
        if method=='POST' and len(up_match)==6 and up_match[:4]==['','api','v1','notes'] and up_match[5]=='submit':
            data=self.json_body()
            if data.get('acknowledged') is not True:
                return self.fail(412,'Explicit author consent required to submit note for team review')
            with db_open(root) as c:
                c.execute('BEGIN IMMEDIATE')
                note=c.execute('SELECT * FROM notes WHERE id=?',(up_match[4],)).fetchone()
                if not note or note['author']!=actor['name']:
                    return self.fail(404,'Only the author can submit a note')
                if note['state'] not in ('proposed','rejected'):
                    return self.fail(409,'Note cannot be submitted in current state')
                if note['item_id']:
                    linked=c.execute('SELECT * FROM items WHERE id=?',(note['item_id'],)).fetchone()
                    if not linked or linked['actor']!=actor['name'] or linked['visibility']!='team':
                        return self.fail(409,'Linked item must be owned and shared with team first')
                c.execute("UPDATE notes SET state='submitted' WHERE id=?",(up_match[4],))
                audit(c,actor['name'],'note.submit','note',up_match[4])
            return self.reply(200,{'note_id':up_match[4],'state':'submitted','visibility':'private'})
        if method=='POST' and len(up_match)==6 and up_match[:4]==['','api','v1','notes'] and up_match[5]=='review':
            if role!='admin':
                return self.fail(403,'Admin review required')
            data=self.json_body()
            if data.get('decision') not in ('approve','reject'):
                return self.fail(400,'decision must be approve or reject')
            with db_open(root) as c:
                c.execute('BEGIN IMMEDIATE')
                note=c.execute('SELECT * FROM notes WHERE id=?',(up_match[4],)).fetchone()
                if not note:
                    return self.fail(404,'Note not found')
                if note['state']!='submitted':
                    return self.fail(409,'Note is not awaiting review')
                state='approved' if data['decision']=='approve' else 'rejected'
                visibility='team' if state=='approved' else 'private'
                c.execute('UPDATE notes SET state=?,visibility=? WHERE id=?',(state,visibility,up_match[4]))
                audit(c,actor['name'],'note.review','note',up_match[4],{'decision':data['decision']})
            return self.reply(200,{'note_id':up_match[4],'state':state,'visibility':visibility})
        if method=='POST' and len(up_match)==6 and up_match[:4]==['','api','v1','notes'] and up_match[5]=='withdraw':
            with db_open(root) as c:
                c.execute('BEGIN IMMEDIATE')
                note=c.execute('SELECT * FROM notes WHERE id=?',(up_match[4],)).fetchone()
                if not note or note['author']!=actor['name']:
                    return self.fail(404,'Only author can withdraw a note')
                c.execute("UPDATE notes SET state='proposed',visibility='private' WHERE id=?",(up_match[4],))
                audit(c,actor['name'],'note.withdraw','note',up_match[4])
            return self.reply(200,{'note_id':up_match[4],'state':'proposed','visibility':'private',
                                   'warning':'Prior exported copies cannot be recalled'})
        if method=='GET' and len(up_match)==6 and up_match[:4]==['','api','v1','notes'] and up_match[5]=='markdown':
            with db_open(root) as c:
                note=c.execute('SELECT * FROM notes WHERE id=?',(up_match[4],)).fetchone()
            if not note or not can_read(actor,note,note=True):
                return self.fail(404,'Note not found')
            # Escape YAML by JSON-string serialization, a safe YAML-compatible scalar.
            yaml=lambda s:json.dumps(str(s),ensure_ascii=False)
            md=(f'---\nid: {yaml(note["id"])}\nauthor: {yaml(note["author"])}\nproject: {yaml(note["project"])}\n'
                f'state: {yaml(note["state"])}\nartifact_id: {yaml(note["item_id"])}\n---\n\n# {note["title"]}\n\n{note["body"]}\n').encode()
            return self.send_bytes(200,md,'text/markdown')
        return self.fail(404,'Unknown endpoint')

    def dispatch(self, method):
        try:
            self.handle_route(method)
        except (ValueError,KeyError,json.JSONDecodeError) as exc:
            self.fail(400,str(exc)[:300])
        except BrokenPipeError:
            return
        except Exception as exc:
            print(f'[hub error] {type(exc).__name__}: {exc}',flush=True)
            self.fail(500,'Server error; see hub logs')

    def do_GET(self): self.dispatch('GET')
    def do_POST(self): self.dispatch('POST')
    def do_PATCH(self): self.dispatch('PATCH')


class FunnelServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self, host, port, root):
        root=Path(root).resolve()
        setup_db(root)
        auth_file=root/'auth.json'
        if not auth_file.exists():
            raise RuntimeError('No auth.json. Run python -m funnel init --data <folder> first')
        with open(auth_file,encoding='utf-8') as f:
            self.auth=json.load(f)
        self.root=root
        self.upload_lock=threading.RLock()
        self.stop_event=threading.Event()
        super().__init__((host,port),FunnelHandler)
        self.worker=threading.Thread(target=worker_loop,args=(root,self.stop_event),daemon=True)
        self.worker.start()

    def server_close(self):
        self.stop_event.set()
        self.worker.join(timeout=3)
        super().server_close()
