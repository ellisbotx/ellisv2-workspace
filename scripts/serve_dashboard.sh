#!/bin/bash
# Serve the trifecta dashboard on a local web server
# This avoids CORS issues with file:// URLs

PORT=8080
WORKSPACE="/Users/ellisbot/.openclaw/workspace"

echo "Starting dashboard server..."
echo "Dashboard will be available at: http://localhost:$PORT/trifecta/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

cd "$WORKSPACE"
python3 -m http.server $PORT
