"""Persistent, source-bound, operator-gated DSOE workflow store."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .registry import PROVIDERS, PROVIDER_BY_KEY

MAX_TEXT = 2000
MAX_RESULT = 16000

class DSOEError(ValueError):
    pass

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()

def bounded(value: str, limit: int = MAX_TEXT) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise DSOEError(f'Expected nonempty text of at most {limit} characters')
    return value.strip()

class DSOEStore:
    def __init__(self, path: str | Path, source_id: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=4)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.execute('PRAGMA journal_mode=WAL')
        with self.lock, self.conn:
            self.conn.executescript("""
              CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS tasks(
                  id TEXT PRIMARY KEY, source_id TEXT NOT NULL, workspace TEXT NOT NULL,
                  objective TEXT NOT NULL, state TEXT NOT NULL, at TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS jobs(
                  id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                  provider TEXT NOT NULL, stage TEXT NOT NULL, ordinal INTEGER NOT NULL,
                  state TEXT NOT NULL, request TEXT NOT NULL, request_sha256 TEXT NOT NULL,
                  response TEXT, response_sha256 TEXT, at TEXT NOT NULL,
                  UNIQUE(task_id, ordinal));
              CREATE TABLE IF NOT EXISTS trail(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                  task_id TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL);
            """)
            self.conn.execute('INSERT OR IGNORE INTO meta(key,value) VALUES (?,?)', ('schema','1'))
            self.conn.execute('INSERT OR IGNORE INTO meta(key,value) VALUES (?,?)', ('ixo_source_id',source_id))
            db_schema = self.conn.execute("SELECT value FROM meta WHERE key='schema'").fetchone()[0]
            bound_source = self.conn.execute("SELECT value FROM meta WHERE key='ixo_source_id'").fetchone()[0]
        if db_schema != '1':
            self.conn.close()
            raise DSOEError('Unsupported DSOE schema')
        if bound_source != source_id:
            self.conn.close()
            raise DSOEError('DSOE database belongs to another IXO instance')
        self.source_id = source_id

    def close(self) -> None:
        with self.lock: self.conn.close()

    def _event(self, task_id: str, action: str, detail: dict) -> None:
        self.conn.execute('INSERT INTO trail(at,task_id,action,detail) VALUES(?,?,?,?)',
                          (now(), task_id, action, canonical(detail)))

    def _task(self, task_id: str) -> sqlite3.Row:
        row = self.conn.execute('SELECT * FROM tasks WHERE id=?',(task_id,)).fetchone()
        if row is None: raise DSOEError('Task not found')
        return row

    def _job(self, job_id: str) -> sqlite3.Row:
        row = self.conn.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
        if row is None: raise DSOEError('Job not found')
        return row

    def plan(self, workspace: str, objective: str) -> dict:
        workspace = bounded(workspace,80)
        objective = bounded(objective)
        task_id = uuid.uuid4().hex
        with self.lock,self.conn:
            self.conn.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?)',
                              (task_id,self.source_id,workspace,objective,'DRAFT',now()))
            for i, provider in enumerate(PROVIDERS):
                job_id = uuid.uuid4().hex
                req = {'protocol':'dsoe-json-file-v1', 'task_id':task_id,'job_id':job_id,
                       'ixo_source_id':self.source_id,'workspace':workspace,'objective':objective,
                       'provider':provider.key,'stage':provider.stage,
                       'instruction':provider.role,
                       'constraints':{'no_ixo_fact_writes':True,'no_automatic_tool_execution':True,
                                      'untrusted_result_requires_operator_review':True}}
                self.conn.execute('INSERT INTO jobs(id,task_id,provider,stage,ordinal,state,request,request_sha256,at) VALUES(?,?,?,?,?,?,?,?,?)',
                                  (job_id,task_id,provider.key,provider.stage,i,'PENDING',canonical(req),digest(req),now()))
            self._event(task_id,'plan.created',{'workspace':workspace})
        return self.detail(task_id)

    def approve(self, task_id: str) -> dict:
        with self.lock,self.conn:
            task=self._task(task_id)
            if task['state']=='APPROVED':return self.detail(task_id)
            if task['state']!='DRAFT':raise DSOEError('Only draft tasks can be approved')
            self.conn.execute("UPDATE tasks SET state='APPROVED' WHERE id=?",(task_id,))
            self._event(task_id,'task.approved',{'operator_approval':True})
        return self.detail(task_id)

    def next_job(self, task_id: str) -> dict:
        with self.lock:
            task=self._task(task_id)
            if task['state'] != 'APPROVED': raise DSOEError('Task requires explicit operator approval')
            rows=self.conn.execute('SELECT * FROM jobs WHERE task_id=? ORDER BY ordinal',(task_id,)).fetchall()
            for row in rows:
                if row['state']=='ACCEPTED':continue
                if row['state']=='PENDING':
                    return dict(row)
                raise DSOEError(f'Previous stage {row["stage"]} remains {row["state"]}; operator review required')
            raise DSOEError('All stages already accepted')

    def make_envelope(self, job_id: str) -> dict:
        with self.lock:
            row=self._job(job_id)
            return {'request':json.loads(row['request']),'request_sha256':row['request_sha256'],
                    'handoff':'external runtime must implement this protocol; not a native Pantheon API'}

    def mark_dispatched(self, job_id: str) -> dict:
        with self.lock,self.conn:
            row=self._job(job_id)
            if row['state']=='DISPATCHED':return dict(row)
            if row['state']!='PENDING':raise DSOEError('Job cannot be dispatched from '+row['state'])
            eligible=self.next_job(row['task_id'])
            if eligible['id']!=job_id:raise DSOEError('Previous stage is not accepted')
            self.conn.execute("UPDATE jobs SET state='DISPATCHED' WHERE id=?",(job_id,))
            self._event(row['task_id'],'job.dispatched',{'job_id':job_id,'provider':row['provider']})
            return dict(self._job(job_id))

    def report(self, job_id: str, payload: dict) -> dict:
        if not isinstance(payload,dict): raise DSOEError('JSON object result required')
        if len(canonical(payload).encode('utf-8'))>MAX_RESULT:raise DSOEError('Result exceeds maximum bytes')
        with self.lock,self.conn:
            row=self._job(job_id)
            for key,expected in [('protocol','dsoe-json-file-v1'),('job_id',job_id),
                                 ('provider',row['provider']),('request_sha256',row['request_sha256'])]:
                if payload.get(key)!=expected: raise DSOEError('Result mismatch: '+key)
            bounded(payload.get('summary'),MAX_TEXT)
            from .protocol import validate_stage
            validate_stage(row['provider'],payload)
            result_hash=digest(payload)
            if row['state']=='REPORTED' and row['response_sha256']==result_hash:return dict(row)
            if row['state']!='DISPATCHED':raise DSOEError('Job must be dispatched before report')
            self.conn.execute("UPDATE jobs SET state='REPORTED', response=?, response_sha256=? WHERE id=?",
                              (canonical(payload),result_hash,job_id))
            self._event(row['task_id'],'job.reported',{'job_id':job_id,'sha256':result_hash,'trusted':False})
            return dict(self._job(job_id))

    def review(self, job_id: str, accept: bool, reason: str) -> dict:
        reason=bounded(reason,500)
        with self.lock,self.conn:
            row=self._job(job_id)
            target='ACCEPTED' if accept else 'REJECTED'
            if row['state']==target:return dict(row)
            if row['state']!='REPORTED':raise DSOEError('Cannot review an unreported result')
            self.conn.execute('UPDATE jobs SET state=? WHERE id=?',(target,job_id))
            if not accept:self.conn.execute("UPDATE tasks SET state='BLOCKED' WHERE id=?",(row['task_id'],))
            self._event(row['task_id'],'job.reviewed',{'job_id':job_id,'accepted':accept,'reason':reason,
                                                       'fact_approval':False})
            if accept:
                remaining=self.conn.execute("SELECT count(*) FROM jobs WHERE task_id=? AND state!='ACCEPTED'",(row['task_id'],)).fetchone()[0]
                if not remaining:
                    self.conn.execute("UPDATE tasks SET state='COMPLETE' WHERE id=?",(row['task_id'],))
                    self._event(row['task_id'],'task.complete',{'fact_writes':0})
            return dict(self._job(job_id))

    def detail(self, task_id: str) -> dict:
        with self.lock:
            task=dict(self._task(task_id))
            jobs=[dict(r) for r in self.conn.execute('SELECT * FROM jobs WHERE task_id=? ORDER BY ordinal',(task_id,))]
            for job in jobs:
                job['request']=json.loads(job['request'])
                if job['response']:job['response']=json.loads(job['response'])
            return {'task':task,'jobs':jobs}

    def status(self) -> dict:
        with self.lock:
            tasks=[dict(x) for x in self.conn.execute('SELECT id,workspace,objective,state,at FROM tasks ORDER BY at DESC LIMIT 25')]
            events=[dict(x) for x in self.conn.execute('SELECT * FROM trail ORDER BY seq DESC LIMIT 20')]
            for event in events:event['detail']=json.loads(event['detail'])
            return {'source_id':self.source_id,'tasks':tasks,'events':events}

    def verified_result(self, job_id: str) -> dict:
        with self.lock:
            row=self._job(job_id)
            if row['state']!='ACCEPTED':raise DSOEError('Result requires explicit acceptance')
            return {'job_id':job_id,'task_id':row['task_id'],'provider':row['provider'],
                    'stage':row['stage'],'sha256':row['response_sha256'],
                    'summary':json.loads(row['response'])['summary'],
                    'evidence_origin':json.loads(row['response']).get('evidence_origin','unspecified_unverified'),
                    'ixo_source_id':self.source_id,'status':'operator_accepted_not_fact'}
