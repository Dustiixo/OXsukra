from __future__ import annotations
from .common import IXOError, STAGES, now

class Moon2:
    def __init__(self, runtime):
        self.runtime=runtime

    def __getattr__(self, name):
        return getattr(self.runtime,name)

    def moon(self, stage, text):
        if stage not in STAGES: raise IXOError('Invalid Moon2 stage')
        text=self._text(text)
        with self.lock, self.conn:
            workspace=self._get('active_set')
            c=self.conn.execute('INSERT INTO reflections(stage,text,workspace,at) VALUES(?,?,?,?)',(stage,text,workspace,now()))
            seq=self._event('moon2.'+stage,{'id':c.lastrowid,'workspace':workspace})
            return {'ok':True,'id':f'M{c.lastrowid}','seq':seq,'message':f'Moon2 {stage} captured (observation/ledger only)'}

