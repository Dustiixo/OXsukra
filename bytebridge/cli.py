"""Local operator entrypoint: python -m bytebridge.cli ..."""
from __future__ import annotations
import argparse, json, shutil, sys, os, re, secrets
from pathlib import Path
from .core import analyze_bytes, verify_vessel, render_self_literal, MAX_INPUT, canonical
from .ledger import initial_world, atomic_write, exclusive_lock, load, propose, commit, verify
from .projections import obj_projection, sonify
from .core import digest
from .self_receipt import import_observation, sign_observation, SCHEMA2
from .self_exchange import METHOD, source_for_revision, one_slot_literal_edit, MAX_SOURCE_BYTES


def initialize(source:Path, out:Path):
    if source.stat().st_size > MAX_INPUT: raise ValueError('Input too large')
    raw=source.read_bytes()
    v=analyze_bytes(raw,source.name)
    if out.exists() and any(out.iterdir()): raise ValueError('Output directory must be empty')
    out.mkdir(parents=True, exist_ok=True)
    # Write immutable exact bytes, never store only a lossy representation.
    (out/'original.bin').write_bytes(raw)
    atomic_write(out/'vessel.json',v)
    atomic_write(out/'world.json',initial_world(v['input']['sha256']))
    (out/'native_self_object.self').write_text(render_self_literal(v),encoding='utf-8')
    assert verify_vessel(raw,v)
    return v


def verify_directory(out:Path) -> dict:
    source=(out/'original.bin').read_bytes()
    vessel=load(out/'vessel.json')
    verify_vessel(source,vessel)
    ledger=load(out/'world.json')
    verify(ledger,vessel['input']['sha256'])
    if (out/'native_self_object.self').read_text(encoding='utf-8')!=render_self_literal(vessel):
        raise ValueError('Native Self candidate has changed')
    return {'sourceBytes':len(source),'sourceSha256':vessel['input']['sha256'],
            'representationPrint':vessel['print'],'patchCount':len(vessel['patches']),
            'spliceCount':len(vessel['splices']), 'revision':ledger['revision'],
            'status':'VERIFIED_LOCAL_ONLY', 'nativeSelfRuntime':'NOT_TESTED'}


