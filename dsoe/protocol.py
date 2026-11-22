"""Portable bridge schema. External Pantheon APIs are not assumed.

An actual third-party connector must translate this envelope to/from its
verified native API. Fixtures let us test orchestration without running agents.
"""
from __future__ import annotations
from .store import DSOEError, bounded

FIELDS = {
    'pantheonos':'team_plan',
    'odysseus_pantheon':'workflow',
    'duskript_pantheon':'assessment',
}

def validate_stage(provider: str, result: dict) -> None:
    field=FIELDS.get(provider)
    if field is None:raise DSOEError('Unsupported provider')
    data=result.get(field)
    if provider in ('pantheonos','odysseus_pantheon'):
        if not isinstance(data,list) or not 1<=len(data)<=20:
            raise DSOEError(f'{field} must contain 1 to 20 structured stages')
        for step in data:
            if not isinstance(step,dict) or not isinstance(step.get('title'),str):
                raise DSOEError(f'{field} requires stage title')
            bounded(step['title'],200)
    else:
        if not isinstance(data,dict):raise DSOEError('assessment must be a structured object')
        if data.get('verdict') not in ('accept','revise','reject'):
            raise DSOEError('assessment verdict must be accept, revise or reject')
        bounded(data.get('rationale'),500)

def fixture(envelope: dict) -> dict:
    """Clearly labelled test data; never claim this came from upstream."""
    request=envelope['request']
    provider=request['provider']
    if provider=='pantheonos': content={'team_plan':[{'title':'Gather evidence','operator_approval':True}]}
    elif provider=='odysseus_pantheon': content={'workflow':[{'title':'Inspect workspace state','operator_approval':True}]}
    elif provider=='duskript_pantheon': content={'assessment':{'verdict':'revise','rationale':'Fixture provides no real model evidence'}}
    else:raise DSOEError('Unsupported provider')
    return {'protocol':'dsoe-json-file-v1','job_id':request['job_id'],'provider':provider,
            'request_sha256':envelope['request_sha256'],
            'summary':'SIMULATED fixture; no third-party runtime executed',
            'evidence_origin':'fixture', **content}
