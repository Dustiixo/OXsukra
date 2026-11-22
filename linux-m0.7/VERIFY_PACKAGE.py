#!/usr/bin/env python3
"""Validate the packaged release against its frozen SHA-256 inventory."""
import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parent
manifest=json.loads((root/'RELEASE_MANIFEST.json').read_text())
actual={str(x.relative_to(root)) for x in root.rglob('*') if x.is_file() and '__pycache__' not in x.parts and not str(x).endswith('.pyc')}
known=set(manifest['files'])|{'RELEASE_MANIFEST.json','SHA256SUMS.txt'}
assert actual==known, f'File inventory differs: extra={actual-known} missing={known-actual}'
for item,digest in manifest['files'].items():
    h=hashlib.sha256((root/item).read_bytes()).hexdigest()
    assert h==digest,f'Hash mismatch: {item}'
print(f"PASS: version {manifest['version']}; {len(manifest['files'])} source/release files SHA-256 verified")
