"""Operator-invoked feature control, not a project/task registry.

Every declared action calls existing IXO, Hermes, Moon2, AIXO, DSOE,
FrameShift or Experience implementation. No arbitrary Python/shell dispatch,
no automatic Hermes approvals and no simulated third-party agent execution.
Receipts are append-only in a separate local SQLite database.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class OperationError(ValueError):
    pass


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


# id, component, effect, fields (name, type, required), purpose
CATALOG = (
 ('habitat.activate','Habitat','write', [('workspace','text',True)], 'Activate a real workspace through Habitat'),
 ('habitat.inspect','Habitat','read', [], 'Read active workspace and sets'),
 ('hermes.propose','Hermes','write', [('text','multiline',True),('source','text',False)], 'Queue a real fact proposal; no auto approval'),
 ('hermes.resolve','Hermes','approval', [('id','text',True),('decision','choice:approve,reject',True)], 'Resolve a specific pending fact proposal'),
 ('hermes.inspect','Hermes','read', [], 'Read actual facts and proposals'),
 ('moon2.record','Moon2','write', [('stage','choice:observe,interpret,decide,act,reflect',True),('text','multiline',True)], 'Append an actual Moon2 stage'),
 ('moon2.inspect','Moon2','read', [], 'Inspect actual stage entries'),
 ('aixo.experiment','AIXO','write', [('title','text',True),('question','multiline',True)], 'Create an AIXO experiment'),
 ('aixo.evaluate','AIXO','write', [('experiment_id','integer',True),('assertion','choice:active_set,facts_count,proposals_count,events_count,reflections_count',True),('expected','json',True)], 'Evaluate actual IXO state against expectation'),
 ('aixo.inspect','AIXO','read', [], 'Inspect lessons, experiments, evaluations'),
 ('dsoe.plan','DSOE','write', [('objective','multiline',True)], 'Create real staged handoff in DSOE; no external agent execution'),
 ('dsoe.inspect','DSOE','read', [], 'Inspect durable DSOE tasks and provider capabilities'),
 ('dsoe.approve','DSOE','approval', [('task_id','text',True)], 'Approve a specific DSOE task'),
 ('dsoe.dispatch','DSOE','write', [('task_id','text',True)], 'Write next provider handoff JSON, not execute a provider'),
 ('experience.sync','Experience','write', [], 'Capture actual IXO event history as self-development exposure'),
 ('experience.ingest','Experience','write', [('path','path',True),('project','text',True),('domain','text',True),('origin','choice:ixo_development,independent_project,external_reference,fixture',True)], 'Ingest real file or directory into labelled experience'),
 ('experience.balance','Experience','read', [], 'Compute actual self/other exposure report and selection'),
 ('frameshift.analyze','FrameShift','read', [('text','multiline',True)], 'Run existing linguistic representation analysis'),
 ('quality.tests','Quality','test', [('suite','choice:all,components,experience,dsoe,frameshift,operations',True)], 'Run named existing Python unittest suites; return test result'),
 ('workflow.investigate','Workflow','write', [('workspace','text',True),('observation','multiline',True),('hypothesis','multiline',True),('question','multiline',True)], 'Run real FrameShift→Habitat→Moon2→Hermes proposal→AIXO experiment→capture chain'),
 ('workflow.ingest_project','Workflow','write', [('path','path',True),('project','text',True),('domain','text',True)], 'Run real file ingestion, exposure report and balanced selection'),
)
INDEX = {op[0]:op for op in CATALOG}
TEST_TARGETS = {
 'all': None,
 'components': 'test_components.py',
 'experience': 'test_experience.py',
 'dsoe': 'test_dsoe.py',
 'frameshift': 'frame',
 'operations': 'test_operations.py',
}


class OperationsHub:
    def __init__(self, foundation):
        self.foundation = foundation
        self.lock=threading.RLock()
        self.path=foundation.home/'operations.sqlite3'
        self.conn=sqlite3.connect(self.path,check_same_thread=False,timeout=15)
        self.conn.row_factory=sqlite3.Row
        self.conn.execute('PRAGMA busy_timeout=15000')
        self.conn.execute('PRAGMA journal_mode=WAL')
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS receipts(
                id INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL,
                feature TEXT NOT NULL, effect TEXT NOT NULL, inputs_sha256 TEXT NOT NULL,
                passed INTEGER NOT NULL, output_sha256 TEXT, result_json TEXT NOT NULL)''')

    def close(self):
        with self.lock:self.conn.close()

    def list(self)->list[dict]:
        return [{'id':key,'component':component,'effect':effect,
                 'fields':[{'name':n,'type':t,'required':r} for n,t,r in fields],
                 'purpose':description}
                for key,component,effect,fields,description in CATALOG]

    def receipts(self, limit:int=30)->list[dict]:
        if not isinstance(limit,int) or limit<1 or limit>200:raise OperationError('limit must be 1..200')
        with self.lock:
            return [dict(x) for x in self.conn.execute('SELECT * FROM receipts ORDER BY id DESC LIMIT ?',(limit,))]

    def _validate(self, action:str, inputs:dict)->dict:
        if action not in INDEX:raise OperationError('Unknown feature; use list')
        if not isinstance(inputs,dict):raise OperationError('Inputs must be a JSON object')
        fields=INDEX[action][3]
        allowed={x[0] for x in fields}
        if set(inputs)-allowed:raise OperationError('Unexpected input fields: '+', '.join(sorted(set(inputs)-allowed)))
        clean={}
        for key,kind,required in fields:
            value=inputs.get(key)
            if value is None or value=='':
                if required:raise OperationError('Missing required field '+key)
                continue
            if kind=='integer':
                if isinstance(value,bool) or not isinstance(value,int) and not (isinstance(value,str) and value.isdecimal()):
                    raise OperationError(key+' must be a positive integer')
                value=int(value)
                if value<1:raise OperationError(key+' must be positive')
            elif kind=='json':
                if isinstance(value,str):
                    try:value=json.loads(value)
                    except json.JSONDecodeError as exc:raise OperationError('Expected valid JSON in '+key) from exc
            else:
                if not isinstance(value,str) or not value.strip() or len(value)>5000:
                    raise OperationError(key+' must be nonempty text <= 5000 characters')
                value=value.strip()
                if kind.startswith('choice:') and value not in kind.split(':',1)[1].split(','):
                    raise OperationError('Unsupported choice for '+key)
            clean[key]=value
        return clean

    def run(self, feature:str, inputs:dict|None=None)->dict:
        """Invoke one working component port; persist a receipt even on failure.

        Receipts record input hashes, not raw potentially sensitive input. Results
        are truncated to 30k when stored. This does NOT make actions atomic
        across IXO, AIXO, Experience, and DSOE databases.
        """
        inputs=self._validate(feature, inputs or {})
        effect=INDEX[feature][2]
        digest=hashlib.sha256(json.dumps(inputs,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        try:
            result=self._invoke(feature,inputs)
            passed=(result.get('passed',True) is not False and result.get('ok',True) is not False)
        except Exception as exc:
            # Do not hide unexpected failures, but record them, including their type.
            result={'ok':False,'error_type':type(exc).__name__,'error':str(exc)[:1000]}
            passed=False
        output=json.dumps(result,ensure_ascii=False,sort_keys=True,default=str)
        out_digest=hashlib.sha256(output.encode()).hexdigest()
        with self.lock,self.conn:
            row=self.conn.execute('INSERT INTO receipts(at,feature,effect,inputs_sha256,passed,output_sha256,result_json) VALUES(?,?,?,?,?,?,?)',
                (timestamp(),feature,effect,digest,int(passed),out_digest,output[:30000]))
            receipt_id=row.lastrowid
        return {'receipt_id':receipt_id,'feature':feature,'effect':effect,'passed':passed,'result':result}

    def _invoke(self, feature:str, p:dict)->dict:
        f=self.foundation
        i=f.ixo
        a=f.aixo
        e=f.experience
        d=f.dsoe
        if feature=='habitat.activate':return i.habitat.activate_set(p['workspace'])
        if feature=='habitat.inspect':
            s=i.status(0);return {'active_set':s['active_set'],'sets':s['sets'],'camera_depth':s['camera_depth']}
        if feature=='hermes.propose':return i.hermes.propose(p['text'],p.get('source','user'))
        if feature=='hermes.resolve':return i.hermes.resolve(p['id'],p['decision'])
        if feature=='hermes.inspect':
            s=i.status(0);return {'facts':s['facts'],'proposals':s['proposals']}
        if feature=='moon2.record':return i.moon2.moon(p['stage'],p['text'])
        if feature=='moon2.inspect':return {'reflections':i.status(0)['reflections']}
        if feature=='aixo.experiment':return a.create_experiment(p['title'],p['question'])
        if feature=='aixo.evaluate':return a.evaluate(p['experiment_id'],p['assertion'],p['expected'],i.status(0))
        if feature=='aixo.inspect':
            s=a.state();return {'lessons':s['lessons'],'experiments':s['experiments'],
                'evaluations':s['evaluations'],'captured_events':s['captured_events']}
        if feature=='dsoe.plan':return d.plan(p['objective'])
        if feature=='dsoe.inspect':return {'status':d.status(),'providers':d.providers(),'native_connected':0}
        if feature=='dsoe.approve':return d.store.approve(p['task_id'])
        if feature=='dsoe.dispatch':return d.dispatch(p['task_id'])
        if feature=='experience.sync':return e.capture_ixo(i)
        if feature=='experience.balance':return {'report':e.report(),'selection':e.select(max_items=40)}
        if feature=='experience.ingest':
            path=Path(p['path']).expanduser().resolve(strict=True)
            labels=dict(project=p['project'],domain=p['domain'],origin=p['origin'])
            if path.is_dir():return e.ingest_tree(path,limit=250,**labels)
            return e.record_file(path,**labels)
        if feature=='frameshift.analyze':return f.probe(p['text'])
        if feature=='quality.tests':return self._tests(p['suite'])
        if feature=='workflow.investigate':
            # Input-derived analysis, never silently promoted as a fact.
            interpretation=f.probe(p['observation'])
            case=f.case(workspace=p['workspace'],observation=p['observation'],
                        hypothesis=p['hypothesis'],question=p['question'])
            return {'ok':True,'analysis':interpretation,'case':case,'verified_steps':[
                'frameshift.analyze','habitat.activate','moon2.observe','moon2.interpret',
                'hermes.propose_pending','aixo.experiment','aixo.bridge.capture'],
                'limitations':'No tool execution, automatic judgment or fact approval'}
        if feature=='workflow.ingest_project':
            path=Path(p['path']).expanduser().resolve(strict=True)
            if not path.is_dir():raise OperationError('Project ingestion requires a directory')
            ingested=e.ingest_tree(path,project=p['project'],domain=p['domain'],origin='independent_project',limit=250)
            return {'ok':True,'ingested':ingested,'report':e.report(),
                    'selection':e.select(max_items=50),
                    'limitation':'Files are observations, not independently verified task outcomes'}
        raise OperationError('Unimplemented feature')

    def _tests(self, suite:str)->dict:
        """Run repository-local source tests by known suite name; never user shell."""
        if suite not in TEST_TARGETS:raise OperationError('Unknown test suite')
        root=Path(__file__).resolve().parents[1]
        if not (root/'tests'/'test_foundation.py').exists():
            raise OperationError('Source checkout with tests is required')
        target=TEST_TARGETS[suite]
        cmd=[sys.executable,'-m','unittest','discover','-s','tests','-q']
        if target=='frame':cmd=[sys.executable,'-m','unittest','discover','-s','tests/frame','-q']
        elif target:cmd=[sys.executable,'-m','unittest','discover','-s','tests','-p',target,'-q']
        try:
            proc=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=90,check=False)
        except subprocess.TimeoutExpired:
            return {'ok':False,'passed':False,'suite':suite,'reason':'90s timeout'}
        return {'ok':proc.returncode==0,'passed':proc.returncode==0,'suite':suite,
                'exit_code':proc.returncode,'output':(proc.stdout+'\n'+proc.stderr)[-12000:],
                'command':cmd,'executed':True}
