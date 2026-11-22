"""Read-only FlowMesh trace projection for an OFFLINE, local-only visual prototype.

Never edits the original FlowMesh source or workspace. It validates the existing
receipt chain and takes a narrow, documented view of event/state fields. The
output still contains local research titles/quotes, so keep it PRIVATE.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from flowmesh import engine
from flowmesh.ledger import Ledger

EVENT_FIELDS = {
    'seq', 'stamp', 'type', 'branch', 'parent', 'question', 'reason', 'tick',
    'credits', 'total_credits', 'maximum', 'source_id', 'relevance', 'novel',
    'sha256', 'source_sha256', 'name', 'revision', 'text', 'status', 'mode',
}


def export(root: Path) -> dict:
    root = Path(root).resolve()
    proof = engine.verify(root)
    if proof.get('integrity') != 'PASS':
        raise ValueError('Workspace receipt integrity is not PASS; refusing export')
    state = engine.read(root)
    raw_events = Ledger(root).events()
    events = []
    for event in raw_events:
        e = {k: v for k, v in event.items() if k in EVENT_FIELDS}
        if 'name' in e:
            e['name'] = Path(e['name']).name
        events.append(e)
    findings = [{
        'id': x['id'], 'branch': x['branch'], 'file': Path(x['file']).name,
        'text': x['text'][:900], 'relevance': x['relevance'],
        'source_sha256': x['source_sha256'], 'tick': x['tick'],
    } for x in state.get('findings', [])]
    branches = {}
    for key, branch in state['branches'].items():
        branches[key] = {k:branch.get(k) for k in
           ('id','parent','question','kind','status','parked_reason','gain','spent','score','wake_count','created_tick')}
    return {
        'schema': 'ixo.flowmesh.visual-trace.v1',
        'dataset': 'LOCAL READ-ONLY EXPORT; not model cognition',
        'source_integrity': proof['integrity'],
        'source_mode': state.get('mode', 'unknown'),
        'goal': state['goal'], 'tick': state['tick'],
        'budget_per_tick': state['budget_per_tick'],
        'focus': state['focus'],
        'branches': branches, 'findings': findings,
        'links': state.get('links', []),
        'prompts': [{k:p.get(k) for k in ('at','kind','text','tick')} for p in state.get('prompts', [])],
        'events': events,
    }


def main():
    ap = argparse.ArgumentParser(description='Export a read-only FlowMesh trace for local visual inspection')
    ap.add_argument('--root', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    data = export(args.root)
    dest = args.out.resolve()
    if dest.exists():
        raise SystemExit('Refusing to overwrite existing export')
    dest.parent.mkdir(parents=True, exist_ok=True)
    # private / local; a local export can contain document excerpts
    with dest.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if os.name != 'nt':
        dest.chmod(0o600)
    print(f'Exported {len(data["events"])} receipt events and {len(data["findings"])} source excerpts to {dest}')
    print('PRIVATE LOCAL FILE: do not push research traces to a public repository')


if __name__ == '__main__':
    main()
