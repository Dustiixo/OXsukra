"""Explicit stdlib command-line interface for the uv Python IXO foundation."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from ixo.common import IXOError
from aixo.engine import AIXOError
from dsoe.store import DSOEError
from experience.store import ExperienceError, ORIGINS
from .system import Foundation


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog='ixo-foundation', description='IXO Python foundation (local SQLite, zero required dependencies)')
    p.add_argument('--home', type=Path, default=Path.home() / '.ixo' / 'foundation',
                   help='Local persistent state directory (default: ~/.ixo/foundation)')
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('status', help='Display IXO and AIXO state')
    w = sub.add_parser('set', help='Activate a Habitat set'); w.add_argument('workspace')
    w = sub.add_parser('propose', help='Queue a durable fact proposal; never auto-approve')
    w.add_argument('text'); w.add_argument('--source', default='user'); w.add_argument('--protected', action='store_true'); w.add_argument('--reason', default='')
    w = sub.add_parser('resolve', help='Approve/reject a pending Hermes proposal')
    w.add_argument('id'); w.add_argument('decision', choices=['approve','reject'])
    w = sub.add_parser('moon', help='Record a Moon2 stage, not a fact'); w.add_argument('stage', choices=['observe','interpret','decide','act','reflect']); w.add_argument('text')
    w = sub.add_parser('command', help='Run a legacy IXO command'); w.add_argument('line')
    sub.add_parser('capture', help='Explicitly send committed IXO events into AIXO')
    sub.add_parser('course', help='Inspect AIXO lesson sequence')
    w = sub.add_parser('lesson', help='Mark next AIXO lesson completed'); w.add_argument('id'); w.add_argument('artifact')
    w = sub.add_parser('experiment', help='Create an AIXO question'); w.add_argument('title'); w.add_argument('question')
    w = sub.add_parser('evaluate', help='Evaluate recorded expectation against current IXO state')
    w.add_argument('experiment_id', type=int)
    w.add_argument('assertion', choices=['active_set','facts_count','proposals_count','events_count','reflections_count'])
    w.add_argument('expected', help='JSON expected value (e.g. 0 or "main")')
    w = sub.add_parser('case', help='Trace one operator-supplied research case across components')
    w.add_argument('--workspace', required=True); w.add_argument('--observation', required=True)
    w.add_argument('--hypothesis', required=True); w.add_argument('--question', required=True)
    w = sub.add_parser('probe', help='FrameShift read-only linguistic candidate generation')
    w.add_argument('text')
    d = sub.add_parser('dsoe', help='DSOE provider registry, durable tasks and gated handoffs')
    actions = d.add_subparsers(dest='dsoe_action',required=True)
    actions.add_parser('providers')
    actions.add_parser('status')
    w=actions.add_parser('plan'); w.add_argument('objective'); w.add_argument('--workspace')
    w=actions.add_parser('detail'); w.add_argument('task_id')
    w=actions.add_parser('approve'); w.add_argument('task_id')
    w=actions.add_parser('dispatch'); w.add_argument('task_id')
    w=actions.add_parser('report'); w.add_argument('job_id'); w.add_argument('json_file',type=Path)
    w=actions.add_parser('fixture'); w.add_argument('job_id'); w.add_argument('json_file',type=Path)
    w=actions.add_parser('review'); w.add_argument('job_id'); w.add_argument('decision',choices=['accept','reject']); w.add_argument('--reason',required=True)
    w=actions.add_parser('evidence'); w.add_argument('job_id')
    xp = sub.add_parser('experience', help='Exposure tracking, balanced corpus and transfer-evaluation gates')
    xs = xp.add_subparsers(dest='xp_action', required=True)
    xs.add_parser('report', help='Exposure balance; no learning claims')
    xs.add_parser('sync-ixo', help='Explicitly capture IXO events as IXO-development experience')
    def labels(q):
        q.add_argument('--project', required=True)
        q.add_argument('--domain', required=True)
        q.add_argument('--origin', choices=ORIGINS, required=True)
        q.add_argument('--partition', choices=['learning','holdout'], default='learning')
        q.add_argument('--kind', choices=['material','task_case'], default='material')
    q=xs.add_parser('add', help='Label and record one text observation or held-out case')
    q.add_argument('content'); labels(q);q.add_argument('--source',required=True)
    q=xs.add_parser('file', help='Opt-in ingestion of one UTF-8 source file')
    q.add_argument('path', type=Path); labels(q)
    q=xs.add_parser('tree', help='Opt-in ingestion of a local text-source directory')
    q.add_argument('path', type=Path);labels(q);q.add_argument('--limit',type=int,default=250)
    q=xs.add_parser('select', help='Balanced manifest; no model invocation')
    q.add_argument('--scope',choices=['general','ixo'],default='general')
    q.add_argument('--limit',type=int,default=100)
    q.add_argument('--self-cap',type=float,default=0.35)
    q=xs.add_parser('export', help='Opt-in JSONL content export, excluding holdouts')
    q.add_argument('path',type=Path);q.add_argument('--scope',choices=['general','ixo'],default='general')
    q.add_argument('--limit',type=int,default=100);q.add_argument('--self-cap',type=float,default=0.35)
    q=xs.add_parser('propose-method', help='Create a candidate, not a trusted skill')
    q.add_argument('name');q.add_argument('claim');q.add_argument('--scope',choices=['general','ixo'],default='general')
    q=xs.add_parser('assess', help='Operator/test attestation against a held-out task case')
    q.add_argument('method_id',type=int);q.add_argument('record_id')
    q.add_argument('verdict',choices=['pass','fail']);q.add_argument('--assessor',choices=['operator','deterministic_test'],required=True)
    q.add_argument('--evidence',required=True)
    q=xs.add_parser('method-status', help='Read method transfer gate')
    q.add_argument('method_id',type=int)
    q=xs.add_parser('promote', help='Operator promotion in experience registry only; no fact write')
    q.add_argument('method_id',type=int)
    sub.add_parser('features', help='List live executable feature ports (not project entries)')
    w = sub.add_parser('run-feature', help='Run a feature through the same foundation runtime')
    w.add_argument('feature'); w.add_argument('--data', default='{}', help='JSON object (or @path.json)')
    sub.add_parser('feature-history', help='Inspect persisted operation receipts')
    sub.add_parser('shell', help='Interactive core command surface; type quit to exit')
    return p


def run(a: argparse.Namespace) -> dict | list:
    if a.action == 'probe':
        return Foundation.probe(a.text)
    with Foundation(a.home) as app:
        r = app.ixo
        e = app.aixo
        if a.action == 'features': return app.operations.list()
        if a.action == 'feature-history': return app.operations.receipts()
        if a.action == 'run-feature':
            data=a.data
            if data.startswith('@'):
                file=Path(data[1:]).expanduser().resolve(strict=True)
                if file.stat().st_size>128000: raise IXOError('Feature JSON input too large')
                data=file.read_text(encoding='utf-8')
            values=json.loads(data)
            return app.operations.run(a.feature,values)
        if a.action == 'experience':
            xp=app.experience
            match a.xp_action:
                case 'report': return xp.report()
                case 'sync-ixo': return xp.capture_ixo(r)
                case 'add': return xp.record(content=a.content,project=a.project,domain=a.domain,
                                              origin=a.origin,source_ref=a.source,partition=a.partition,kind=a.kind)
                case 'file': return xp.record_file(a.path,project=a.project,domain=a.domain,
                                                   origin=a.origin,partition=a.partition,kind=a.kind)
                case 'tree': return xp.ingest_tree(a.path,limit=a.limit,project=a.project,domain=a.domain,
                                                   origin=a.origin,partition=a.partition,kind=a.kind)
                case 'select': return xp.select(scope=a.scope,max_items=a.limit,self_cap=a.self_cap)
                case 'export': return xp.export(a.path,scope=a.scope,max_items=a.limit,self_cap=a.self_cap)
                case 'propose-method': return xp.propose_method(a.name,a.claim,a.scope)
                case 'assess': return xp.assess(a.method_id,a.record_id,passed=a.verdict=='pass',
                                                assessor=a.assessor,evidence_ref=a.evidence)
                case 'method-status': return xp.method_status(a.method_id)
                case 'promote': return xp.promote(a.method_id)
        if a.action == 'dsoe':
            d=app.dsoe
            match a.dsoe_action:
                case 'providers': return d.providers()
                case 'status': return d.status()
                case 'plan': return d.plan(a.objective, a.workspace)
                case 'detail': return d.detail(a.task_id)
                case 'approve': return d.store.approve(a.task_id)
                case 'dispatch': return d.dispatch(a.task_id)
                case 'report': return d.report_file(a.job_id,a.json_file)
                case 'fixture':
                    from dsoe.protocol import fixture
                    content=fixture(d.store.make_envelope(a.job_id))
                    if a.json_file.exists():raise DSOEError('Refusing to overwrite fixture file')
                    a.json_file.write_text(json.dumps(content,ensure_ascii=False,indent=2),encoding='utf-8')
                    return {'ok':True,'file':str(a.json_file),'evidence_origin':'fixture','external_runtime_executed':False}
                case 'review':
                    row=d.store.review(a.job_id,a.decision=='accept',a.reason)
                    return {'ok':True,'job_id':a.job_id,'state':row['state']}
                case 'evidence': return d.record_evidence(a.job_id)
        match a.action:
            case 'status': return app.status()
            case 'set': return r.activate_set(a.workspace)
            case 'propose': return r.propose(a.text, a.source, a.protected, a.reason)
            case 'resolve': return r.resolve(a.id, a.decision)
            case 'moon': return r.moon(a.stage, a.text)
            case 'command': return r.command(a.line)
            case 'capture': return app.capture()
            case 'course': return e.state()['lessons']
            case 'lesson': return e.complete_lesson(a.id, a.artifact)
            case 'experiment': return e.create_experiment(a.title, a.question)
            case 'evaluate':
                try: expected = json.loads(a.expected)
                except json.JSONDecodeError as err: raise IXOError('Expected must be valid JSON') from err
                return e.evaluate(a.experiment_id, a.assertion, expected, r.status(0))
            case 'case': return app.case(workspace=a.workspace, observation=a.observation, hypothesis=a.hypothesis, question=a.question)
            case 'shell':
                print('IXO core shell. Type /help or quit.', file=sys.stderr)
                while True:
                    try: line = input('IXO> ').strip()
                    except (EOFError, KeyboardInterrupt): break
                    if line in ('quit','exit'):break
                    if line:
                        try: print(json.dumps(r.command(line), ensure_ascii=False))
                        except IXOError as exc: print(json.dumps({'ok':False,'error':str(exc)}))
                return {'ok': True, 'closed': True}
    raise IXOError('Unsupported command')


def main(argv: list[str] | None = None) -> int:
    try:
        result = run(parser().parse_args(argv))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (IXOError, AIXOError, DSOEError, ExperienceError, ValueError, KeyError, OSError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}), file=sys.stderr)
        return 2
