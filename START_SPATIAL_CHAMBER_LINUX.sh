#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m webbrowser "file://$(pwd)/spatial_lab/index.html"
