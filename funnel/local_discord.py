"""Optional local-only Discord pilot bridge. No token is saved to disk.

Run after INSTALL_HERMES.bat; bot and hub share the installed local owner vault.
Only allowlisted slash commands are supported by discord_bridge; no scraping.
"""
import getpass
import json
import os
import tempfile
import threading
import webbrowser
from pathlib import Path

from .local_app import load_local, state_root
from .hub import FunnelServer


def valid_ids(value, multiple=False):
    fields=[s.strip() for s in value.split(',')]
    if not multiple and len(fields)!=1:
        raise ValueError('Provide one ID')
    if not fields or any(not x.isdecimal() or len(x)>22 or int(x)==0 for x in fields):
        raise ValueError('IDs must be positive numeric Discord IDs')
    if len(set(fields))!=len(fields):
        raise ValueError('Duplicate IDs')
    return ','.join(fields)


def load_ids(path):
    if not path.is_file():
        return None
    data=json.loads(path.read_text(encoding='utf-8'))
    return (valid_ids(data['guild']),valid_ids(data['allowed'],multiple=True))


def save_ids(path,guild,allowed):
    path.parent.mkdir(parents=True,exist_ok=True)
    payload={'schema':'hermes.discord-local.v1','guild':valid_ids(guild),
             'allowed':valid_ids(allowed,multiple=True)}
    # Only server/user IDs, never bot tokens, are written to this file.
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,
                                     prefix='discord_ids_',suffix='.tmp',delete=False) as f:
        tmp=Path(f.name)
        json.dump(payload,f,indent=2)
    os.replace(str(tmp),str(path))


def ask_ids(path):
    prior=load_ids(path)
    if prior:
        print('Existing server/allowed user IDs:',prior[0],'/',prior[1],flush=True)
        keep=input('Keep these IDs? [Y/n]: ').strip().lower()
        if keep in ('','y','yes'):
            return prior
    guild=valid_ids(input('Your Discord SERVER ID (not app ID): ').strip())
    allowed=valid_ids(input('Your Discord USER ID, comma-separated if more: ').strip(),multiple=True)
    save_ids(path,guild,allowed)
    return guild,allowed


def run_local_discord():
    vault,owner_token,_=load_local()
    try:
        import discord  # optional dependency; checked before asking for secrets
    except ImportError as e:
        raise RuntimeError('Discord bot dependency missing. Run 03_CONNECT_DISCORD.bat.') from e
    if tuple(int(x) for x in discord.__version__.split('.')[:2]) < (2,4):
        raise RuntimeError('discord.py 2.4+ required')
    config=state_root()/'discord_connection.json'
    print('\nHERMES Discord test: private local vault; no message scraping.',flush=True)
    guild,allowed=ask_ids(config)
    bot_token=getpass.getpass('Paste Discord BOT token (hidden; never saved): ').strip()
    if len(bot_token)<20:
        raise ValueError('No valid-looking bot token supplied; nothing connected.')
    print('IMPORTANT: bot token only lives in this process. Do not share it.',flush=True)
    # Fixed port is needed so the optional bot can contact this specific hub.
    # OPEN_HERMES uses a different ephemeral port; close it for this pilot.
    server=FunnelServer('127.0.0.1',8787,vault)
    thread=threading.Thread(target=server.serve_forever,daemon=True)
    old={k:os.environ.get(k) for k in ('DISCORD_BOT_TOKEN','DISCORD_GUILD_ID','DISCORD_ALLOWED_IDS',
                                       'FUNNEL_HUB_URL','FUNNEL_BOT_API_TOKEN')}
    os.environ.update({'DISCORD_BOT_TOKEN':bot_token,'DISCORD_GUILD_ID':guild,
                       'DISCORD_ALLOWED_IDS':allowed,'FUNNEL_HUB_URL':'http://127.0.0.1:8787',
                       'FUNNEL_BOT_API_TOKEN':owner_token})
    thread.start()
    print('Local HERMES dashboard: http://127.0.0.1:8787',flush=True)
    print('Use ONLY a small synthetic attachment for the first /funnel_ingest test.',flush=True)
    webbrowser.open('http://127.0.0.1:8787')
    try:
        from .discord_bridge import run_bot
        run_bot()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        for k,v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v


def run_local_operator():
    """Native reviewer attached to the hub already managed by CONNECT_DISCORD."""
    import urllib.request
    from .client import desktop
    vault,member,admin=load_local()
    url='http://127.0.0.1:8787'
    req=urllib.request.Request(url+'/api/v1/status',headers={'Authorization':'Bearer '+member})
    try:
        with urllib.request.urlopen(req,timeout=3) as response:
            if response.status!=200:raise RuntimeError('Hub response not ready')
    except Exception as exc:
        raise RuntimeError('Discord hub is not running. First launch 03_CONNECT_DISCORD.bat.') from exc
    old={k:os.environ.get(k) for k in ('FUNNEL_HUB_URL','FUNNEL_TOKEN')}
    os.environ['FUNNEL_HUB_URL']=url
    os.environ['FUNNEL_TOKEN']=member
    try:desktop(local_hub_url=url,member_token=member,admin_token=admin)
    finally:
        for k,v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v

