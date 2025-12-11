#!/bin/bash
# Wrapper script to run Flask with correct environment
# This ensures Edge browser is visible (non-headless)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=================================================="
echo "Starting Flask Backend with Visible Edge Browser"
echo "=================================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please create venv first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate venv
echo "[1] Activating virtual environment..."
source venv/bin/activate

# Check if selenium is installed
if ! python -c "import selenium" 2>/dev/null; then
    echo ""
    echo "[2] Installing dependencies..."
    pip install -r requirements.txt
fi

# Set environment variables
export EDGE_HEADLESS=0
export EDGE_BINARY_PATH=/usr/bin/microsoft-edge-stable
export EDGE_DRIVER_PATH=/home/iman874/Downloads/edgedriver_linux64/msedgedriver

echo ""
echo "[3] Configuration:"
echo "    - EDGE_HEADLESS=0 (browser will be VISIBLE)"
echo "    - EDGE_BINARY=$EDGE_BINARY_PATH"
echo "    - EDGE_DRIVER=$EDGE_DRIVER_PATH"
echo ""
echo "=================================================="
echo "Flask server will start on http://127.0.0.1:5001"
echo "Edge browser will open VISIBLY when scraping"
echo "You can solve captcha/login manually in the browser"
echo "=================================================="
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run Flask
python main.py
