#!/bin/sh
set -eu
cd "$(dirname "$0")"
python3 VERIFY_PACKAGE.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s visual_lab/tests -v
