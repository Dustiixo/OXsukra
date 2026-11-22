#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="$HOME/.local/share/oxsukra/parallax/bridge"
PROFILE="$HOME/.mozilla/native-messaging-hosts"
BIN="$HOME/.local/bin"
printf 'OX PARALLAX / Linux vault bridge installation\n\n'
printf 'App directory: %s\nFirefox native host: %s\n\n' "$PREFIX" "$PROFILE"
printf 'This creates a local Python environment and may install cryptography from PyPI.\n'
printf 'Type YES to approve installation: '
read -r confirm
[[ "$confirm" == "YES" ]] || { echo 'Cancelled';exit 1; }
command -v python3 >/dev/null || { echo 'Python3 missing';exit 1; }
mkdir -p "$PREFIX/versions" "$PROFILE" "$BIN"
chmod 700 "$PREFIX" "$PROFILE"
STAGE="$PREFIX/versions/m0.7.0"
mkdir -p "$STAGE"
cp "$HERE/parallax_host.py" "$HERE/requirements.txt" "$STAGE/"
if [[ ! -d "$PREFIX/venv" ]]; then python3 -m venv "$PREFIX/venv"; fi
"$PREFIX/venv/bin/python" -m pip install --disable-pip-version-check -r "$STAGE/requirements.txt"
cat > "$BIN/ox-parallax-native" <<LAUNCH
#!/usr/bin/env bash
exec "$PREFIX/venv/bin/python" "$STAGE/parallax_host.py"
LAUNCH
chmod 700 "$BIN/ox-parallax-native"
python3 - "$PROFILE/org.oxsukra.parallax_capture.json" "$BIN/ox-parallax-native" <<'PY'
import json,sys
with open(sys.argv[1], 'w', encoding='utf-8') as f:
    json.dump({'name':'org.oxsukra.parallax_capture','description':'PARALLAX encrypted local capture bridge',
      'path':sys.argv[2],'type':'stdio','allowed_extensions':['parallax-capture@oxsukra.local']},f,indent=2)
PY
chmod 600 "$PROFILE/org.oxsukra.parallax_capture.json"
printf '\nInstalled native bridge. Restart Firefox and connect it from PARALLAX sidebar.\n'
printf 'Firefox extension is separate: see README.md for temporary dev loading and signing.\n'
