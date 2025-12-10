"""
Cross-platform Edge WebDriver initialization helper for Windows and Linux.

This module provides a helper function to detect the OS, locate the Edge WebDriver
and binary, and create a ready-to-use Selenium Edge driver that works on both
Windows and Linux.
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional, Tuple


def _detect_os_mode() -> str:
    """
    Detect the runtime OS mode.

    Priority:
    1. Environment variable SCRAPER_OS_MODE (fallback to "auto" if not set).
    2. CLI argument --os (parsed from sys.argv).
    3. Actual platform (platform.system()).

    Returns:
        One of: "windows", "linux", "auto" (maps to actual platform).
    """
    # Check CLI argument first
    os_mode = None
    if "--os" in sys.argv:
        try:
            idx = sys.argv.index("--os")
            if idx + 1 < len(sys.argv):
                os_mode = sys.argv[idx + 1].lower()
        except (IndexError, AttributeError):
            pass

    # Fall back to environment variable
    if not os_mode:
        os_mode = os.environ.get("SCRAPER_OS_MODE", "auto").lower()

    # Validate and resolve "auto"
    if os_mode == "auto":
        system = platform.system()
        if system == "Windows":
            os_mode = "windows"
        elif system in ("Linux", "Darwin"):
            os_mode = "linux"
        else:
            os_mode = "linux"  # default fallback for unknown systems
    elif os_mode not in ("windows", "linux"):
        # Default to auto-detect if invalid
        os_mode = _detect_os_mode.__code__.co_consts[1]  # Recursion prevention: use auto
        system = platform.system()
        os_mode = "windows" if system == "Windows" else "linux"

    return os_mode


def _find_edge_binary_windows() -> Optional[str]:
    """
    Find Microsoft Edge binary on Windows.

    Tries these candidate paths in order:
    - C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe
    - C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe
    - %LOCALAPPDATA%\\Microsoft\\Edge\\Application\\msedge.exe

    Returns:
        Path to msedge.exe if found, None otherwise.
    """
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            r"Microsoft\Edge\Application\msedge.exe",
        ),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def _find_edge_binary_linux() -> Optional[str]:
    """
    Find Microsoft Edge binary on Linux.

    Tries these candidate paths in order:
    - /usr/bin/microsoft-edge
    - /usr/bin/microsoft-edge-stable
    - /usr/bin/microsoft-edge-dev
    - /opt/microsoft/msedge/msedge

    Returns:
        Path to Edge binary if found, None otherwise.
    """
    candidates = [
        "/usr/bin/microsoft-edge",
        "/usr/bin/microsoft-edge-stable",
        "/usr/bin/microsoft-edge-dev",
        "/opt/microsoft/msedge/msedge",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def _resolve_edge_driver_path(os_mode: str) -> str:
    """
    Resolve the path to the Edge WebDriver.

    Priority:
    1. EDGE_DRIVER_PATH environment variable (if set).
    2. OS-specific default path relative to the script's module.

    Args:
        os_mode: "windows" or "linux".

    Returns:
        Path to the Edge WebDriver.
    """
    # Check environment variable first
    env_path = os.environ.get("EDGE_DRIVER_PATH")
    if env_path and os.path.isfile(env_path):
        return env_path

    # Compute default path relative to this module
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(module_dir)))

    if os_mode == "windows":
        default_path = os.path.join(
            project_root, "browser-dummy", "edgedriver_win64", "msedgedriver.exe"
        )
    else:  # linux
        default_path = os.path.join(
            project_root, "browser-dummy", "edgedriver_linux64", "msedgedriver"
        )

    return default_path


def _validate_edge_driver(driver_path: str, os_mode: str) -> None:
    """
    Validate that the Edge WebDriver exists and is executable.

    Args:
        driver_path: Path to the Edge WebDriver.
        os_mode: "windows" or "linux".

    Raises:
        FileNotFoundError: If the driver does not exist or is not executable.
    """
    if not os.path.isfile(driver_path):
        raise FileNotFoundError(
            f"Edge WebDriver not found at {driver_path}. "
            f"For {os_mode.upper()}, place the driver at: {driver_path}. "
            f"Or set EDGE_DRIVER_PATH environment variable to override."
        )

    if os_mode == "linux" and not os.access(driver_path, os.X_OK):
        raise PermissionError(
            f"Edge WebDriver at {driver_path} is not executable. "
            f"Run: chmod +x {driver_path}"
        )


def _validate_edge_binary(binary_path: Optional[str], os_mode: str) -> None:
    """
    Validate that the Edge binary is available (Linux only).

    Args:
        binary_path: Path to the Edge binary (None if not found).
        os_mode: "windows" or "linux".

    Raises:
        FileNotFoundError: On Linux, if no Edge binary is found.
    """
    if os_mode == "linux":
        if not binary_path:
            raise FileNotFoundError(
                "Microsoft Edge binary not found on Linux. "
                "Checked: /usr/bin/microsoft-edge, /usr/bin/microsoft-edge-stable, "
                "/usr/bin/microsoft-edge-dev, /opt/microsoft/msedge/msedge. "
                "Please install Edge or set EDGE_BINARY_PATH environment variable. "
                "To install on Ubuntu/Debian: sudo apt install microsoft-edge-stable"
            )


def create_edge_driver(debug: bool = False):
    """
    Create and return a ready-to-use Selenium Edge WebDriver.

    This function:
    1. Detects the runtime OS (Windows or Linux) using platform.system().
    2. Allows OS override via SCRAPER_OS_MODE environment variable or --os CLI argument.
    3. Locates the Edge WebDriver and binary (for Linux).
    4. Configures EdgeOptions with the binary location (for Linux).
    5. Initializes and returns the Selenium Edge driver.

    Args:
        debug: If True, print debug information about OS mode and paths.

    Returns:
        A Selenium webdriver.Edge instance ready to use.

    Raises:
        FileNotFoundError: If required driver or binary is missing.
        PermissionError: If driver is not executable (Linux).
        Exception: Other Selenium initialization errors.

    Example:
        driver = create_edge_driver(debug=True)
        try:
            driver.get("https://example.com")
        finally:
            driver.quit()
    """
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.edge.options import Options as EdgeOptions

    # Detect OS mode
    os_mode = _detect_os_mode()
    
    if debug:
        print(f"[EDGE_DRIVER] OS mode detected: {os_mode}")
        print(f"[EDGE_DRIVER] Platform: {platform.system()}")

    # Resolve driver path
    driver_path = _resolve_edge_driver_path(os_mode)
    
    if debug:
        print(f"[EDGE_DRIVER] Driver path: {driver_path}")

    # Validate driver exists
    _validate_edge_driver(driver_path, os_mode)

    if debug:
        print(f"[EDGE_DRIVER] Driver validated successfully")

    # Platform-specific configuration
    options = EdgeOptions()

    if os_mode == "linux":
        # Find and validate Edge binary on Linux
        binary_path = _find_edge_binary_linux()
        
        if debug:
            print(f"[EDGE_DRIVER] Linux binary candidates checked")
        
        _validate_edge_binary(binary_path, os_mode)
        
        if debug:
            print(f"[EDGE_DRIVER] Linux binary found: {binary_path}")
        
        # Set binary location for Linux
        options.binary_location = binary_path
    else:
        # Windows: binary location usually not needed (auto-detected)
        binary_path = _find_edge_binary_windows()
        if debug:
            print(
                f"[EDGE_DRIVER] Windows binary: "
                f"{binary_path if binary_path else '(auto-detected)'}"
            )

    if debug:
        print(f"[EDGE_DRIVER] Creating Selenium Edge driver service...")

    # Create service with explicit driver path
    service = EdgeService(driver_path)

    if debug:
        print(f"[EDGE_DRIVER] Initializing Selenium Edge WebDriver...")

    # Initialize driver
    driver = webdriver.Edge(service=service, options=options)

    if debug:
        print(f"[EDGE_DRIVER] Edge WebDriver initialized successfully")

    return driver


if __name__ == "__main__":
    # Simple test: create driver and print info
    import argparse

    parser = argparse.ArgumentParser(
        description="Test cross-platform Edge WebDriver initialization."
    )
    parser.add_argument(
        "--os",
        choices=["auto", "windows", "linux"],
        default="auto",
        help="Override OS mode (default: auto-detect)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print debug information"
    )

    args = parser.parse_args()

    # Set OS mode if specified
    if args.os != "auto":
        os.environ["SCRAPER_OS_MODE"] = args.os

    try:
        driver = create_edge_driver(debug=True)
        print("[TEST] Driver created successfully!")
        driver.quit()
    except Exception as e:
        print(f"[TEST] Error: {e}", file=sys.stderr)
        sys.exit(1)
