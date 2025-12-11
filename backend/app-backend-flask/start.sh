#!/bin/bash
cd "$(dirname "$0")"
echo "Setting up and starting Flask..."
[ ! -d venv ] && python3 -m venv venv
source venv/bin/activate
pip install -q selenium flask python-dotenv pandas beautifulsoup4 2>/dev/null || pip install -r requirements.txt
export EDGE_HEADLESS=0
echo "Starting Flask on http://127.0.0.1:5001 - Edge will be VISIBLE"
python3 main.py
