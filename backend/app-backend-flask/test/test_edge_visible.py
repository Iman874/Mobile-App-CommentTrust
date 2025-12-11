#!/usr/bin/env python3
"""
Test script to verify Edge opens in visible (non-headless) mode.
Edge window should appear on your desktop.
"""
import os
import sys

# Set environment before importing
os.environ['EDGE_HEADLESS'] = '0'
os.environ['EDGE_BINARY_PATH'] = '/usr/bin/microsoft-edge-stable'
os.environ['EDGE_DRIVER_PATH'] = '/home/iman874/Downloads/edgedriver_linux64/msedgedriver'

from utils.scrapper.edge_driver_helper import create_edge_driver

print("=" * 60)
print("Testing Edge in VISIBLE (non-headless) mode")
print("=" * 60)
print(f"EDGE_HEADLESS: {os.getenv('EDGE_HEADLESS')}")
print(f"EDGE_BINARY_PATH: {os.getenv('EDGE_BINARY_PATH')}")
print(f"EDGE_DRIVER_PATH: {os.getenv('EDGE_DRIVER_PATH')}")
print("=" * 60)

try:
    print("\n[1] Creating Edge driver...")
    driver = create_edge_driver(debug=True)
    
    print("\n[2] Edge driver created successfully!")
    print("[3] Opening test page...")
    driver.get("https://www.google.com")
    
    print("\n" + "=" * 60)
    print("SUCCESS! Edge window should be visible on your desktop.")
    print("You should see Google homepage.")
    print("=" * 60)
    
    input("\nPress ENTER to close Edge and exit...")
    
    driver.quit()
    print("Edge closed. Test complete.")
    
except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
