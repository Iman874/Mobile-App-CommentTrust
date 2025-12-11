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


def _load_env() -> None:
    """Load .env so EDGE_* vars are available even if caller did not export them."""
    env_path = Path(__file__).resolve().parents[2] / ".env"  # app-backend-flask/.env
    if not env_path.exists():
        return

    # Prefer python-dotenv if available
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(env_path)
        return
    except Exception:
        # Fallback: simple parser for KEY=VALUE lines (ignore comments/empties)
        try:
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
        except Exception:
            pass


# Load env variables at import time
_load_env()


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
    # 0. Highest priority: environment variable override
    env_binary = os.environ.get("EDGE_BINARY_PATH")
    if env_binary:
        # Direct use if exists and executable
        if os.path.isfile(env_binary):
            if not os.access(env_binary, os.X_OK):
                try:
                    os.chmod(env_binary, 0o755)
                except Exception:
                    pass
            return env_binary
    
    # If env var points to host binary but we're in Flatpak, try to find it
    # This shouldn't create wrapper - just return the path for validation
    if env_binary and not os.path.isfile(env_binary):
        # Path doesn't exist in container, might be on host
        # Return as-is and let caller handle
        return env_binary

    # 1. Search Flatpak installs (system/user) for the binary name
    flatpak_candidates = []
    for root in (
        Path("/var/lib/flatpak/app/com.microsoft.Edge"),
        Path.home() / ".local/share/flatpak/app/com.microsoft.Edge",
    ):
        if root.exists():
            try:
                found = list(root.rglob("microsoft-edge"))
                flatpak_candidates.extend(str(p) for p in found)
            except Exception:
                pass

    candidates = [
        env_binary,
        *flatpak_candidates,
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
    # Path: app-backend-flask/utils/scrapper/edge_driver_helper.py
    # Go up 2 levels to reach app-backend-flask
    module_dir = os.path.dirname(os.path.abspath(__file__))
    flask_app_dir = os.path.dirname(os.path.dirname(module_dir))

    if os_mode == "windows":
        default_path = os.path.join(
            flask_app_dir, "browser-dummy", "edgedriver_win64", "msedgedriver.exe"
        )
    else:  # linux
        default_path = os.path.join(
            flask_app_dir, "browser-dummy", "edgedriver_linux64", "msedgedriver"
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
        
        # If in Flatpak container, binary might be on host - skip file check
        if os.path.exists("/.flatpak-info"):
            # We're in Flatpak - trust EDGE_BINARY_PATH even if not visible in container
            # The path will be accessed via flatpak-spawn or wrapper
            return
        
        # Native environment - check if file exists
        if not os.path.isfile(binary_path):
            raise FileNotFoundError(
                f"Microsoft Edge binary not found at {binary_path}. "
                "Please verify the path or install Edge. "
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
    import requests
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.edge.options import Options as EdgeOptions


    # --- Remote Debugging Detection ---
    remote_port = int(os.environ.get("EDGE_REMOTE_PORT", "9222"))
    remote_debug_url = f"http://localhost:{remote_port}/json"
    try:
        resp = requests.get(remote_debug_url, timeout=1)
        if resp.status_code == 200:
            if debug:
                print(f"[EDGE_DRIVER] Detected running Edge with remote debugging at {remote_debug_url}")
            options = EdgeOptions()
            options.add_experimental_option("debuggerAddress", f"localhost:{remote_port}")
            driver = webdriver.Edge(options=options)
            if debug:
                print(f"[EDGE_DRIVER] Connected to existing Edge instance via remote debugging.")
            return driver
    except Exception:
        if debug:
            print(f"[EDGE_DRIVER] No Edge remote debugging instance detected on port {remote_port}, will launch new instance.")

    # --- Normal Edge Launch ---
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

        # Validate binary
        _validate_edge_binary(binary_path, os_mode)
        
        # If in Flatpak and binary is on host, create wrapper to access it
        if os.path.exists("/.flatpak-info") and binary_path and not os.path.isfile(binary_path):
            # We're in Flatpak and binary is on host - create wrapper
            wrapper_path = "/tmp/edge-flatpak-host-wrapper.sh"
            with open(wrapper_path, "w") as f:
                f.write("#!/bin/sh\n")
                f.write(f'exec flatpak-spawn --host {binary_path} "$@"\n')
            os.chmod(wrapper_path, 0o755)
            binary_path = wrapper_path
            if debug:
                print(f"[EDGE_DRIVER] Created Flatpak wrapper: {wrapper_path}")
        
        if not binary_path or not os.path.isfile(binary_path):
            # This shouldn't happen after validation, but be safe
            pass
        elif not os.access(binary_path, os.X_OK):
            try:
                os.chmod(binary_path, 0o755)
            except Exception:
                pass

        if debug:
            print(f"[EDGE_DRIVER] Linux binary found: {binary_path}")
        
        # Check if this is a wrapper script (for host access from Flatpak)
        is_flatpak_wrapper = binary_path.startswith("/tmp/edge-host-wrapper")
        
        # Set binary location for Linux
        options.binary_location = binary_path

        # Add common arguments for all Linux Edge instances
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--remote-debugging-port=9222")

        headless_env = os.environ.get("EDGE_HEADLESS", "1").lower()
        if headless_env in ("1", "true", "yes", "on"):
            options.add_argument("--headless=new")
        
        # Additional stability arguments
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        
        if debug:
            print(f"[EDGE_DRIVER] Headless mode: {headless_env in ('1', 'true', 'yes', 'on')}")
            print(f"[EDGE_DRIVER] Using wrapper for host access: {is_flatpak_wrapper}")
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
