#!/bin/bash

# Manual setup Edge Driver untuk Flatpak atau custom installation
# Gunakan ini jika Edge sudah terinstall tapi di lokasi non-standard

echo "=========================================="
echo "Edge Driver Setup - Manual Mode"
echo "=========================================="
echo ""

# Option 1: Input manual path
echo "Ada beberapa cara untuk setup Edge Driver:"
echo ""
echo "1. Jika Edge sudah terinstall:"
echo "   - Gunakan: /snap/bin/msedgedriver (jika via snap)"
echo "   - Atau: /opt/microsoft/msedge/msedgedriver"
echo "   - Atau cari dengan: find / -name msedgedriver -type f 2>/dev/null"
echo ""
echo "2. Jika hanya punya binary Edge (tanpa driver):"
echo "   - Download dari: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/"
echo "   - Extract dan set path ke msedgedriver"
echo ""
echo "3. Alternatif: Gunakan Chromium/Chrome WebDriver sebagai gantinya"
echo ""

read -p "Masukkan path lengkap ke msedgedriver (atau tekan Enter untuk skip): " DRIVER_PATH

if [ -n "$DRIVER_PATH" ]; then
    # Verify path exists
    if [ -f "$DRIVER_PATH" ]; then
        echo "✓ File ditemukan: $DRIVER_PATH"
        
        # Make executable
        chmod +x "$DRIVER_PATH"
        echo "✓ Made executable"
        
        # Update Flask .env
        FLASK_ENV="/home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/app-backend-flask/.env"
        sed -i '/^EDGE_DRIVER_PATH=/d' "$FLASK_ENV"
        echo "EDGE_DRIVER_PATH=$DRIVER_PATH" >> "$FLASK_ENV"
        echo "✓ Updated Flask .env"
        
        # Update Scrapper .env
        SCRAPPER_ENV="/home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/Scrapper/.env"
        sed -i '/^EDGE_DRIVER_PATH=/d' "$SCRAPPER_ENV"
        echo "EDGE_DRIVER_PATH=$DRIVER_PATH" >> "$SCRAPPER_ENV"
        echo "✓ Updated Scrapper .env"
        
        # Verify
        echo ""
        echo "Verifikasi driver version:"
        $DRIVER_PATH --version 2>/dev/null || echo "⚠ Tidak bisa get version"
        
        echo ""
        echo "✓ Setup selesai!"
    else
        echo "✗ File tidak ditemukan: $DRIVER_PATH"
        exit 1
    fi
else
    echo "Setup dibatalkan"
    exit 1
fi
