#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m compileall -q bytebridge engine.py run.py tests
python -m unittest discover -s tests -v
if command -v node >/dev/null; then
  node --check static/splice.js
  node --check static/byte.js
  node tests/test_splice_core.mjs
  node tests/test_byte_core.mjs
else
  echo 'Node is absent: JavaScript tests NOT RUN; install Node >= 18 for full gate' >&2
fi
