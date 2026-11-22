"""Strict, read-only import of operator-attested Self slot observations.

This does not prove a Self VM ran. A secret kept OUTSIDE the world folder
signs the receipt; only a separately approved proposal may change mapping.
"""
import hashlib, hmac, json, re
from pathlib import Path
from .core import canonical
from .ledger import validate_slot, verify, propose

SCHEMA='OX_SELF_SLOT_OBSERVATION/1'
SCHEMA2='OX_SELF_SLOT_OBSERVATION/2'
FROM_LITERAL={'baselineSourceSha256','objectSourceSha256','observationMethod'}
HEX=re.compile(r'^[0-9a-f]{64}$')
FIELDS={'schema','sourceSha256','representationPrint','baseRevision','baseHead','slot','before','value','nonce','runtime','mac'}
RUNTIME={'implementation','commit','worldImage','objectOutlinerObserved'}


def _check(receipt,world,vessel):
    if type(receipt) is not dict: raise ValueError('Receipt schema fields mismatch')
    if receipt.get('schema') not in (SCHEMA,SCHEMA2): raise ValueError('Wrong receipt schema')
    if set(receipt)!=(FIELDS if receipt['schema']==SCHEMA else FIELDS|FROM_LITERAL):
        raise ValueError('Receipt schema fields mismatch')
    if receipt['schema']==SCHEMA2:
        from .self_exchange import METHOD
        if receipt['observationMethod']!=METHOD or not all(type(receipt[k]) is str and HEX.fullmatch(receipt[k]) for k in ('baselineSourceSha256','objectSourceSha256')):
            raise ValueError('Invalid Self source evidence')
    if type(receipt['runtime']) is not dict or set(receipt['runtime'])!=RUNTIME: raise ValueError('Runtime metadata missing')
    runtime=receipt['runtime']
    if runtime['implementation']!='russellallen/self' or type(runtime['objectOutlinerObserved']) is not bool:
        raise ValueError('Native runtime identity invalid')
    if not all(type(runtime[k]) is str and 1<=len(runtime[k])<=180 for k in ('commit','worldImage')):
        raise ValueError('Runtime provenance missing')
    if not isinstance(receipt['nonce'],str) or not re.fullmatch(r'[0-9a-f]{32}',receipt['nonce']):
        raise ValueError('Invalid nonce')
    if type(receipt['baseRevision']) is not int or receipt['baseRevision']!=world['revision']:
        raise ValueError('Stale receipt revision')
    if receipt['baseHead']!=world['head'] or receipt['sourceSha256']!=world['artifactHash'] or receipt['representationPrint']!=vessel['print']:
        raise ValueError('Receipt bound to different world or representation')
    validate_slot(receipt['slot'],receipt['value'])
    if type(receipt['before']) not in (int,float) or receipt['before']!=world['mapping'][receipt['slot']]:
        raise ValueError('Receipt base slot mismatch')
    if type(receipt['mac']) is not str or not HEX.fullmatch(receipt['mac']):raise ValueError('Malformed MAC')


def sign_observation(observation,world,vessel,key):
    """Test fixture/operator tool only: NOT proof of native execution."""
    candidate={**observation,'mac':'0'*64}
    _check(candidate,world,vessel)
    if type(key) is not bytes or len(key)<32:raise ValueError('Key must be at least 32 bytes')
    payload={k:v for k,v in candidate.items() if k!='mac'}
    return {**payload,'mac':hmac.new(key,canonical(payload),hashlib.sha256).hexdigest()}


def import_observation(receipt,world,vessel,key,seen_nonces, candidate_source=None):
    """Returns review proposal ONLY; never executes Self source or commits a mapping."""
    verify(world,vessel['input']['sha256'])
    _check(receipt,world,vessel)
    if type(key) is not bytes or len(key)<32:raise ValueError('Key must be at least 32 bytes')
    if receipt['nonce'] in seen_nonces:raise ValueError('Replayed observation nonce')
    payload={k:v for k,v in receipt.items() if k!='mac'}
    expected=hmac.new(key,canonical(payload),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,receipt['mac']):raise ValueError('Observation authentication failed')
    if receipt['schema']==SCHEMA2:
        if type(candidate_source) is not bytes:raise ValueError('Signed Self literal source required')
        from .self_exchange import validate_source_evidence
        validate_source_evidence(receipt,vessel,world,candidate_source)
    # Even signed receipt is only an operator assertion, not a cryptographic VM attestation.
    reason = ('Self literal '+receipt['objectSourceSha256'][:16]+' verified; original Self VM not attested'
              if receipt['schema']==SCHEMA2 else
              'Operator-attested Self observation; native VM proof independently required')
    proposal=propose(world,receipt['slot'],receipt['value'],reason)
    return proposal
