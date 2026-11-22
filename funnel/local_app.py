"""Two-click Windows owner experience: install once, launch the local app.

Never downloads, installs, or controls Discord, Obsidian, Java, or any model
runner. The hub stays on 127.0.0.1 and its persistent vault stays in the
current Windows user's LOCALAPPDATA outside the extracted source ZIP.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import threading
from pathlib import Path

from .client import write_json, read_json
from .hub import FunnelServer, setup_db


PROFILE_SCHEMA = 'hermes.local-profile.v1'


def state_root() -> Path:
    base = os.environ.get('LOCALAPPDATA')
    return (Path(base) if base else Path.home() / '.local' / 'share') / 'OX_HERMES'


def _create_owner_auth(vault: Path) -> tuple[str, str]:
    """Only the local owner and operator roles are issued on this computer."""
    vault.mkdir(parents=True, exist_ok=True)
    path = vault / 'auth.json'
    member = secrets.token_urlsafe(32)
    admin = secrets.token_urlsafe(32)
    credentials = {
        hashlib.sha256(member.encode()).hexdigest(): {'name': 'local-owner', 'role': 'member'},
        hashlib.sha256(admin.encode()).hexdigest(): {'name': 'local-admin', 'role': 'admin'},
    }
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        json.dump(credentials, handle, indent=2)
    return member, admin


def install_local() -> dict:
    """Idempotent; never overwrites a previous vault or rotates its keys."""
    root = state_root()
    profile = root / 'owner_profile.json'
    auth = root / 'vault' / 'auth.json'
    if profile.is_file() and auth.is_file():
        load_local()
        return {'status': 'already-installed', 'location': str(root)}
    if profile.exists() or auth.exists():
        raise RuntimeError('Partial local installation found. No data or tokens were changed. '\
                           'Back up the OX_HERMES folder and inspect the two files before retrying.')
    root.mkdir(parents=True, exist_ok=True)
    member, admin = _create_owner_auth(root / 'vault')
    setup_db(root / 'vault')
    write_json(profile, {'schema': PROFILE_SCHEMA, 'member_token': member,
                         'admin_token': admin})
    try:
        os.chmod(profile, 0o600)
    except OSError:
        pass
    return {'status': 'installed', 'location': str(root)}


def load_local() -> tuple[Path, str, str]:
    root = state_root()
    profile = read_json(root / 'owner_profile.json')
    if profile.get('schema') != PROFILE_SCHEMA:
        raise RuntimeError('HERMES not installed for this Windows user; run INSTALL_HERMES.bat first')
    member = profile.get('member_token')
    admin = profile.get('admin_token')
    if not all(isinstance(t, str) and len(t) >= 32 for t in (member, admin)):
        raise RuntimeError('Local credential profile damaged; no changes made')
    auth_file = root / 'vault' / 'auth.json'
    if not auth_file.is_file():
        raise RuntimeError('Local HERMES vault missing. No files recreated or reset.')
    auth = read_json(auth_file)
    for token, role in ((member, 'member'), (admin, 'admin')):
        principal = auth.get(hashlib.sha256(token.encode()).hexdigest())
        if not principal or principal.get('role') != role:
            raise RuntimeError('Stored credentials do not match the vault; no data changed')
    return root / 'vault', member, admin


def smoke_local() -> dict:
    """Non-GUI acceptance of installed credentials and localhost hub startup."""
    import json as json_module
    import urllib.request

    vault, member, _ = load_local()
    server = FunnelServer('127.0.0.1', 0, vault)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f'http://127.0.0.1:{server.server_port}/api/v1/status'
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + member})
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json_module.load(response)
        if result.get('actor') != 'local-owner' or result.get('role') != 'member':
            raise RuntimeError('Unexpected profile in local status response')
        return {'status': 'pass', 'actor': result['actor'], 'hub': '127.0.0.1'}
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def run_local_app():
    vault, member, admin = load_local()
    # Installed apps and cloud services are never launched or called by default.
    for key in ('FUNNEL_RCLONE_REMOTE', 'FUNNEL_DISCORD_WEBHOOK_URL'):
        os.environ.pop(key, None)
    server = FunnelServer('127.0.0.1', 0, vault)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    os.environ['FUNNEL_HUB_URL'] = url
    os.environ['FUNNEL_TOKEN'] = member
    try:
        from .client import desktop
        desktop(local_hub_url=url, member_token=member, admin_token=admin)
    finally:
        os.environ.pop('FUNNEL_TOKEN', None)
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
