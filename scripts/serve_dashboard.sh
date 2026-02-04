#!/bin/bash
# Serve the Trifecta dashboard over HTTP so pages can fetch JSON (avoids file:// CORS blocking)
# Usage:
#   /Users/ellisbot/.openclaw/workspace/scripts/serve_dashboard.sh
# Then open:
#   http://localhost:8000/trifecta/
#   http://localhost:8000/trifecta/profitability.html

set -euo pipefail

WORKDIR="/Users/ellisbot/.openclaw/workspace"
PORT="8000"
BIND="127.0.0.1"

cd "$WORKDIR"

echo "Serving Trifecta dashboard…"
echo "  Root: $WORKDIR"
echo "  URL : http://localhost:${PORT}/trifecta/"
echo "  Stop: Ctrl+C"
echo ""

default_py="python3"
if ! command -v "$default_py" >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install Python 3, or run: python -m http.server $PORT" >&2
  exit 1
fi

# --bind is supported by Python 3's http.server
exec "$default_py" -m http.server "$PORT" --bind "$BIND"