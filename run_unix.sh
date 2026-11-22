#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
exec uv run python -m ixo_foundation --home ./state "$@"
