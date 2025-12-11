#!/bin/bash

# Script untuk mendeteksi dan setup Microsoft Edge Driver pada Linux
# Supports: Ubuntu/Debian, Fedora/RHEL, Arch, Flatpak

set -e

echo "=========================================="
echo "Microsoft Edge Driver Setup untuk Linux"
echo "=========================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_NAME=$NAME
else
    echo "Error: Tidak bisa deteksi Linux distro"
    exit 1
fi

echo "Detected OS: $OS_NAME ($OS)"
echo ""

# Function untuk cek apakah command ada
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Cek apakah Edge sudah terinstall
check_edge_installed() {
    if command_exists msedgedriver; then
        EDGE_PATH=$(which msedgedriver)
        echo "✓ msedgedriver ditemukan: $EDGE_PATH"
        return 0
    elif command_exists microsoft-edge-stable; then
        echo "✓ Microsoft Edge browser ditemukan"
        EDGE_PATH="/usr/bin/msedgedriver"
        return 1
    else
        return 2
    fi
}

# Install Edge berdasarkan distro
install_edge() {
    case "$OS" in
        ubuntu|debian)
            echo "Installing untuk Ubuntu/Debian..."
            curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
            sudo install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/
            sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list'
            sudo apt update
            sudo apt install -y microsoft-edge-stable
            ;;
        fedora|rhel|centos)
            echo "Installing untuk Fedora/RHEL..."
            sudo dnf install -y microsoft-edge-stable
            ;;
        arch|manjaro)
            echo "Installing untuk Arch Linux..."
            sudo pacman -S --noconfirm microsoft-edge-stable
            ;;
        *)
            echo "Distro $OS_NAME tidak langsung didukung"
            echo "Manual install dari: https://www.microsoft.com/en-us/edge/download"
            return 1
            ;;
    esac
}

# Main logic
echo "Step 1: Memeriksa instalasi Edge..."
if check_edge_installed; then
    echo ""
    echo "Step 2: Edge sudah terinstall dengan msedgedriver ✓"
elif [ $? -eq 1 ]; then
    echo ""
    echo "Step 2: Edge browser ada tapi msedgedriver belum"
    echo "Anda perlu download WebDriver dari: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
else
    echo ""
    echo "Step 2: Edge belum terinstall"
    read -p "Install Microsoft Edge sekarang? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_edge
        check_edge_installed
        EDGE_PATH=$(which msedgedriver)
    else
        echo "Instalasi dibatalkan"
        exit 1
    fi
fi

# Get actual path
if [ -z "$EDGE_PATH" ]; then
    EDGE_PATH=$(which msedgedriver)
fi

echo ""
echo "Step 3: Update .env files..."

# Update Flask .env
FLASK_ENV="/home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/app-backend-flask/.env"
if [ -f "$FLASK_ENV" ]; then
    # Hapus line lama jika ada
    sed -i '/^EDGE_DRIVER_PATH=/d' "$FLASK_ENV"
    # Tambah yang baru
    echo "EDGE_DRIVER_PATH=$EDGE_PATH" >> "$FLASK_ENV"
    echo "✓ Updated: $FLASK_ENV"
else
    echo "⚠ File tidak ditemukan: $FLASK_ENV"
fi

# Update Scrapper .env
SCRAPPER_ENV="/home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/Scrapper/.env"
if [ -f "$SCRAPPER_ENV" ]; then
    # Hapus line lama jika ada
    sed -i '/^EDGE_DRIVER_PATH=/d' "$SCRAPPER_ENV"
    # Tambah yang baru
    echo "EDGE_DRIVER_PATH=$EDGE_PATH" >> "$SCRAPPER_ENV"
    echo "✓ Updated: $SCRAPPER_ENV"
else
    echo "⚠ File tidak ditemukan: $SCRAPPER_ENV"
fi

echo ""
echo "Step 4: Verifikasi..."

# Test msedgedriver
if command_exists msedgedriver; then
    DRIVER_VERSION=$(msedgedriver --version)
    echo "✓ msedgedriver version: $DRIVER_VERSION"
else
    echo "✗ msedgedriver tidak ditemukan di PATH"
    echo "  Mungkin perlu restart terminal atau login ulang"
fi

# Verify .env content
echo ""
echo "Content of .env files:"
echo "Flask: $(grep EDGE_DRIVER_PATH $FLASK_ENV 2>/dev/null || echo 'Not set')"
echo "Scrapper: $(grep EDGE_DRIVER_PATH $SCRAPPER_ENV 2>/dev/null || echo 'Not set')"

echo ""
echo "=========================================="
echo "✓ Setup selesai!"
echo "=========================================="
echo ""
echo "Untuk test:"
echo "  cd backend/app-backend-flask"
echo "  source .venv/bin/activate"
echo "  python3 -c \"from utils.scrapper.edge_driver_helper import create_edge_driver; driver = create_edge_driver(); print('Success!'); driver.quit()\""
