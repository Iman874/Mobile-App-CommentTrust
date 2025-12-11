#!/bin/sh
# Wrapper to launch Microsoft Edge via Flatpak
# Use flatpak-spawn --host when running inside Flatpak (e.g., VS Code Flatpak)
if command -v flatpak-spawn >/dev/null 2>&1; then
    # Running inside Flatpak - use flatpak-spawn to access host
    exec flatpak-spawn --host flatpak run com.microsoft.Edge "$@"
else
    # Running on host - use flatpak directly
    exec flatpak run com.microsoft.Edge "$@"
fi
