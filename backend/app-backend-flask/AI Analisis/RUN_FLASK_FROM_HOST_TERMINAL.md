# Running Flask Backend - Edge Browser Issue di VS Code Flatpak

## Masalah

Ketika menjalankan Flask dari **VS Code Terminal (Flatpak)**, Edge WebDriver gagal spawn browser dengan error:
```
session not created from disconnected: unable to connect to renderer
```

## Penyebab

VS Code Flatpak berjalan di sandbox container yang isolated dari host system. Selenium WebDriver tidak bisa spawn browser native (Edge di `/usr/bin/microsoft-edge-stable`) dari dalam container.

## ✅ Solusi: Jalankan Flask di Terminal Host

### Langkah-Langkah:

1. **Buka Terminal Biasa** (BUKAN terminal VS Code)
   - Tekan `Ctrl+Alt+T` di Ubuntu
   - Atau buka aplikasi Terminal dari menu

2. **Navigate ke direktori backend:**
   ```bash
   cd /home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/app-backend-flask
   ```

3. **Aktifkan virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Jalankan Flask:**
   ```bash
   python main.py
   ```

5. **Test scraping:**
   ```bash
   # Di terminal lain atau di browser
   curl -X POST http://127.0.0.1:5001/api/force/scrape \
     -H "Content-Type: application/json" \
     -d '{"link":"https://shopee.co.id/PRODUCT_LINK_HERE"}'
   ```

### Hasil Yang Diharapkan:

✅ Flask server berjalan di `http://127.0.0.1:5001`  
✅ **Edge browser window muncul** di desktop (karena `EDGE_HEADLESS=0`)  
✅ User bisa melihat scraping process  
✅ User bisa solve captcha/login manual jika diperlukan  

## Konfigurasi

File `.env` sudah dikonfigurasi dengan benar:
```env
EDGE_DRIVER_PATH=/home/iman874/Downloads/edgedriver_linux64/msedgedriver
EDGE_BINARY_PATH=/usr/bin/microsoft-edge-stable
EDGE_HEADLESS=0  # Tidak headless - browser akan terlihat
```

## Akses Progress Page

Buka di browser:
- Progress: `http://127.0.0.1:5001/progress?job=JOB_ID`
- Visualisasi: `http://127.0.0.1:5001/visualisasi.html`

## Troubleshooting

### Edge window tidak muncul?
- Pastikan `EDGE_HEADLESS=0` di `.env`
- Restart Flask setelah mengubah `.env`

### Masih error "unable to connect to renderer"?
- **PASTI karena dijalankan dari VS Code Flatpak terminal**
- Solusi: Jalankan dari terminal host (lihat langkah di atas)

### Permission denied untuk Edge driver?
```bash
chmod +x /home/iman874/Downloads/edgedriver_linux64/msedgedriver
```