def run(argv=None):
    p=argparse.ArgumentParser(description='OX Spatial Fabric Byte World / offline deterministic experiments')
    sub=p.add_subparsers(dest='cmd',required=True)
    x=sub.add_parser('ingest');x.add_argument('source',type=Path);x.add_argument('--out',type=Path,required=True)
    x=sub.add_parser('verify');x.add_argument('out',type=Path)
    x=sub.add_parser('propose');x.add_argument('out',type=Path);x.add_argument('--slot',required=True);x.add_argument('--value',required=True,type=float);x.add_argument('--reason',required=True)
    x=sub.add_parser('commit');x.add_argument('out',type=Path);x.add_argument('--proposal',required=True,type=Path);x.add_argument('--expected-revision',type=int,required=True);x.add_argument('--approve',action='store_true',required=True)
    x=sub.add_parser('render');x.add_argument('out',type=Path)
    x=sub.add_parser('self-gate');x.add_argument('out',type=Path)
    x=sub.add_parser('self-import');x.add_argument('out',type=Path);x.add_argument('--receipt',required=True,type=Path);x.add_argument('--key-file',required=True,type=Path);x.add_argument('--candidate',type=Path)
    x=sub.add_parser('self-export');x.add_argument('out',type=Path)
    x=sub.add_parser('self-stage');x.add_argument('out',type=Path);x.add_argument('--candidate',required=True,type=Path);x.add_argument('--key-file',required=True,type=Path);x.add_argument('--receipt-out',required=True,type=Path);x.add_argument('--runtime-commit',default='unknown-unverified');x.add_argument('--world-image',default='unknown-unverified')
    a=p.parse_args(argv)
    try:
        if a.cmd=='ingest':
            v=initialize(a.source,a.out)
            result={'status':'CREATED','sourceSha256':v['input']['sha256'],'patches':len(v['patches']),'splices':len(v['splices']),'out':str(a.out)}
        elif a.cmd=='verify':
            result=verify_directory(a.out)
        elif a.cmd=='propose':
            verify_directory(a.out)
            proposal=propose(load(a.out/'world.json'),a.slot,a.value,a.reason)
            pd=a.out/'proposals';pd.mkdir(exist_ok=True)
            atomic_write(pd/(proposal['id']+'.json'),proposal)
            result={'status':'REVIEW_REQUIRED', 'proposalId':proposal['id'], 'baseRevision':proposal['baseRevision'],'proposalPath':str(pd/(proposal['id']+'.json'))}
        elif a.cmd=='commit':
            if not a.approve: raise ValueError('Explicit approval required')
            # Constrain proposal to this world's proposal directory.
            expected=a.out/'proposals'/a.proposal.name
            if a.proposal.resolve()!=expected.resolve() or a.proposal.suffix!='.json':
                raise ValueError('Proposal outside local review directory')
            with exclusive_lock(a.out/'world.json'):
                verify_directory(a.out)
                world=load(a.out/'world.json')
                next_=commit(world,load(a.proposal),a.expected_revision)
                atomic_write(a.out/'world.json',next_)
                result={'status':'COMMITTED_MAPPING_ONLY','revision':next_['revision'],'head':next_['head']}
        elif a.cmd=='render':
            verify_directory(a.out)
            w=load(a.out/'world.json');v=load(a.out/'vessel.json')
            target=a.out/'renders'/f'rev{w["revision"]:05}'
            if target.exists(): raise ValueError('Render revision exists: never overwrite prior evidence')
            target.mkdir(parents=True,exist_ok=False)
            mesh=obj_projection(v,w['mapping']);wav=sonify(v)
            (target/'byte_world.obj').write_bytes(mesh)
            (target/'byte_view.wav').write_bytes(wav)
            receipt={'schema':'OX_BYTE_WORLD_RENDER/1','revision':w['revision'],'head':w['head'],
              'sourceSha256':v['input']['sha256'],'representationPrint':v['print'],'mapping':w['mapping'],
              'objSha256':digest(mesh),'wavSha256':digest(wav),
              'caveat':'Geometric and sonic projections, not semantic/audio reconstruction'}
            atomic_write(target/'receipt.json',receipt)
            result={'status':'RENDERED','directory':str(target),'receipt':receipt}
        elif a.cmd=='self-export':
            verify_directory(a.out)
            world=load(a.out/'world.json');vessel=load(a.out/'vessel.json')
            exported=source_for_revision(vessel,world)
            dest=a.out/'self_exchange'/f'rev{world["revision"]:05}'
            dest.mkdir(parents=True,exist_ok=False)
            (dest/'baseline.self').write_bytes(exported)
            atomic_write(dest/'manifest.json', {'schema':'OX_SELF_EXCHANGE_MANIFEST/1',
                'revision':world['revision'],'head':world['head'],
                'sourceSha256':vessel['input']['sha256'],'representationPrint':vessel['print'],
                'baselineSourceSha256':digest(exported),'nativeSelfRuntime':'NOT_VERIFIED',
                'method':METHOD})
            result={'status':'EXPORTED_LITERAL_NOT_EXECUTED','path':str(dest/'baseline.self'),
                    'baselineSourceSha256':digest(exported),'revision':world['revision']}
        elif a.cmd=='self-stage':
            verify_directory(a.out)
            if a.key_file.resolve().is_relative_to(a.out.resolve()) or a.key_file.resolve().is_relative_to(Path(__file__).resolve().parents[1]):
                raise ValueError('Signing key cannot reside inside world directory or project source')
            if a.candidate.resolve().is_relative_to(a.out.resolve()):
                raise ValueError('Edited candidate cannot reside inside world directory')
            if a.receipt_out.resolve().is_relative_to(a.out.resolve()):
                raise ValueError('Stage receipt must be outside world directory')
            if a.candidate.stat().st_size>MAX_SOURCE_BYTES: raise ValueError('Self candidate too large')
            cand=a.candidate.read_bytes()
            v=load(a.out/'vessel.json');w=load(a.out/'world.json')
            original=source_for_revision(v,w)
            exchange=a.out/'self_exchange'/f'rev{w["revision"]:05}'
            if not exchange.is_dir():raise ValueError('Export the Self baseline before staging')
            if (exchange/'baseline.self').read_bytes()!=original:
                raise ValueError('Exported Self baseline does not match verified world')
            manifest=load(exchange/'manifest.json')
            if (manifest.get('baselineSourceSha256')!=digest(original) or
                manifest.get('head')!=w['head'] or manifest.get('revision')!=w['revision'] or
                manifest.get('sourceSha256')!=w['artifactHash'] or
                manifest.get('representationPrint')!=v['print'] or
                manifest.get('method')!=METHOD):
                raise ValueError('Self export manifest mismatch')
            slot,before,value=one_slot_literal_edit(original,cand)
            raw={'schema':SCHEMA2,'sourceSha256':w['artifactHash'],
                'representationPrint':v['print'],'baseRevision':w['revision'],
                'baseHead':w['head'],'slot':slot,'before':before,'value':value,
                'nonce':secrets.token_hex(16),'observationMethod':METHOD,
                'baselineSourceSha256':digest(original),'objectSourceSha256':digest(cand),
                'runtime':{'implementation':'russellallen/self',
                    'commit':a.runtime_commit,'worldImage':a.world_image,
                    'objectOutlinerObserved':False}}
            receipt=sign_observation(raw,w,v,a.key_file.read_bytes())
            with a.receipt_out.open('xb') as f:
                f.write(canonical(receipt)); f.flush();os.fsync(f.fileno())
            result={'status':'STAGED_UNVERIFIED_SELF_LITERAL','slot':slot,'before':before,'value':value,
                    'receiptPath':str(a.receipt_out),'objectSourceSha256':digest(cand)}
        elif a.cmd=='self-import':
            with exclusive_lock(a.out/'world.json'):
                verify_directory(a.out)
                # Never accept secret from world directory or source tree.
                if a.key_file.resolve().is_relative_to(a.out.resolve()):
                    raise ValueError('Signing key cannot reside inside world directory')
                key=a.key_file.read_bytes()
                if a.receipt.stat().st_size>8192:raise ValueError('Receipt too large')
                observation=json.loads(a.receipt.read_text(encoding='utf-8'))
                nonce_file=a.out/'self_observation_nonces.json'
                seen=json.loads(nonce_file.read_text()) if nonce_file.exists() else []
                if type(seen) is not list or any(type(n) is not str for n in seen):raise ValueError('Corrupt replay registry')
                candidate=None
                if observation.get('schema')==SCHEMA2:
                    if a.candidate is None: raise ValueError('Self literal candidate required for schema 2')
                    if a.candidate.stat().st_size>MAX_SOURCE_BYTES: raise ValueError('Self candidate too large')
                    candidate=a.candidate.read_bytes()
                proposal=import_observation(observation,load(a.out/'world.json'),load(a.out/'vessel.json'),key,set(seen),candidate)
                pd=a.out/'proposals';pd.mkdir(exist_ok=True)
                atomic_write(pd/(proposal['id']+'.json'),proposal)
                atomic_write(nonce_file,seen+[observation['nonce']])
                result={'status':'REVIEW_REQUIRED','proposalPath':str(pd/(proposal['id']+'.json')),'nativeSelfRuntime':'OPERATOR_ATTESTED_NOT_INDEPENDENTLY_VERIFIED'}
        else:
            verify_directory(a.out)
            binary=shutil.which('Self') or shutil.which('self')
            result={'status':'BLOCKED' if not binary else 'AVAILABLE_UNTESTED',
                    'selfExecutable':binary,'message':'Native Self VM not executed. Set up original VM/world and evaluate native_self_object.self in the Self evaluator; export changed slots for checked reconciliation.'}
        print(json.dumps(result,indent=2,sort_keys=True));return 0
    except (ValueError,TypeError,KeyError,PermissionError,OSError,json.JSONDecodeError) as exc:
        print(json.dumps({'status':'REJECTED','error':str(exc)},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__': raise SystemExit(run())
