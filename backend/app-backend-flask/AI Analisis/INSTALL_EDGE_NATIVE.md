# Install Microsoft Edge (Native) untuk Ubuntu

## Masalah
Flatpak Edge tidak bisa di-spawn dari Selenium WebDriver karena sandboxing issues.

## Solusi: Install Edge Native

Jalankan command berikut di **terminal host** (bukan VS Code terminal):

```bash
# 1. Download dan install Microsoft GPG key
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo install -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/
rm microsoft.gpg

# 2. Tambahkan repository Edge
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" | sudo tee /etc/apt/sources.list.d/microsoft-edge.list

# 3. Update dan install Edge
sudo apt update
sudo apt install microsoft-edge-stable -y

# 4. Verify instalasi
which microsoft-edge-stable
microsoft-edge-stable --version
```

## Update Konfigurasi

Setelah install, update `.env`:

```bash
cd /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/app-backend-flask

# Edit .env file
nano .env
```

Ubah `EDGE_BINARY_PATH` menjadi:
```
EDGE_BINARY_PATH=/usr/bin/microsoft-edge-stable
EDGE_HEADLESS=1
```

## Test

```bash
cd /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/app-backend-flask
source venv/bin/activate
python main.py
```

Lalu test scraping dari browser atau curl.

## Alternative: Gunakan Chrome/Chromium

Jika Edge sulit diinstall, bisa gunakan Chrome/Chromium:

```bash
sudo apt install chromium-browser -y
# atau
sudo apt install google-chrome-stable -y
```

Lalu update code untuk gunakan ChromeDriver instead of EdgeDriver.
