#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for f in extension/*.js extension/ui/*.js; do node --check "$f"; done
node tests/test_extension.cjs
node tests/test_content.cjs
python3 -m pytest -q tests/test_host.py
