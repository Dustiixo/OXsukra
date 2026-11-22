"""Reproducible, credential-excluding source ZIP builder for HERMES.

Run from the project root: python -m tools.build_share_zip
The build itself does NOT create credentials, start a server, or upload files.
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path


PACKAGE = 'OX_HERMES_Windows_TwoBAT_v0.6'
RELEASE = 'OX_HERMES_Windows_TwoBAT_v0.6_EDITABLE.zip'
SOURCE_DIRS = {'funnel', 'adapters', 'tests', 'tools', 'contracts'}
SAFE_EXTENSIONS = {'.py', '.md', '.txt', '.json', '.html', '.bat', '.cmd',
                   '.yaml', '.yml', '.toml', '.java', '.ebnf', '.astra', '.sl2'}
SAFE_SPECIAL = {'.gitignore', '.env.example', 'Dockerfile', 'compose.yaml', 'compose.drive.yaml'}
BLOCKED_NAMES = {'auth.json', 'client.json', 'bot.json', 'tokens.txt', 'credentials.json'}
BLOCKED_PARTS = {'__pycache__', '.venv', 'vault', 'demo_vault', '.ox_funnel',
                 '.git', 'dist', 'build', 'node_modules', 'private', 'secrets'}
SOURCE_SUFFIXES = {
    'funnel': {'.py'}, 'tests': {'.py'}, 'tools': {'.py'},
    'adapters': {'.java', '.md', '.sl2', '.astra'}, 'contracts': {'.json'},
}
ROOT_FILES = {
    'README.md', 'README_FIRST.md', '.gitignore', '.env.example',
    'STRATEGIC_ENGINEERING_PROMPT.md', 'DEPLOYMENT_FOUR_DEVS.md',
    'ALEX_SYNTRA_BRIDGE_HANDOFF.md', 'ARCHITECTURE.md', 'VERIFICATION.md',
    'VERIFICATION_v0.3.md', 'VERIFICATION_v0.4.md', 'VERIFICATION_v0.5.md',
    'VERIFICATION_v0.6.md',
    'DISCORD_PROPOSAL_POST.txt', 'OFFICIAL_REFERENCES.md',
    'BOT_AND_AUTOMATION_CATALOG.md', 'HERMES_ROUTER_CONTRACT.md',
    'DISCORD_SERVER_BLUEPRINT.md', 'PROPOSAL_FOR_THE_FOUR_OF_US.md',
    'GROUP_DISCLOSURE_TEMPLATE.md', 'TEAM_DECISIONS_TO_FILL.md',
    'MILESTONES_AND_FUTURE_PROSPECTS.md', 'PURPOSE_FIRST_ARCHITECTURE.md',
    'PILOT_V0.5.md', 'MEETING_OVERVIEW.html', 'server_blueprint.json',
    'Dockerfile', 'compose.yaml', 'compose.drive.yaml',
    'requirements-bot.txt', 'requirements-client-optional.txt',
    'INSTALL_HERMES.bat', 'OPEN_HERMES.bat',
}


def allowed(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    parts = relative.parts
    if path.is_symlink() or not path.is_file():
        return False
    if any(part in BLOCKED_PARTS for part in parts):
        return False
    if any(part.startswith('.') and part not in SAFE_SPECIAL for part in parts):
        return False
    if path.name in BLOCKED_NAMES or path.name.endswith(('.pyc', '.sqlite3', '.db', '.secret', '.token')):
        return False
    if path.name == 'MANIFEST_SHA256.txt':
        return False  # reconstructed from the exact bytes in this build
    if len(parts) == 1 and path.suffix.lower() in {'.bat', '.cmd'}:
        return path.name in {'INSTALL_HERMES.bat', 'OPEN_HERMES.bat'}
    if len(parts) == 1:
        if path.name not in ROOT_FILES:
            return False
    elif parts[0] not in SOURCE_DIRS or path.suffix.lower() not in SOURCE_SUFFIXES[parts[0]]:
        return False
    if path.name not in SAFE_SPECIAL and path.suffix.lower() not in SAFE_EXTENSIONS:
        return False
    return True


def build(destination: Path | None = None) -> Path:
    root = Path(__file__).resolve().parents[1]
    destination = destination or root / 'dist' / RELEASE
    destination.parent.mkdir(parents=True, exist_ok=True)
    paths = sorted((path for path in root.rglob('*') if allowed(root, path)),
                   key=lambda p: p.relative_to(root).as_posix())
    if not paths or not any(p.name == 'README_FIRST.md' for p in paths):
        raise RuntimeError('No valid HERMES source tree found')

    rows = []
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=True) as archive:
        for path in paths:
            data = path.read_bytes()
            relative = path.relative_to(root).as_posix()
            archive.writestr(f'{PACKAGE}/{relative}', data)
            rows.append(f'{hashlib.sha256(data).hexdigest()}  ./{relative}')
        manifest = ('\n'.join(rows) + '\n').encode('utf-8')
        archive.writestr(f'{PACKAGE}/MANIFEST_SHA256.txt', manifest)
    (root / 'MANIFEST_SHA256.txt').write_bytes(manifest)

    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('ZIP CRC verification failed')
        for row in rows:
            digest, relative = row.split('  ./', 1)
            data = archive.read(f'{PACKAGE}/{relative}')
            if hashlib.sha256(data).hexdigest() != digest:
                raise RuntimeError('SHA-256 verification failed: ' + relative)
        if len(archive.namelist()) != len(rows) + 1:
            raise RuntimeError('Unexpected ZIP entry count')

    print(f'Verified {len(paths)} source files + SHA-256 manifest: {destination}')
    return destination


if __name__ == '__main__':
    build(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None)
