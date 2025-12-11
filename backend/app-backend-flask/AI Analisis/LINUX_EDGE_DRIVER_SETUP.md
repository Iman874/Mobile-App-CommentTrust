# Edge WebDriver Setup untuk Linux

## Masalah
Error: `Edge WebDriver not found at /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/browser-dummy/edgedriver_linux64/msedgedriver`

## Solusi

Ada 3 cara untuk mengatasi masalah ini:

### Opsi 1: Menggunakan System Package Manager (Recommended)

Instalasi msedgedriver melalui package manager sistem Anda:

#### Ubuntu/Debian
```bash
# Tambahkan Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo install -o root -g root -m 644 microsoft.gpg /etc/apt/trusted.gpg.d/
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" > /etc/apt/sources.list.d/microsoft-edge-dev.list'

# Update dan install
sudo apt update
sudo apt install microsoft-edge-stable

# Verify instalasi
which msedgedriver
# Output: /usr/bin/msedgedriver
```

#### Fedora/RHEL
```bash
sudo dnf install microsoft-edge-stable
```

#### Arch Linux
```bash
sudo pacman -S microsoft-edge-stable
```

**Kemudian, set environment variable di `.env`:**
```
EDGE_DRIVER_PATH=/usr/bin/msedgedriver
```

### Opsi 2: Download dari Microsoft Edge WebDriver Repository

1. Kunjungi: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
2. Download binary Linux untuk versi Edge Anda
3. Extract ke direktori pilihan, contoh: `/opt/msedgedriver/`
4. Buat executable:
```bash
chmod +x /opt/msedgedriver/msedgedriver
```

**Kemudian, set di `.env`:**
```
EDGE_DRIVER_PATH=/opt/msedgedriver/msedgedriver
```

### Opsi 3: Gunakan Default Path yang Sudah Ada

Jika sudah ada file `edgedriver_linux64/msedgedriver` di direktori project:

```bash
# Pastikan file executable
chmod +x /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/browser-dummy/edgedriver_linux64/msedgedriver

# Verifikasi path
ls -la /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/browser-dummy/edgedriver_linux64/msedgedriver
```

Jika file ada tapi tidak executable, jalankan:
```bash
chmod +x /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/browser-dummy/edgedriver_linux64/msedgedriver
```

## Bagaimana Sistem Membaca Konfigurasi

File `backend/app-backend-flask/utils/scrapper/edge_driver_helper.py` mencari driver dengan urutan prioritas:

1. **Environment Variable `EDGE_DRIVER_PATH`** (jika set di `.env` atau sistem)
2. **Default Path untuk Linux**: 
   ```
   {PROJECT_ROOT}/backend/browser-dummy/edgedriver_linux64/msedgedriver
   ```
3. **Default Path untuk Windows**: 
   ```
   {PROJECT_ROOT}/backend/browser-dummy/edgedriver_win64/msedgedriver.exe
   ```

## Cara Menggunakan .env File

File `.env` sudah disediakan di:
- `backend/app-backend-flask/.env`
- `backend/Scrapper/.env`

Uncomment dan sesuaikan path sesuai dengan instalasi Anda:

```bash
# Buka file
nano backend/app-backend-flask/.env

# Uncomment salah satu baris (hapus # di awal):
# EDGE_DRIVER_PATH=/usr/bin/msedgedriver
```

Jauh yang akan dibaca oleh sistem:
```python
import os
from dotenv import load_dotenv

load_dotenv()
driver_path = os.environ.get("EDGE_DRIVER_PATH")
```

## Verifikasi Instalasi

Setelah setup, jalankan test:

```bash
cd backend/app-backend-flask
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Jalankan test driver
python3 -c "from utils.scrapper.edge_driver_helper import create_edge_driver; driver = create_edge_driver(debug=True); print('Success!'); driver.quit()"
```

## Troubleshooting

### Error: "Not Executable"
```bash
chmod +x /path/to/msedgedriver
```

### Error: "File Not Found"
1. Verifikasi path dengan: `ls -la /path/to/msedgedriver`
2. Pastikan path di `.env` menggunakan absolute path, bukan relative path
3. Jalankan: `which msedgedriver` untuk cari lokasi default

### Error: "Permission Denied"
```bash
chmod +x /path/to/msedgedriver
```

## Quick Start untuk Ubuntu/Debian

```bash
# 1. Install Edge dan driver
sudo apt update
sudo apt install microsoft-edge-stable

# 2. Set environment variable di .env
echo 'EDGE_DRIVER_PATH=/usr/bin/msedgedriver' >> backend/app-backend-flask/.env
echo 'EDGE_DRIVER_PATH=/usr/bin/msedgedriver' >> backend/Scrapper/.env

# 3. Test
cd backend/app-backend-flask
source .venv/bin/activate
python3 -c "from utils.scrapper.edge_driver_helper import create_edge_driver; driver = create_edge_driver(); driver.quit()"
```
