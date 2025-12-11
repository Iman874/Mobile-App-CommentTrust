# Edge Driver Setup - Summary

## ✅ Status: SELESAI

Edge WebDriver sudah berhasil dikonfigurasi untuk Linux!

### Lokasi Edge Driver
```
/home/iman874/Downloads/edgedriver_linux64/msedgedriver
```

### .env Configuration
Kedua file sudah ter-update dengan path yang benar:

**Flask Backend** (`backend/app-backend-flask/.env`):
```
EDGE_DRIVER_PATH=/home/iman874/Downloads/edgedriver_linux64/msedgedriver
```

**Scrapper** (`backend/Scrapper/.env`):
```
EDGE_DRIVER_PATH=/home/iman874/Downloads/edgedriver_linux64/msedgedriver
```

### Verification ✓
- ✅ File exists
- ✅ File is executable (rwx permissions)
- ✅ Driver version: Microsoft Edge WebDriver 143.0.3650.66
- ✅ Path resolution working
- ✅ Driver validation passed

## Cara Menggunakan

### 1. Pastikan .env ter-load saat runtime
Kode sudah support dua cara loading:
```python
# Via python-dotenv (jika installed)
from dotenv import load_dotenv
load_dotenv()

# Atau via environment variable langsung
export EDGE_DRIVER_PATH="/home/iman874/Downloads/edgedriver_linux64/msedgedriver"
```

### 2. Test Driver
```bash
cd backend/app-backend-flask
export EDGE_DRIVER_PATH="/home/iman874/Downloads/edgedriver_linux64/msedgedriver"
python3 << 'EOF'
from utils.scrapper.edge_driver_helper import create_edge_driver
driver = create_edge_driver()
print("✅ Driver created successfully!")
driver.quit()
EOF
```

### 3. Jalankan Scrapper
```bash
cd backend/app-backend-flask
export EDGE_DRIVER_PATH="/home/iman874/Downloads/edgedriver_linux64/msedgedriver"
python main.py
```

## Jika Edge Driver Berubah Lokasi

Jalankan auto-setup script lagi:
```bash
cd /home/iman874/Documents/GitHub/Mobile-App-CommentTrust
python3 auto_setup_edge_driver.py
```

Script ini akan:
1. 🔍 Cari lokasi msedgedriver di sistem
2. ✅ Verifikasi bahwa driver executable
3. ⚙️ Update .env files secara otomatis

## Tools Setup Tersedia

### 1. Auto Setup (Python)
```bash
python3 auto_setup_edge_driver.py
```
Recommended - intelligent detection dan cross-platform support

### 2. Manual Setup (Bash)
```bash
bash setup_edge_driver_manual.sh
```
Untuk input path manual jika Edge di lokasi custom

### 3. Auto Setup (Bash)
```bash
bash setup_edge_driver.sh
```
Untuk distro Linux standard (Ubuntu/Debian/Fedora/Arch)

## Troubleshooting

### Error: "Edge WebDriver not found"
1. Pastikan environment variable set: `export EDGE_DRIVER_PATH=...`
2. Pastikan .env file ter-load
3. Jalankan auto-setup lagi: `python3 auto_setup_edge_driver.py`

### Error: "Permission denied"
```bash
chmod +x /home/iman874/Downloads/edgedriver_linux64/msedgedriver
```

### Error: "WebDriver crashed"
- Pastikan Microsoft Edge browser juga terinstall
- Check driver version kompatibel dengan browser version
- Update ke driver terbaru dari: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/

## Versi yang Terpasang
- Driver: 143.0.3650.66
- Path: `/home/iman874/Downloads/edgedriver_linux64/msedgedriver`
- Status: ✅ Fully functional
