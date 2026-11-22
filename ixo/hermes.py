from __future__ import annotations
import re
from .common import IXOError, words, now

class Hermes:
    def __init__(self, runtime):
        self.runtime=runtime

    def __getattr__(self, name):
        return getattr(self.runtime,name)

    def propose(self, text, source='user', protected=False, protection_reason=''):
        text=self._text(text,6174 if protected else 2200)
        source=self._text(source,100)
        if protected: protection_reason=self._text(protection_reason,400)
        key=' '.join(text.lower().split())
        with self.lock, self.conn:
            exact=self.conn.execute('SELECT id FROM facts WHERE key=?',(key,)).fetchone()
            allfacts=self.conn.execute('SELECT text FROM facts').fetchall()
            # Deliberately conservative: overlapping long words -> HUMAN_REVIEW.
            # Historical Hermes Mark 12 classifier has NOT been reproduced.
            overlap=any(bool({w for w in words(row['text']) if len(w)>=5} &
                             {w for w in words(text) if len(w)>=5}) for row in allfacts)
            cls='AGREE' if exact else 'REVIEW' if overlap else 'UNRELATED'
            status='BLOCKED' if source=='memory' else 'PENDING'
            c=self.conn.execute('''INSERT INTO proposals(text,key,source,protected,protection_reason,classification,status,at)
                VALUES(?,?,?,?,?,?,?,?)''',(text,key,source,int(bool(protected)),protection_reason,cls,status,now()))
            id_=c.lastrowid
            seq=self._event('hermes.propose',{'id':id_,'classification':cls,'status':status})
            return {'ok':True,'id':f'P{id_}','classification':cls,'status':status,'seq':seq,'message':f'P{id_} {cls} [{status}]'}

    def resolve(self, identifier, decision):
        if decision not in ('approve','reject'): raise IXOError('Unknown decision')
        match=re.fullmatch(r'P(\d+)',str(identifier))
        if not match: raise IXOError('Expected proposal ID such as P1')
        with self.lock, self.conn:
            p=self.conn.execute('SELECT * FROM proposals WHERE id=?',(int(match.group(1)),)).fetchone()
            if not p: raise IXOError('Proposal does not exist')
            if p['status']!='PENDING': raise IXOError('Proposal is not pending')
            if decision=='approve':
                if p['classification']=='REVIEW': raise IXOError('REVIEW needs original Hermes classifier; cannot approve here')
                if p['source']=='memory': raise IXOError('memory-origin proposals cannot auto-write')
                if p['classification']=='UNRELATED':
                    self.conn.execute('''INSERT INTO facts(text,key,source,protected,protection_reason,at)
                        VALUES(?,?,?,?,?,?)''',(p['text'],p['key'],p['source'],p['protected'],p['protection_reason'],now()))
                    status='APPROVED'
                else: status='AGREED'
            else: status='REJECTED'
            self.conn.execute('UPDATE proposals SET status=?,resolved_at=? WHERE id=?',(status,now(),p['id']))
            seq=self._event('hermes.resolve',{'id':p['id'],'status':status})
            return {'ok':True,'id':identifier,'status':status,'seq':seq,'message':f'{identifier} {status}'}

