"""Standalone SHA-256 integrity check for the shipped FlowMesh source tree."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "docs" / "PACKAGE_SHA256.json"


def main():
    metadata = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = []
    for relative, expected in metadata["files"].items():
        dest = HERE / relative
        if dest.is_symlink() or not dest.is_file():
            failures.append(relative + " missing, not regular or symbolic link")
        elif hashlib.sha256(dest.read_bytes()).hexdigest() != expected:
            failures.append(relative + " changed")
    print(f"Checked {len(metadata['files'])} candidate source/package files")
    if failures:
        for failure in failures:
            print("FAIL", failure)
        raise SystemExit(2)
    print("PASS: all listed candidate package hashes match the candidate manifest")
    print("This does not verify runtime workspace output or guarantee code safety.")


if __name__ == "__main__":
    main()
