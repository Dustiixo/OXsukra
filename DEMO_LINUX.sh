#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m flowmesh demo --root ./DEMO_TRIAL_001
python3 -m flowmesh verify --root ./DEMO_TRIAL_001
