import hashlib
import json
import os
import secrets
import re
from pathlib import Path

MAX_CHUNK = 4 * 1024 * 1024
MAX_JSON = 64 * 1024
MAX_FILE = int(os.environ.get('FUNNEL_MAX_FILE_BYTES', str(50 * 1024**3)))


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(name):
    name = str(name).replace('\\', '/').split('/')[-1].strip()
    if not name or name in {'.', '..'} or any(ord(c) < 32 for c in name):
        raise ValueError('Invalid file name')
    return name[:180]


def safe_project(project):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,40}', str(project)):
        raise ValueError('Invalid project slug (letters, digits, underscore, dash only)')
    return str(project).lower()


def safe_digest(d):
    return bool(re.fullmatch('[0-9a-f]{64}', str(d)))


def short_id():
    return secrets.token_hex(12)


def json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def init_data(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    auth = root / 'auth.json'
    if auth.exists():
        raise FileExistsError(f'{auth} already exists; refusing to rotate tokens silently')
    credentials = []
    hashed = {}
    for label, role in [(f'dev-{i}', 'member') for i in range(1, 5)] + [('hermes-bot', 'bot')]:
        token = secrets.token_urlsafe(32)
        hashed[hashlib.sha256(token.encode()).hexdigest()] = {'name': label, 'role': role}
        credentials.append((label, role, token))
    admin = secrets.token_urlsafe(32)
    hashed[hashlib.sha256(admin.encode()).hexdigest()] = {'name': 'hub-admin', 'role': 'admin'}
    credentials.append(('hub-admin', 'admin', admin))
    fd = os.open(str(auth), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as file:
        json.dump(hashed, file, indent=2)
    for folder in ['partials', 'blobs']:
        (root / folder).mkdir(exist_ok=True)
    return credentials
