#!/usr/bin/env python3
"""
Auto-detect Edge WebDriver location and configure .env files
Works on Windows, Linux (various distros + Flatpak), macOS
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class EdgeDriverSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.flask_env = self.project_root / "backend" / "app-backend-flask" / ".env"
        self.scrapper_env = self.project_root / "backend" / "Scrapper" / ".env"
        self.os_type = platform.system()
        
    def find_edge_driver(self):
        """Cari lokasi msedgedriver di sistem"""
        print("🔍 Searching for Edge WebDriver...")
        
        # Priority 1: Check PATH
        try:
            result = subprocess.run(
                ["which", "msedgedriver"] if self.os_type != "Windows" else ["where", "msedgedriver"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                path = result.stdout.strip()
                print(f"  ✓ Found in PATH: {path}")
                return path
        except Exception as e:
            print(f"  ⚠ PATH search failed: {e}")
        
        # Priority 2: Common locations
        common_paths = {
            "Linux": [
                "/usr/bin/msedgedriver",
                "/usr/local/bin/msedgedriver",
                "/snap/bin/msedgedriver",
                "/opt/microsoft/msedge/msedgedriver",
                "/opt/microsoft/msedgedriver",
                os.path.expanduser("~/.local/bin/msedgedriver"),
            ],
            "Darwin": [  # macOS
                "/Applications/Microsoft Edge.app/Contents/MacOS/msedgedriver",
                "/usr/local/bin/msedgedriver",
            ],
            "Windows": [
                "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedgedriver.exe",
                "C:\\Program Files\\Microsoft\\Edge\\Application\\msedgedriver.exe",
                os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\Application\\msedgedriver.exe"),
            ]
        }
        
        paths_to_check = common_paths.get(self.os_type, [])
        
        for path in paths_to_check:
            if os.path.isfile(path):
                print(f"  ✓ Found at: {path}")
                return path
        
        # Priority 3: Find dengan command find (Linux only)
        if self.os_type == "Linux":
            print("  🔄 Doing deeper search (this may take a while)...")
            try:
                result = subprocess.run(
                    ["find", "/usr", "/opt", "/snap", os.path.expanduser("~"), "-name", "msedgedriver", "-type", "f"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.stdout:
                    paths = result.stdout.strip().split("\n")
                    if paths and paths[0]:
                        print(f"  ✓ Found via find: {paths[0]}")
                        return paths[0]
            except subprocess.TimeoutExpired:
                print("  ⚠ Search timeout")
            except Exception as e:
                print(f"  ⚠ Find search failed: {e}")
        
        return None
    
    def check_executable(self, path):
        """Cek apakah file executable"""
        if not os.path.isfile(path):
            return False
        
        if self.os_type == "Windows":
            return path.lower().endswith('.exe')
        else:
            return os.access(path, os.X_OK)
    
    def make_executable(self, path):
        """Buat file executable (Linux/macOS only)"""
        if self.os_type != "Windows":
            try:
                os.chmod(path, 0o755)
                print(f"  ✓ Made executable: {path}")
                return True
            except Exception as e:
                print(f"  ✗ Failed to chmod: {e}")
                return False
        return True
    
    def update_env_file(self, env_file, driver_path):
        """Update .env file dengan EDGE_DRIVER_PATH"""
        if not env_file.parent.exists():
            print(f"  ✗ Directory tidak ada: {env_file.parent}")
            return False
        
        try:
            # Read existing content
            content = ""
            if env_file.exists():
                with open(env_file, 'r') as f:
                    content = f.read()
            
            # Remove old EDGE_DRIVER_PATH if exists
            lines = content.split('\n')
            lines = [l for l in lines if not l.startswith('EDGE_DRIVER_PATH=')]
            
            # Add new setting
            if lines and lines[-1].strip():
                lines.append('')
            lines.append(f'EDGE_DRIVER_PATH={driver_path}')
            
            # Write back
            with open(env_file, 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"  ✓ Updated: {env_file}")
            return True
        except Exception as e:
            print(f"  ✗ Failed to update {env_file}: {e}")
            return False
    
    def verify_driver(self, driver_path):
        """Verify driver berfungsi"""
        try:
            result = subprocess.run(
                [driver_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                print(f"  ✓ Driver version: {version}")
                return True
        except Exception as e:
            print(f"  ⚠ Could not verify version: {e}")
        return False
    
    def run(self):
        """Main setup flow"""
        print("=" * 50)
        print("Edge WebDriver Auto-Setup")
        print("=" * 50)
        print(f"OS: {self.os_type}")
        print()
        
        # Step 1: Find driver
        driver_path = self.find_edge_driver()
        
        if not driver_path:
            print("\n✗ Edge WebDriver tidak ditemukan!")
            print("\nOptions:")
            print("  1. Install Edge: https://www.microsoft.com/en-us/edge/download")
            print("  2. Download WebDriver: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
            print("  3. Use manual setup: ./setup_edge_driver_manual.sh")
            return False
        
        # Step 2: Verify executable
        print("\n📋 Verifying driver...")
        if not self.check_executable(driver_path):
            print(f"  ⚠ File not executable, attempting to fix...")
            self.make_executable(driver_path)
        else:
            print(f"  ✓ File is executable")
        
        # Step 3: Verify works
        self.verify_driver(driver_path)
        
        # Step 4: Update .env files
        print("\n⚙️  Updating .env files...")
        self.update_env_file(self.flask_env, driver_path)
        self.update_env_file(self.scrapper_env, driver_path)
        
        # Step 5: Show result
        print("\n" + "=" * 50)
        print("✅ Setup Complete!")
        print("=" * 50)
        print(f"\nEdge Driver Path: {driver_path}")
        print(f"Flask .env: {self.flask_env}")
        print(f"Scrapper .env: {self.scrapper_env}")
        
        print("\n🧪 To test:")
        print("  cd backend/app-backend-flask")
        print("  source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows")
        print("  python3 -c \"from utils.scrapper.edge_driver_helper import create_edge_driver; driver = create_edge_driver(); print('Success!'); driver.quit()\"")
        
        return True

if __name__ == "__main__":
    setup = EdgeDriverSetup()
    success = setup.run()
    sys.exit(0 if success else 1)
