#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE" || exit 1
exec python3 tools-server.py 5006