#!/bin/sh
# Launch Edge via Flatpak with remote debugging enabled
# This should be run BEFORE starting the scraper

REMOTE_DEBUG_PORT=9222

# Kill existing Edge instances
echo "Stopping existing Edge instances..."
flatpak-spawn --host pkill -f "com.microsoft.Edge" 2>/dev/null || true
sleep 2

# Launch Edge with remote debugging
echo "Starting Edge with remote debugging on port $REMOTE_DEBUG_PORT..."
flatpak-spawn --host flatpak run \
  com.microsoft.Edge \
  --remote-debugging-port=$REMOTE_DEBUG_PORT \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir=/tmp/edge-selenium-profile \
  "about:blank" &

echo "Edge launched. WebDriver will connect to port $REMOTE_DEBUG_PORT"
echo "Press Ctrl+C to stop Edge when done."
wait
