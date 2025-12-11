#!/bin/bash
# Test script to verify Edge opens visibly (non-headless)

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "Testing Edge WebDriver in VISIBLE (non-headless) mode"
echo "============================================================"
echo ""

# Activate venv
source venv/bin/activate

# Set environment
export EDGE_HEADLESS=0
export EDGE_BINARY_PATH=/usr/bin/microsoft-edge-stable
export EDGE_DRIVER_PATH=/home/iman874/Downloads/edgedriver_linux64/msedgedriver

echo "Configuration:"
echo "  EDGE_HEADLESS: $EDGE_HEADLESS"
echo "  EDGE_BINARY_PATH: $EDGE_BINARY_PATH"
echo "  EDGE_DRIVER_PATH: $EDGE_DRIVER_PATH"
echo ""
echo "============================================================"
echo ""

# Run test
python test_edge_visible.py
