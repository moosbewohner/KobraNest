#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(id -u)" -ne 0 ]; then exec sudo sh "$0" "$@"; fi
command -v python3 >/dev/null
command -v openssl >/dev/null
if [ -f /etc/s1-boot-ready ]; then
    if [ -f /usr/share/kobranest-update/version.json ]; then
        python3 "$HERE/install.py" --root / --platform printer --patch-web --if-missing
        exit 0
    fi
    python3 -c 'import sys; sys.path.insert(0,sys.argv[1]); import updater; updater.require_idle(); updater.sync_clock()' "$HERE"
    python3 "$HERE/install.py" --root / --platform printer --patch-web --if-missing
    python3 - <<'PY'
from pathlib import Path
import os,signal
for p in Path('/proc').iterdir():
    if not p.name.isdigit(): continue
    try:
        args=(p/'cmdline').read_bytes().split(b'\0')
        if b'/usr/local/sbin/s1-web' in args[:2]: os.kill(int(p.name),signal.SIGTERM)
    except OSError: pass
PY
else
    python3 "$HERE/install.py" --root / --platform pi --if-missing
fi
echo 'Updater installed. Printer WebUI: reload and sign in again. Pi: sudo s1-update --help'
