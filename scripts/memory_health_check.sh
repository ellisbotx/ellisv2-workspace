#!/usr/bin/env bash
set -euo pipefail
cd /Users/ellisbot/.openclaw/workspace
python3 scripts/memory_selfheal.py "$@"
