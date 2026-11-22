"""AIXO v0.3: evidence-first experiments and narrow reproducible evaluations.

Does NOT run arbitrary code, load LLMs or change IXO state. Its sole IXO access
is a read-only snapshot, plus ingesting committed IXO event records via bridge.
"""
from __future__ import annotations
import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

LESSONS = [
 ('A1','desk','Build the course container'),
 ('A2','train','Read AI Engineering from Scratch'),
 ('A3','desk','Inspect and change one template'),
 ('A4','desk','Study Adam calibration'),
 ('B5','train','Choose one curriculum phase'),
 ('B6','desk','Type, break and repair an exercise'),
 ('B7','train','Relate a lesson to the project'),
 ('B8','desk','Build one verified vertical slice'),
 ('C9','desk','Record a trace and inspect it'),
 ('C10','desk','Run one evaluation'),
 ('C11','train','Review an unexpected observation')]

class AIXOError(ValueError):pass

def stamp():return datetime.now(timezone.utc).isoformat()

class AIXOEngine:
 def __init__(self, path):
  self.path=str(path)
  Path(self.path).parent.mkdir(parents=True,exist_ok=True) if self.path!=':memory:' else None
  self.lock=threading.RLock()
  self.conn=sqlite3.connect(self.path,check_same_thread=False)
  self.conn.row_factory=sqlite3.Row
  self.conn.execute('PRAGMA journal_mode=WAL')
  self.conn.execute('PRAGMA busy_timeout=4000')
  with self.conn:
   self.conn.executescript('''
   CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS lessons(id TEXT PRIMARY KEY, completed_at TEXT,artifact TEXT NOT NULL DEFAULT '');
   CREATE TABLE IF NOT EXISTS experiments(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,question TEXT NOT NULL,at TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS evaluations(id INTEGER PRIMARY KEY AUTOINCREMENT,experiment_id INTEGER NOT NULL,claim TEXT NOT NULL,passed INTEGER NOT NULL,observed TEXT NOT NULL,at TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS observed_ixo_events(ixo_seq INTEGER PRIMARY KEY, at TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS trail(seq INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL);
   CREATE TABLE IF NOT EXISTS dsoe_evidence(job_id TEXT PRIMARY KEY, ixo_source_id TEXT NOT NULL, task_id TEXT NOT NULL, provider TEXT NOT NULL, stage TEXT NOT NULL, sha256 TEXT NOT NULL, summary TEXT NOT NULL, evidence_origin TEXT NOT NULL DEFAULT 'unspecified_unverified', at TEXT NOT NULL);
   ''')
   for lesson in LESSONS:self.conn.execute('INSERT OR IGNORE INTO lessons(id) VALUES (?)',(lesson[0],))
   self.conn.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',('schema','1'))
   if self.conn.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]!='1':raise AIXOError('Unsupported AIXO schema')
 def _log(self,kind,payload):
  self.conn.execute('INSERT INTO trail(at,kind,payload) VALUES (?,?,?)',(stamp(),kind,json.dumps(payload,sort_keys=True)))
 @staticmethod
 def valid(s,maxlen=500):
  if not isinstance(s,str) or not s.strip() or len(s)>maxlen:raise AIXOError('Expected nonempty bounded text')
  return s.strip()
 def complete_lesson(self,lesson,artifact):
  artifact=self.valid(artifact,2000)
  with self.lock,self.conn:
   r=self.conn.execute('SELECT completed_at FROM lessons WHERE id=?',(lesson,)).fetchone()
   if r is None:raise AIXOError('Unknown session')
   previous=[x[0] for x in self.conn.execute('SELECT id FROM lessons WHERE completed_at IS NULL ORDER BY rowid')]
   if r['completed_at'] is None and (not previous or previous[0]!=lesson):raise AIXOError('Course sessions must be completed in order')
   self.conn.execute('UPDATE lessons SET completed_at=?,artifact=? WHERE id=?',(stamp(),artifact,lesson))
   self._log('aixo.lesson.complete',{'lesson':lesson,'artifact':artifact})
  return {'ok':True,'lesson':lesson}
 def create_experiment(self,title,question):
  title=self.valid(title,120);question=self.valid(question,500)
  with self.lock,self.conn:
   c=self.conn.execute('INSERT INTO experiments(title,question,at) VALUES (?,?,?)',(title,question,stamp()))
   self._log('aixo.experiment.create',{'id':c.lastrowid,'title':title})
   return {'ok':True,'experiment_id':c.lastrowid}
 def ingest_events(self, events, source_id=None):
  """Atomic, idempotent capture from exactly one IXO source instance.

  AIXO v0.3 used seq alone, which is not globally unique. Refuse silent
  cross-source merging. Previously captured unbound records need a deliberate
  migration, not a guessed provenance.
  """
  if not isinstance(source_id,str) or not source_id.strip():
   raise AIXOError('IXO source identity required for capture')
  with self.lock,self.conn:
   binding=self.conn.execute("SELECT value FROM meta WHERE key='ixo_source_id'").fetchone()
   if binding and binding['value']!=source_id:
    raise AIXOError('AIXO is bound to another IXO database; use a separate AIXO database')
   if not binding:
    count=self.conn.execute('SELECT COUNT(*) FROM observed_ixo_events').fetchone()[0]
    if count:raise AIXOError('Legacy captured events lack source provenance; manual migration required')
    self.conn.execute("INSERT INTO meta(key,value) VALUES('ixo_source_id',?)",(source_id,))
   inserted=0
   for e in sorted(events,key=lambda x:x['seq']):
    if not all(k in e for k in ('seq','at','type','payload')):
     raise AIXOError('Event missing required fields')
    payload=json.dumps(e['payload'],sort_keys=True)
    existing=self.conn.execute('SELECT at,kind,payload FROM observed_ixo_events WHERE ixo_seq=?',(e['seq'],)).fetchone()
    if existing:
     if (existing['at'],existing['kind'],existing['payload']) != (e['at'],e['type'],payload):
      raise AIXOError('Captured event conflicts with existing record at sequence '+str(e['seq']))
     continue
    self.conn.execute('INSERT INTO observed_ixo_events(ixo_seq,at,kind,payload) VALUES(?,?,?,?)',
                      (e['seq'],e['at'],e['type'],payload))
    inserted+=1
   if inserted:self._log('aixo.bridge.capture',{'count':inserted,'source_id':source_id})
   return inserted
 def evaluate(self,experiment_id,assertion,expected,snapshot):
  """Allowed assertions deliberately limited; no code evaluation or writes to IXO."""
  rules={
   'active_set': lambda s:s['active_set'],
   'facts_count':lambda s:s['counts']['facts'],
   'proposals_count':lambda s:s['counts']['proposals'],
   'events_count':lambda s:s['counts']['events'],
   'reflections_count':lambda s:s['counts']['reflections'],
  }
  if assertion not in rules:raise AIXOError('Unsupported assertion')
  with self.lock,self.conn:
   if not self.conn.execute('SELECT 1 FROM experiments WHERE id=?',(experiment_id,)).fetchone():raise AIXOError('Experiment missing')
   observed=rules[assertion](snapshot);passed=observed==expected
   c=self.conn.execute('INSERT INTO evaluations(experiment_id,claim,passed,observed,at) VALUES (?,?,?,?,?)',(experiment_id,json.dumps({'assertion':assertion,'expected':expected}),int(passed),json.dumps(observed),stamp()))
   self._log('aixo.eval.run',{'id':c.lastrowid,'passed':passed,'assertion':assertion})
   return {'ok':True,'id':c.lastrowid,'passed':passed,'assertion':assertion,'expected':expected,'observed':observed}
 def ingest_dsoe_evidence(self, record, expected_source_id):
  """Accept provenance-bound operator-reviewed DSOE result as *evidence*, never fact."""
  required={'job_id','ixo_source_id','task_id','provider','stage','sha256','summary','status','evidence_origin'}
  if not isinstance(record,dict) or not required.issubset(record):raise AIXOError('Missing DSOE evidence fields')
  if record['status']!='operator_accepted_not_fact':raise AIXOError('DSOE evidence must be operator accepted')
  if record['ixo_source_id'] != expected_source_id:raise AIXOError('DSOE evidence belongs to another IXO source')
  if any(not isinstance(record[k],str) or not record[k].strip() for k in required):raise AIXOError('Invalid DSOE evidence field')
  if len(record['summary'])>2000:raise AIXOError('DSOE summary too long')
  with self.lock,self.conn:
   source=self.conn.execute("SELECT value FROM meta WHERE key='ixo_source_id'").fetchone()
   if source is None:
    if self.conn.execute('SELECT COUNT(*) FROM observed_ixo_events').fetchone()[0]:
     raise AIXOError('Legacy IXO events have missing provenance')
    self.conn.execute("INSERT INTO meta(key,value) VALUES('ixo_source_id',?)",(record['ixo_source_id'],))
   elif source[0]!=record['ixo_source_id']:
    raise AIXOError('AIXO belongs to another IXO source')
   row=self.conn.execute('SELECT * FROM dsoe_evidence WHERE job_id=?',(record['job_id'],)).fetchone()
   if row:
    keys=['ixo_source_id','task_id','provider','stage','sha256','summary','evidence_origin']
    if any(row[k]!=record[k] for k in keys):raise AIXOError('DSOE evidence replay conflict')
    return False
   self.conn.execute('INSERT INTO dsoe_evidence VALUES(?,?,?,?,?,?,?,?,?)',
                     tuple(record[k] for k in ('job_id','ixo_source_id','task_id','provider','stage','sha256','summary','evidence_origin'))+(stamp(),))
   self._log('aixo.dsoe.evidence',{'job_id':record['job_id'],'provider':record['provider'],'origin':record['evidence_origin'],'status':'evidence_only'})
   return True

 def state(self):
  with self.lock:
   def rows(q):return [dict(x) for x in self.conn.execute(q)]
   lessonrows=rows('SELECT * FROM lessons ORDER BY rowid')
   for row,ref in zip(lessonrows,LESSONS):row.update({'mode':ref[1],'title':ref[2]})
   return {'source_id':(lambda row: row[0] if row else None)(self.conn.execute("SELECT value FROM meta WHERE key='ixo_source_id'").fetchone()),'lessons':lessonrows,'experiments':rows('SELECT * FROM experiments ORDER BY id DESC LIMIT 100'),
           'evaluations':rows('SELECT * FROM evaluations ORDER BY id DESC LIMIT 100'),
           'captured_events':self.conn.execute('SELECT COUNT(*) FROM observed_ixo_events').fetchone()[0],
           'dsoe_evidence_count':self.conn.execute('SELECT COUNT(*) FROM dsoe_evidence').fetchone()[0],
           'dsoe_evidence':rows('SELECT * FROM dsoe_evidence ORDER BY at DESC LIMIT 20'),
           'recent_evidence':rows('SELECT * FROM observed_ixo_events ORDER BY ixo_seq DESC LIMIT 20'),
           'trail':rows('SELECT * FROM trail ORDER BY seq DESC LIMIT 40')}
 def close(self):
  with self.lock:self.conn.close()
