"""Command line shell for local research capture; no background agent."""
import argparse
import json
import os
from pathlib import Path
from .core import ResearchStore,fetch_public_page


def main(argv=None):
    p=argparse.ArgumentParser(description='OX Research Ecology M0.1 (local-first)')
    p.add_argument('--db',default=str(Path.home()/'.oxsukra'/'research-ecology'/'events.sqlite3'))
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('plan');a.add_argument('topic');a.add_argument('project');a.add_argument('when');a.add_argument('minutes',type=int)
    a=sub.add_parser('start');a.add_argument('topic');a.add_argument('project');a.add_argument('--slotline-ref')
    a=sub.add_parser('capture');a.add_argument('url');a.add_argument('--objective',required=True);a.add_argument('--text-file');a.add_argument('--fetch',action='store_true');a.add_argument('--session')
    a=sub.add_parser('insight');a.add_argument('project');a.add_argument('claim');a.add_argument('--source-id',action='append',default=[]);a.add_argument('--session')
    a=sub.add_parser('tick');a.add_argument('source_id');a.add_argument('level',choices=['looked_at','skimmed','notes','explained','applied']);a.add_argument('--session')
    a=sub.add_parser('recap');a.add_argument('session')
    sub.add_parser('verify');sub.add_parser('export'); sub.add_parser('desktop')
    args=p.parse_args(argv)
    if args.cmd=='desktop':
        from .desktop import run
        run(args.db); return
    store=ResearchStore(args.db)
    try:
        if args.cmd=='plan': result=store.plan(args.topic,args.project,args.when,args.minutes)
        elif args.cmd=='start': result={'session':store.start(args.topic,args.project,args.slotline_ref)}
        elif args.cmd=='capture':
            if args.fetch==bool(args.text_file): p.error('Provide exactly one of --fetch or --text-file')
            data=fetch_public_page(args.url) if args.fetch else Path(args.text_file).read_text('utf-8')
            result=store.source(args.url,data,args.objective,args.session)
        elif args.cmd=='insight':result=store.insight(args.claim,args.source_id,args.project,args.session)
        elif args.cmd=='tick':result=store.reviewed(args.source_id,args.level,args.session)
        elif args.cmd=='recap':result=store.recap(args.session)
        elif args.cmd=='verify':result={'verified':store.verify()}
        else:result=store.export()
        print(json.dumps(result,ensure_ascii=False,indent=2))
    finally:store.close()
if __name__=='__main__': main()
