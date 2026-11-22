"""Pack this repository into a *single downloadable, double-clickable* Windows CMD.

Only stdlib Python. The embedded source zip is SHA-256 checked before any
code runs. Rebuild after modifying source or documentation.
"""
from pathlib import Path
import base64
import hashlib
import io
import zipfile
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'Install_IXO_Live_Features_v0_4_0.cmd'
BLACKLIST = {'.git', '.venv', '__pycache__', 'state', 'dist', 'build', '.pytest_cache', '.ruff_cache'}


def include(path: Path) -> bool:
    parts = path.relative_to(ROOT).parts
    if any(part in BLACKLIST for part in parts):
        return False
    if path.suffix in {'.pyc', '.db', '.sqlite3'} or path.name.endswith('.sqlite3-wal'):
        return False
    return path.is_file()


def pack() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for file in sorted(ROOT.rglob('*')):
            if include(file):
                rel = file.relative_to(ROOT).as_posix()
                z.write(file, arcname=rel)
    return b.getvalue()


def main():
    source = pack()
    checksum = hashlib.sha256(source).hexdigest()
    ps = (ROOT / 'installer' / 'OneClick.ps1').read_text(encoding='utf-8').replace('__PAYLOAD_SHA256__', checksum)
    # The powershell code uses $env:IXO_INSTALLER instead of concatenating an
    # untrusted path into a PowerShell command line.
    header = r'''@echo off
setlocal
set "IXO_INSTALLER=%~f0"
echo Installing IXO Live Feature Control for the current Windows user...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$f=$env:IXO_INSTALLER;$s=[IO.File]::ReadAllText($f);$m=[regex]::Match($s,'(?ms)^::IXO-PS-BEGIN\r?\n(.*?)^::IXO-PS-END\s*$');if(!$m.Success){throw 'Setup script missing'}; & ([scriptblock]::Create($m.Groups[1].Value))"
set "IXO_RC=%ERRORLEVEL%"
if not "%IXO_RC%"=="0" (
 echo Installation could not complete. Check the error above.
 pause
)
exit /b %IXO_RC%
::IXO-PS-BEGIN
'''.replace('\\"', '"')
    # Normalize CRLF; Windows cmd.exe supports that reliably.
    lines = base64.b64encode(source).decode('ascii')
    wrapped = '\n'.join(lines[i:i+76] for i in range(0, len(lines), 76))
    installer = header + ps + '\n::IXO-PS-END\n::IXO-PAYLOAD-BEGIN\n' + wrapped + '\n::IXO-PAYLOAD-END\n'
    OUT.write_bytes(installer.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))
    print('Built', OUT, 'bytes', OUT.stat().st_size, 'source_sha256', checksum)


if __name__ == '__main__':
    sys.exit(main())
