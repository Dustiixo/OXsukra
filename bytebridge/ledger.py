"""Append-only review/commit ledger for *mapping* edits only.

The raw asset and its analysis vessel are immutable. No protected service
callbacks, arbitrary scripts, inherited permissions or remote endpoints.
"""
from __future__ import annotations
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import json, math, os, secrets
from .core import canonical

BOUNDS = {'depth':(0.,3.),'twist':(-6.,6.),'hue':(-180.,180.),'threshold':(0.,1.)}
DEFAULTS = {'depth':1.2, 'twist':2.0, 'hue':0., 'threshold':0.18}
GENESIS = '0' * 64


def load(path:Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def atomic_write(path:Path, obj:dict):
    temp = path.with_name(path.name + '.' + secrets.token_hex(6) + '.tmp')
    try:
        with temp.open('xb') as file:
            file.write(canonical(obj)); file.flush(); os.fsync(file.fileno())
        os.replace(temp,path)
    finally:
        temp.unlink(missing_ok=True)


@contextmanager
def exclusive_lock(path:Path):
    lock = path.with_suffix(path.suffix+'.lock')
    try:
        fd = os.open(lock, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ValueError('World locked; inspect stale lock manually') from exc
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink(missing_ok=True)


def initial_world(artifact_hash:str) -> dict:
    return {'schema':'OX_BYTE_WORLD_LEDGER/1','artifactHash':artifact_hash,
            'revision':0,'mapping':DEFAULTS.copy(),'events':[],'head':GENESIS}


def event_hash(event:dict) -> str:
    return sha256(canonical(event)).hexdigest()


def verify(world:dict, artifact_hash:str) -> bool:
    if world.get('schema')!='OX_BYTE_WORLD_LEDGER/1' or world.get('artifactHash')!=artifact_hash:
        raise ValueError('Ledger identity mismatch')
    if world.get('revision')!=len(world.get('events',[])):
        raise ValueError('Ledger revision mismatch')
    values=DEFAULTS.copy(); prev=GENESIS
    for index,item in enumerate(world['events']):
        ev = item['event']; field=ev['slot']; value=ev['value']
        validate_slot(field,value)
        if ev['sequence']!=index+1 or ev['previous']!=prev or ev['before']!=values[field]:
            raise ValueError('Ledger chain broken')
        digest=event_hash(ev)
        if item['digest']!=digest: raise ValueError('Ledger event hash mismatch')
        values[field]=value; prev=digest
    if world['head']!=prev or world['mapping']!=values:
        raise ValueError('Ledger mapping/head mismatch')
    return True


def validate_slot(name, value):
    if name not in BOUNDS or type(value) not in (float,int) or not math.isfinite(value):
        raise ValueError('Unsupported slot/value')
    lo,hi=BOUNDS[name]
    if value < lo or value > hi: raise ValueError('Slot value out of bounds')


def propose(world:dict, slot:str, value:float, reason:str) -> dict:
    validate_slot(slot,value)
    if not isinstance(reason,str) or not (5 <= len(reason.strip()) <= 300):
        raise ValueError('A specific reason (5-300 chars) is required')
    verify(world,world['artifactHash'])
    return {'schema':'OX_BYTE_WORLD_PROPOSAL/1', 'id':secrets.token_hex(12),
            'artifactHash':world['artifactHash'], 'baseRevision':world['revision'],
            'baseHead':world['head'], 'slot':slot, 'before':world['mapping'][slot],
            'value':value, 'reason':reason.strip(), 'policy':'human-review-only'}


def commit(world:dict, proposal:dict, expected_revision:int) -> dict:
    verify(world,world['artifactHash'])
    if proposal.get('schema')!='OX_BYTE_WORLD_PROPOSAL/1' or proposal.get('artifactHash')!=world['artifactHash']:
        raise ValueError('Wrong proposal or artifact')
    if type(expected_revision) is not int or expected_revision!=world['revision'] or proposal['baseRevision']!=world['revision'] or proposal['baseHead']!=world['head']:
        raise ValueError('Stale revision; reject, do not silently rebase')
    slot,value=proposal['slot'],proposal['value']
    validate_slot(slot,value)
    if proposal['before']!=world['mapping'][slot]:
        raise ValueError('Proposal base mismatch')
    reason=proposal.get('reason','')
    if not isinstance(reason,str) or len(reason.strip())<5 or len(reason)>300:
        raise ValueError('Proposal reason missing')
    event={'sequence':world['revision']+1,'previous':world['head'],
           'proposalId':proposal['id'],'slot':slot,'before':world['mapping'][slot],
           'value':value,'reason':reason}
    next_=json.loads(json.dumps(world))
    next_['mapping'][slot]=value
    next_['revision']+=1
    next_['head']=event_hash(event)
    next_['events'].append({'event':event,'digest':next_['head']})
    verify(next_,world['artifactHash'])
    return next_
