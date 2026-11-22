"""Three-provider sequential handoff orchestrator, explicitly not an agent runtime.

Native provider integrations are separate future components. A DSOE job is a
portable, reviewable local artifact with real state transitions and evidence.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile

from ixo.common import SETS
from .registry import manifest
from .store import DSOEStore, DSOEError, MAX_RESULT

class DSOESystem:
    def __init__(self, foundation):
        self.foundation=foundation
        self.root=foundation.home/'dsoe'
        self.root.mkdir(parents=True,exist_ok=True)
        self.store=DSOEStore(self.root/'dsoe.sqlite3',foundation.ixo._get('instance_id'))

    def close(self): self.store.close()

    @staticmethod
    def providers():return manifest()

    def plan(self,objective,workspace=None):
        active=self.foundation.ixo.status(0)['active_set']
        workspace=workspace or active
        if workspace not in SETS:raise DSOEError('Unknown Habitat set')
        if workspace!=active:
            raise DSOEError('First activate workspace via Habitat; DSOE cannot change workspace identity')
        return self.store.plan(workspace,objective)

    def dispatch(self,task_id):
        job=self.store.next_job(task_id)
        envelope=self.store.make_envelope(job['id'])
        detail=self.store.detail(task_id)
        prior=[{'job_id':j['id'],'provider':j['provider'],'result_sha256':j['response_sha256'],
                'summary':j['response']['summary']} for j in detail['jobs'] if j['state']=='ACCEPTED']
        envelope['accepted_predecessors']=prior
        # Never automatically run imported code or send data over the network.
        # File export is visible and an external bridge must be explicitly installed.
        inbox=self.root/'outbox'/job['provider']
        inbox.mkdir(parents=True,exist_ok=True)
        output=inbox/(job['id']+'.json')
        data=json.dumps(envelope,sort_keys=True,ensure_ascii=False,indent=2).encode('utf-8')
        if output.exists():
            if output.read_bytes()!=data:raise DSOEError('Existing outbox envelope differs; refusing overwrite')
        else:
            fd,tmp=tempfile.mkstemp(prefix='.pending-',dir=inbox)
            try:
                with os.fdopen(fd,'wb') as stream:stream.write(data)
                os.replace(tmp,output)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
        self.store.mark_dispatched(job['id'])
        return {'ok':True,'task_id':task_id,'job_id':job['id'],
                'provider':job['provider'],'handoff_file':str(output),'native_upstream_execution':False,
                'next':'An audited external bridge or operator supplies a result JSON; then report and review.'}

    def report_file(self,job_id,path):
        path=Path(path)
        if not path.is_file():raise DSOEError('Result file is missing')
        if path.stat().st_size>MAX_RESULT:raise DSOEError('Result file exceeds size limit')
        try:content=json.loads(path.read_text(encoding='utf-8'))
        except (UnicodeError,json.JSONDecodeError) as exc:raise DSOEError('Invalid UTF-8 JSON result file') from exc
        row=self.store.report(job_id,content)
        return {'ok':True,'job_id':job_id,'status':row['state'],'source':'untrusted_external_result',
                'next':'Review explicitly; nothing has been committed as IXO fact.'}

    def record_evidence(self,job_id):
        payload=self.store.verified_result(job_id)
        written=self.foundation.aixo.ingest_dsoe_evidence(payload, self.foundation.ixo._get('instance_id'))
        return {'ok':True,'job_id':job_id,'aixo_evidence_new':written,'source_id':payload['ixo_source_id'],
                'fact_writes':0,'meaning':'Operator acceptance is not Hermes fact approval'}

    def detail(self,task_id):return self.store.detail(task_id)
    def status(self):return self.store.status()
