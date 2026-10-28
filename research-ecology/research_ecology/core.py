"""OX Research Ecology M0.1: owner-local event log, bounded research distillation.

No external application is modified. No claim of AI understanding or accreditation.
"""
from __future__ import annotations
import hashlib
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPHandler, HTTPSHandler, HTTPRedirectHandler
from uuid import uuid4

SCHEMA = 'oxsukra.research-event.v1'
KINDS = {'plan', 'session_started', 'source_saved', 'insight', 'understanding_claim',
         'verification', 'session_ended', 'companion_event'}
CATEGORIES = {
    'electrical': ('circuit','voltage','resistance','instrumentation','ohm','transformer'),
    'programming': ('python','javascript','typescript','github','repository','api','code','css'),
    'ai': ('model','llm','embedding','rag','inference','agent','neural'),
    'thermal': ('thermodynamics','thermal','cooling','heat','conduction','fluid'),
    'marketing': ('seo','conversion','audience','traffic','campaign','analytics'),
    'commerce': ('store','ecommerce','product','checkout','merchant'),
    'finance': ('blockchain','crypto','trading','backtest','market'),
    'design': ('animation','interface','layout','transition','ux','ui')
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def classify(text):
    words = set(re.findall(r'[a-z0-9]+', text.lower()))
    scored = [(sum(term in words for term in terms), name) for name,terms in CATEGORIES.items()]
    return [name for score,name in sorted(scored, key=lambda pair:(-pair[0],pair[1])) if score > 0][:3] or ['general']


class DocumentText(HTMLParser):
    """Extract readable headings and paragraph/code blocks; never execute scripts."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lines, self.buf, self.depth, self.hidden = [], [], 0, 0
        self.capture = {'h1','h2','h3','h4','p','li','pre','code','title'}
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','svg','noscript'): self.hidden += 1
        if tag in self.capture and not self.hidden: self.depth += 1
    def handle_endtag(self, tag):
        if tag in self.capture and self.depth and not self.hidden:
            self.depth -= 1
            if not self.depth and self.buf:
                line = ' '.join(''.join(self.buf).split())
                if line: self.lines.append(line[:1200])
                self.buf = []
        if tag in ('script','style','svg','noscript') and self.hidden: self.hidden -= 1
    def handle_data(self, data):
        if self.depth and not self.hidden: self.buf.append(data)


def distill(text, objective='', max_items=6):
    """Deterministic extractive digest, NOT model comprehension or a truth judgment."""
    blocks = [x.strip() for x in text.splitlines() if len(x.strip()) >= 25]
    query = set(re.findall(r'[a-z0-9]+', objective.lower())) - {'the','and','for','with','from','into','what','this'}
    ranking = sorted(enumerate(blocks), key=lambda p: (-len(set(re.findall(r'[a-z0-9]+',p[1].lower())) & query),p[0]))
    selected = sorted(ranking[:max_items], key=lambda p:p[0]); return [x[:600] for _,x in selected]


def validate_public_https(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        raise ValueError('Only public HTTPS links without credentials or custom ports are supported')
    if parsed.hostname.lower() in ('localhost',) or parsed.hostname.lower().endswith('.local'):
        raise ValueError('Local hosts are not allowed')
    # Blocking resolved private addresses reduces SSRF risk; not an anti-rebinding guarantee.
    for info in socket.getaddrinfo(parsed.hostname,443,type=socket.SOCK_STREAM):
        addr=ipaddress.ip_address(info[4][0])
        if not addr.is_global: raise ValueError('Non-public network address is not allowed')
    return url


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Redirects require a separate approved link')


def fetch_public_page(url):
    """Opt-in and bounded. Do not supply cookies, auth or private sessions."""
    validate_public_https(url)
    req = Request(url, headers={'User-Agent':'OX-Research-Ecology-M0.1', 'Accept':'text/html,text/plain'})
    opener = build_opener(HTTPSHandler(), HTTPHandler(), NoRedirect())
    with opener.open(req, timeout=8) as resp:
        kind=resp.headers.get_content_type()
        if kind not in ('text/html','text/plain'): raise ValueError('Only HTML/text sources supported')
        declared=resp.headers.get('Content-Length')
        if declared and int(declared)>256000: raise ValueError('Page too large')
        raw=resp.read(256001)
    if len(raw)>256000: raise ValueError('Page too large')
    text=raw.decode('utf-8',errors='replace')
    if kind=='text/html':
        p=DocumentText(); p.feed(text); text='\n'.join(p.lines)
    return text[:100000]


class ResearchStore:
    """SQLite append-only event stream. Each event carries previous hash for evidence chaining."""
    def __init__(self, path):
        self.path=Path(path).expanduser()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA busy_timeout=3000')
        self.db.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE, ts TEXT NOT NULL, kind TEXT NOT NULL, session TEXT, body TEXT NOT NULL, prior TEXT NOT NULL, sha TEXT NOT NULL)')
        self.db.commit()
    def close(self): self.db.close()
    def add(self,kind,payload,session=None):
        if kind not in KINDS: raise ValueError('Unknown event kind')
        if not isinstance(payload,dict): raise ValueError('Payload must be an object')
        if len(canonical(payload))>120000: raise ValueError('Payload too large')
        latest=self.db.execute('SELECT sha FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        event={'schema':SCHEMA,'id':uuid4().hex,'ts':now(),'kind':kind,'session':session,'payload':payload,'prior':latest['sha'] if latest else 'GENESIS'}
        sha=digest(event)
        with self.db:
            self.db.execute('INSERT INTO events(id,ts,kind,session,body,prior,sha) VALUES(?,?,?,?,?,?,?)',
                            (event['id'],event['ts'],kind,session,canonical(payload),event['prior'],sha))
        return {**event,'sha256':sha}
    def list(self,session=None):
        sql='SELECT * FROM events'+(' WHERE session=?' if session else '')+' ORDER BY seq'
        rows=self.db.execute(sql,(session,) if session else ()).fetchall()
        return [{**dict(row),'payload':json.loads(row['body'])} for row in rows]
    def verify(self):
        expected='GENESIS'
        for row in self.list():
            ev={'schema':SCHEMA,'id':row['id'],'ts':row['ts'],'kind':row['kind'],'session':row['session'],'payload':row['payload'],'prior':row['prior']}
            if row['prior']!=expected or digest(ev)!=row['sha']:return False
            expected=row['sha']
        return True
    def plan(self,topic,project,when,minutes,prepared_sources=None):
        if not (5 <= int(minutes) <= 480): raise ValueError('Slot duration must be 5-480 minutes')
        return self.add('plan',{'topic':topic,'project':project,'proposed_for':when,'minutes':int(minutes),
                'prepared_sources':prepared_sources or [],'state':'proposal','owner':'research-ecology',
                'slotline_commit':'NOT_REQUESTED'})
    def start(self,topic,project,slotline_ref=None):
        sid=uuid4().hex
        self.add('session_started',{'topic':topic,'project':project,'slotline_ref':slotline_ref,
                                    'slotline_verified':False},sid)
        return sid
    def source(self,url,text,objective,session=None):
        if len(text)>100000: raise ValueError('Source extraction too large')
        extracted=distill(text,objective)
        record={'url':url,'source_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'objective':objective,'classification':classify(objective+' '+text[:5000]),
                'extract':extracted,'extraction':'deterministic; not AI-verified',
                'capture_state':'user-supplied text or approved public fetch'}
        return self.add('source_saved',record,session)
    def insight(self,claim,source_ids,project,session=None):
        if not claim.strip(): raise ValueError('Insight cannot be empty')
        return self.add('insight',{'claim':claim,'origin':'human-hypothesis','source_ids':source_ids,
                'project':project,'verification_state':'unverified'},session)
    def reviewed(self,source_id,level,session=None):
        if level not in ('looked_at','skimmed','notes','explained','applied'): raise ValueError('Invalid learning stage')
        return self.add('understanding_claim',{'source_id':source_id,'level':level,'attested_by':'user',
                'competency_signoff':False},session)
    def recap(self,session):
        events=self.list(session)
        return {'schema':'oxsukra.study-recap.v1','session':session,'events':len(events),
          'sources':[e['payload']['url'] for e in events if e['kind']=='source_saved'],
          'insights':[e['payload']['claim'] for e in events if e['kind']=='insight'],
          'research_ticks':sum(e['kind']=='understanding_claim' for e in events),
          'competency_signoffs':0}
    def export(self):
        return {'schema':'oxsukra.research-export.v1','owner':'research-ecology',
                'data_classification':'private; review before sharing','verified_chain':self.verify(),
                'events':[{'schema':SCHEMA,'id':r['id'],'ts':r['ts'],'kind':r['kind'],
                    'session':r['session'],'payload':r['payload'],'prior':r['prior'],'sha256':r['sha']}
                    for r in self.list()]}
