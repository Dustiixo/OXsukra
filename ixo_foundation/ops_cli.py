"""Run the actual IXO capabilities; source-independent command interface."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .system import Foundation


def parser():
    p=argparse.ArgumentParser(prog='ixo-ops',description='Executable IXO component manager (not a project tracker)')
    p.add_argument('--home',type=Path,default=Path.home()/'.ixo'/'foundation')
    s=p.add_subparsers(dest='action',required=True)
    s.add_parser('list',help='List invocable component functions and inputs')
    s.add_parser('history',help='Show real execution receipts')
    r=s.add_parser('run',help='Invoke existing component operation; JSON field values')
    r.add_argument('feature');r.add_argument('--data',default='{}',help='JSON object or @path.json')
    s.add_parser('console',help='Use text-based interactive component controller')
    s.add_parser('desktop',help='Start native Tkinter controller where available')
    return p


def console(hub):
    features=hub.list()
    by_id={f['id']:f for f in features}
    while True:
        print('\nIXO FEATURE OPERATIONS — every selection invokes a real component')
        for n,f in enumerate(features,1):print(f'{n:2d}. {f["id"]:29s} [{f["effect"]}]')
        raw=input('Select number, h history, or q quit: ').strip()
        if raw.lower() in ('q','quit','exit'):break
        if raw.lower()=='h':print(json.dumps(hub.receipts(10),ensure_ascii=False,indent=2));continue
        if not raw.isdecimal() or int(raw) not in range(1,len(features)+1):
            print('Unknown choice');continue
        feature=features[int(raw)-1]
        params={}
        for field in feature['fields']:
            value=input(f'  {field["name"]} [{field["type"]}]: ').strip()
            if value:params[field['name']]=value
        if feature['effect']=='approval' and input('Approval action: type YES to continue: ')!='YES':continue
        print(json.dumps(hub.run(feature['id'],params),ensure_ascii=False,indent=2,default=str))


def main(argv=None):
    args=parser().parse_args(argv)
    if args.action=='desktop':
        from .native_control import main as native_main
        return native_main(args.home)
    with Foundation(args.home) as app:
        hub=app.operations
        if args.action=='list':out=hub.list()
        elif args.action=='history':out=hub.receipts()
        elif args.action=='console':
            try:console(hub)
            except (EOFError,KeyboardInterrupt):pass
            return 0
        else:
            raw=args.data
            if raw.startswith('@'):
                path=Path(raw[1:]).expanduser().resolve(strict=True)
                if path.stat().st_size>128000:raise ValueError('JSON input too large')
                raw=path.read_text(encoding='utf-8')
            try:values=json.loads(raw)
            except json.JSONDecodeError as exc:raise ValueError('Invalid JSON input') from exc
            out=hub.run(args.feature,values)
        print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
        return 0 if not isinstance(out,dict) or out.get('passed',True) else 2


if __name__=='__main__':
    try:sys.exit(main())
    except (ValueError,OSError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)}),file=sys.stderr)
        sys.exit(2)
