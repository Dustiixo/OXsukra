"""Non-destructive Windows operator onboarding and optional Discord bot runner.

Does not create a Discord app, enroll machines, or upload data.
"""
from __future__ import annotations
import getpass
import importlib.util
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

HOME=Path.home()/'.ox_funnel'
BOT_CONFIG=HOME/'bot.json'


def valid_local_or_secure_url(s: str) -> bool:
    """Require HTTPS, localhost HTTP, or an RFC1918/Tailscale HTTP endpoint."""
    s=s.strip()
    if not s or any(c.isspace() for c in s):
        return False
    try:
        u=urlsplit(s)
        if u.scheme not in ('http','https') or not u.hostname or u.username or u.password:
            return False
        if u.path not in ('','/') or u.query or u.fragment:
            return False
        _port=u.port  # Validate numeric port syntax if supplied.
        if u.scheme == 'https':
            return True
        if u.hostname == 'localhost':
            return True
        ip=ipaddress.ip_address(u.hostname)
        if ip.version != 4:
            return ip.is_loopback
        return ip.is_loopback or ip.is_private or ip in ipaddress.ip_network('100.64.0.0/10')
    except (ValueError,TypeError):
        return False


def validate_bot_config(data):
    ids=[x.strip() for x in data.get('DISCORD_ALLOWED_IDS','').split(',') if x.strip()]
    guild=data.get('DISCORD_GUILD_ID','')
    if not guild.isdigit() or not 15<=len(guild)<=22:
        raise ValueError('Guild ID must be a Discord snowflake identifier')
    if not ids or len(ids)>20 or any(not x.isdigit() or not 15<=len(x)<=22 for x in ids):
        raise ValueError('Enter comma-separated authorized Discord user IDs')
    for k in ('DISCORD_BOT_TOKEN','FUNNEL_BOT_API_TOKEN'):
        if len(data.get(k,''))<20:
            raise ValueError(f'{k} appears missing or invalid')
    if not valid_local_or_secure_url(data.get('FUNNEL_HUB_URL','')):
        raise ValueError('Hub must use HTTPS, loopback, or trusted private LAN/VPN URL')
    return True


def bot_config():
    print('Optional HERMES bot setup. Never paste these credentials in Discord.')
    if BOT_CONFIG.exists():
        answer=input('Existing private bot config found. Type REPLACE to rotate: ').strip()
        if answer != 'REPLACE':
            print('No changes made.')
            return 1
    record={
        'DISCORD_GUILD_ID':input('Staging Discord guild ID: ').strip(),
        'DISCORD_ALLOWED_IDS':input('Approved Discord user IDs (comma-separated): ').strip(),
        'DISCORD_BOT_TOKEN':getpass.getpass('Discord bot token (hidden): ').strip(),
        'FUNNEL_BOT_API_TOKEN':getpass.getpass('Hub hermes-bot token (hidden): ').strip(),
        'FUNNEL_HUB_URL':input('Private hub URL [http://127.0.0.1:8787]: ').strip() or 'http://127.0.0.1:8787'
    }
    try:
        validate_bot_config(record)
    except ValueError as exc:
        print('Cannot save:',exc)
        return 1
    HOME.mkdir(mode=0o700,parents=True,exist_ok=True)
    temp=BOT_CONFIG.with_suffix('.tmp')
    try:
        fd=os.open(str(temp),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(record,f,indent=2)
        os.replace(temp,BOT_CONFIG)
    finally:
        if temp.exists(): temp.unlink()
    try: os.chmod(BOT_CONFIG,0o600)
    except OSError: pass
    print('Credentials saved outside the shareable ZIP. Keep your Windows account secure.')
    return 0


def run_bot():
    if not BOT_CONFIG.is_file():
        print('No private bot configuration. Run step 07 first.')
        return 1
    try:
        rec=json.loads(BOT_CONFIG.read_text(encoding='utf-8'))
        validate_bot_config(rec)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print('Invalid local bot configuration:',type(exc).__name__)
        return 1
    env=os.environ.copy()
    env.update(rec)
    # Bot is user-started only; never spawn as a hidden background service.
    print('Starting HERMES Discord bot in foreground. Ctrl+C to stop.')
    try:
        return subprocess.run([sys.executable,'-m','funnel','bot'],env=env,check=False).returncode
    except KeyboardInterrupt:
        return 0


def doctor():
    print('\nOX HERMES system diagnostic (offline, no secrets displayed)')
    print('Python:',sys.version.split()[0], '>=3.10:',sys.version_info>=(3,10))
    print('Hub/client:', 'READY' if Path('funnel/hub.py').is_file() and Path('funnel/client.py').is_file() else 'MISSING')
    print('Discord package:', 'optional' if not importlib.util.find_spec('discord') else 'installed')
    print('rclone executable:', 'available' if shutil.which('rclone') else 'not installed (optional)')
    print('Docker executable:', 'available' if shutil.which('docker') else 'not installed (optional)')
    print('Private member config:', 'present' if (HOME/'config.json').is_file() else 'not configured')
    print('Private bot config:', 'present' if BOT_CONFIG.is_file() else 'not configured')
    print('Hub auth:', 'present (do not share)' if Path('vault/auth.json').is_file() else 'not initialized')
    print('Network access / Discord / Drive: NOT TESTED BY THIS DIAGNOSTIC')
    return 0


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if args==['doctor']:
        return doctor()
    if args==['bot-config']:
        return bot_config()
    if args==['bot-run']:
        return run_bot()
    print('Usage: python tools/hermes_operator.py [doctor|bot-config|bot-run]')
    return 2

if __name__=='__main__':
    raise SystemExit(main())
