import argparse
import os
import tempfile
import webbrowser
from .common import init_data


def main():
    parser=argparse.ArgumentParser(prog='python -m funnel',description='OX Funnel / HERMES Bridge v0.6 Windows pilot')
    p=parser.add_subparsers(dest='command',required=True)
    init=p.add_parser('init',help='Create shared vault and print once-only credentials')
    init.add_argument('--data',default='./vault')
    hub=p.add_parser('hub',help='Start central API, dashboard, and queue worker')
    hub.add_argument('--data',default='./vault')
    hub.add_argument('--host',default='127.0.0.1')
    hub.add_argument('--port',type=int,default=8787)
    config=p.add_parser('client-config',help='Store endpoint and member token locally')
    config.add_argument('--url',required=True)
    config.add_argument('--token',default=None,help='Optional; omitted for a secure hidden prompt')
    upload=p.add_parser('upload',help='Send one file with resume and checksum')
    upload.add_argument('file')
    upload.add_argument('--project',default='shared')
    upload.add_argument('--ollama',default=None)
    exported=p.add_parser('export-obsidian',help='Download team knowledge notes as Obsidian-compatible Markdown ZIP')
    exported.add_argument('destination')
    ask=p.add_parser('ask',help='Ask a LOCAL Ollama model about shared indexed knowledge')
    ask.add_argument('query')
    ask.add_argument('--model',required=True)
    ask.add_argument('--project',default='shared')
    watch=p.add_parser('watch',help='Continuously send stable new/changed files from a local folder')
    watch.add_argument('folder')
    watch.add_argument('--project',default='shared')
    watch.add_argument('--ollama',default=None)
    p.add_parser('desktop',help='Open Tkinter file picker sender')
    p.add_parser('bot',help='Run optional allowlisted HERMES Discord bot')
    p.add_parser('demo',help='Start a temporary, loopback-only browser pilot; Ctrl+C erases demo vault')
    p.add_parser('local-install',help='Install persistent HERMES vault/profile for the current Windows user')
    p.add_parser('local-app',help='Open persistent native HERMES app and its loopback-only hub')
    p.add_parser('local-discord',help='Run allowlisted Discord slash-command bridge with the persistent local hub')
    p.add_parser('local-operator',help='Open native review window connected to active local Discord hub')
    args=parser.parse_args()
    if args.command=='init':
        results=init_data(args.data)
        from .hub import setup_db
        setup_db(args.data)
        print('INITIALIZED. Store these tokens in a password manager; they are only printed once.\n')
        for name,role,token in results:
            print(f'{name:12} [{role:6}] {token}')
    elif args.command=='hub':
        from .hub import FunnelServer
        server=FunnelServer(args.host,args.port,args.data)
        print(f'OX Funnel: http://{args.host}:{server.server_port}/ (Ctrl+C to stop)',flush=True)
        try: server.serve_forever(poll_interval=.3)
        except KeyboardInterrupt: pass
        finally: server.shutdown();server.server_close()
    elif args.command=='client-config':
        from .client import config_set
        import getpass
        token=args.token or getpass.getpass('Paste member token (hidden input): ')
        config_set(args.url,token)
        print('Saved local client configuration. Keep the config private.')
    elif args.command=='upload':
        from .client import upload as send
        send(args.file,args.project,args.ollama)
    elif args.command=='export-obsidian':
        from .client import export_obsidian
        print('Saved:',export_obsidian(args.destination))
    elif args.command=='ask':
        from .client import ask
        ask(args.query,args.model,args.project)
    elif args.command=='watch':
        from .client import watch as loop
        loop(args.folder,args.project,args.ollama)
    elif args.command=='desktop':
        from .client import desktop
        desktop()
    elif args.command=='bot':
        from .discord_bridge import run_bot
        run_bot()
    elif args.command=='local-install':
        from .local_app import install_local, smoke_local
        result=install_local()
        print('HERMES LOCAL INSTALL:',result['status'])
        print('Vault location:',result['location'])
        print('LOCAL SMOKE:',smoke_local()['status'])
        print('No Discord, Obsidian, Java or LLM installation was performed.')
        print('Next: double-click OPEN_HERMES.bat')
    elif args.command=='local-app':
        from .local_app import run_local_app
        run_local_app()
    elif args.command=='local-discord':
        from .local_discord import run_local_discord
        run_local_discord()
    elif args.command=='local-operator':
        from .local_discord import run_local_operator
        run_local_operator()
    elif args.command=='demo':
        from .hub import FunnelServer
        # Never inherit real remote destinations into the temporary demo.
        for key in ('FUNNEL_RCLONE_REMOTE','FUNNEL_DISCORD_WEBHOOK_URL'):
            os.environ.pop(key,None)
        with tempfile.TemporaryDirectory(prefix='ox-hermes-demo-') as folder:
            credentials=init_data(folder)
            server=FunnelServer('127.0.0.1',0,folder)
            url=f'http://127.0.0.1:{server.server_port}/'
            print('\nHERMES TEMPORARY PRIVATE DEMO',flush=True)
            print('Only this computer can reach the demo. All demo records are deleted on exit.',flush=True)
            print('Use SYNTHETIC files only. Do NOT upload confidential or valuable documents.',flush=True)
            print('\nDashboard:',url,flush=True)
            print('MEMBER token:',credentials[0][2],flush=True)
            print('ADMIN  token:',credentials[-1][2],flush=True)
            print('\nPaste a token into ACCESS. Submit a dummy file, share it, or review notes.',flush=True)
            print('Press Ctrl+C to stop and remove the temporary demo vault.\n',flush=True)
            webbrowser.open(url)
            try:
                server.serve_forever(poll_interval=.3)
            except KeyboardInterrupt:
                pass
            finally:
                server.shutdown()
                server.server_close()

if __name__=='__main__': main()
