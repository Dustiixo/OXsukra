from __future__ import annotations
import json
from .common import SCHEMA_VERSION, SETS

class Inspector:
    def __init__(self, runtime):
        self.runtime=runtime

    def __getattr__(self, name):
        return getattr(self.runtime,name)

    def status(self, events_limit=35):
        with self.lock:
            def rows(sql): return [dict(x) for x in self.conn.execute(sql).fetchall()]
            counts={name:self.conn.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
                    for name in ('facts','proposals','reflections','events')}
            events=[]
            for r in self.conn.execute('SELECT * FROM events ORDER BY seq DESC LIMIT ?', (max(0,min(int(events_limit),500)),)):
                d=dict(r);d['payload']=json.loads(d['payload']);events.append(d)
            return {'schema':SCHEMA_VERSION,'active_set':self._get('active_set'),
                    'camera_depth':int(self._get('camera_depth')),'sets':list(SETS),
                    'counts':counts,'facts':rows('SELECT * FROM facts ORDER BY id DESC LIMIT 100'),
                    'proposals':rows('SELECT * FROM proposals ORDER BY id DESC LIMIT 100'),
                    'reflections':rows('SELECT * FROM reflections ORDER BY id DESC LIMIT 100'),
                    'events':events,'capabilities':{'hermes':'conservative_proposal_gate',
                    'moon2':'manual_staged_ledger','spatial':'2d_client_projection','aixo':'separate_reference'}}

