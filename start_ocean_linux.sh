#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if ! command -v godot >/dev/null 2>&1; then
  echo "Godot not installed. Open godot/project.godot with the native Godot 4.6 editor." >&2
  exit 2
fi
exec godot --path godot
