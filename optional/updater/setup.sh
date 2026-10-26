#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ "$(id -u)" -ne 0 ]; then exec sudo sh "$0" "$@"; fi
exec python3 "$HERE/setup.py" "$@"
