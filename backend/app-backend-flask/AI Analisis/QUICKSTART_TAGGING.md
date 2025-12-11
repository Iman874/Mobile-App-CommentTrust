# Quick Start: Product History & Comment Tagging

## 🚀 Cara Pakai

### 1. **Lihat Histori Produk (Home)**
Buka halaman `http://127.0.0.1:5001/progress`

Di bagian bawah, akan ada **"Histori Produk"** yang menampilkan:
- Nama produk + Status analisis (✓ atau ○)
- Nama toko
- Jumlah komentar & rating
- Tombol "Re-Analyze" & "View Details"

### 2. **Re-Analyze Produk Lama (tanpa scrape ulang)**
```
1. Cari produk di Histori
2. Klik tombol "Re-Analyze"
3. Tunggu job selesai (akan ada di job queue di atas)
4. Review otomatis di-tag ulang
5. CSV `review_tagged.csv` diupdate
```

### 3. **Lihat Statistik Produk**
```
1. Klik tombol "View Details" pada produk
2. Popup menampilkan:
   - Total komentar
   - Breakdown sentiment (positif/netral/negatif)
   - Top tags yang paling banyak dibicarakan
```

---

## 📊 Output Files

Setelah scrape & analyze selesai, file akan tersimpan di:

```
output/review/{product_id}/
├── review.json                    # Semua reviews + tags
├── product.json                   # Info produk
├── tag_statistics.json            # Statistik tags
└── indobert/
    ├── review_tagged.csv          # CSV dengan tags column
    ├── review_sentiment.csv       # Sentiment analysis
    ├── review_fake.csv            # Fake review detection
    └── review_trust.csv           # Trust score
```

---

## 🏷️ Daftar Tags yang Tersedia

### Pengiriman (Shipping Issues)
- `Pengiriman Buruk` - keyword: lambat, kurir, ongkir, hilang, rusak, packing
- `Barang Rusak` - keyword: rusak, packing

### Kualitas (Quality)
- `Kualitas Buruk` - keyword: jelek, buruk, kualitas
- `Kualitas Bagus` - keyword: bagus, sempurna

### Barang (Product)
- `Barang Tidak Sesuai` - keyword: tidak sesuai, beda, palsu, fake, replika, kw
- `Warna Tidak Sesuai` - keyword: warna, pudar
- `Masalah Ukuran` - keyword: ukuran, ketat, longgar, size
- `Barang Cacat` - keyword: cacat
- `Tidak Berfungsi` - keyword: tidak berfungsi, error
- `Produk Expired` - keyword: expired

### Harga (Price)
- `Harga Mahal` - keyword: mahal
- `Harga Murah` - keyword: murah
- `Promo/Diskon` - keyword: promo, diskon

### Penjual (Seller)
- `Respon Lambat` - keyword: tidak respon, respon
- `Layanan Customer Service` - keyword: customer service, cs
- `Komunikasi Buruk` - keyword: komunikasi
- `Masalah Penjual` - keyword: penjual

### Positif (Positive Feedback)
- `Direkomendasikan` - keyword: rekomendasi, rekomen
- `Akan Beli Lagi` - keyword: beli lagi, beli ulang
- `Puas` - keyword: puas, memuaskan
- `Senang` - keyword: senang, suka

---

## 💡 Contoh Tagging

### Input Comment:
```
"Pengiriman lambat, barang sampai rusak. Kualitas buruk, 
tidak sesuai deskripsi. Sangat kecewa dan tidak rekomen."
```

### Output Tags:
```json
{
  "comment": "Pengiriman lambat, barang sampai rusak...",
  "tags": [
    "Pengiriman Buruk",
    "Barang Rusak",
    "Kualitas Buruk",
    "Barang Tidak Sesuai"
  ]
}
```

---

## 🔧 Tambah Tag Baru

Edit file: `backend/app-backend-flask/utils/comment_tagger.py`

Cari section `KEYWORD_MAPPING` dan tambahkan:

```python
KEYWORD_MAPPING = {
    # ... existing entries ...
    
    # Tambahan baru
    'baik banget': 'Kualitas Bagus Sekali',
    'tidak puas': 'Tidak Puas',
    'kemasan rapi': 'Kemasan Rapi',
}
```

Setelah itu, cukup jalankan **Re-Analyze** untuk re-tag dengan keyword baru.

---

## 📈 API Reference

### Get All Products History
```
GET /api/history/products

Response:
{
  "products": [
    {
      "product_id": "12345-67890",
      "product_name": "...",
      "shop_name": "...",
      "price": 150000,
      "review_count": 245,
      "analysis_done": true,
      "rating": 4.5
    }
  ]
}
```

### Get Product Statistics
```
GET /api/product/{product_id}/stats

Response:
{
  "product_id": "12345-67890",
  "product_name": "...",
  "review_count": 245,
  "rating": 4.5,
  "sentiment_count": {
    "positive": 180,
    "neutral": 45,
    "negative": 20
  },
  "tag_stats": {
    "Pengiriman Buruk": 15,
    "Kualitas Bagus": 120,
    ...
  }
}
```

### Trigger Re-Analysis
```
POST /api/reanalyze/{product_id}

Response:
{
  "ok": true,
  "job_id": "a1b2c3d4"
}
```

---

## ⚙️ Configuration

### Change Remote Debugging Port (untuk Edge)
Edit `.env`:
```
EDGE_REMOTE_PORT=9222  # Default port untuk remote debugging
```

### Change Analysis Backend
Edit main flow di `service/api.py` (currently using 'indobert'):
```python
out_dir = pipeline.run_pipeline(
    source_dir=review_dir, 
    product_id=product_id, 
    backend='indobert',  # Change ini jika ada backend lain
    progress=_progress
)
```

---

## 🐛 Tips Troubleshooting

**Q: Re-analyze tapi tags tidak muncul?**
A: Cek apakah:
1. `review.json` ada di folder product
2. Keyword di `KEYWORD_MAPPING` lowercase
3. Text comment sudah di-normalize (punctuation removed)

**Q: History tidak muncul di UI?**
A: Pastikan:
1. Ada minimal 1 produk di `output/review/` folder
2. Setiap product punya `review.json`
3. Browser di-refresh (Ctrl+F5)

**Q: Tag statistics kosong?**
A: Jalankan Re-Analyze dari history page

---

## 📝 Notes

- Tagging dilakukan secara **offline** (tidak butuh internet)
- Performa: ~1000 comments/detik
- Support multi-word keywords (max 3 words)
- Case-insensitive & punctuation-tolerant
- Satu comment bisa punya multiple tags

---

## Next Steps

1. ✅ Scrape produk dari Shopee
2. ✅ Auto-analyze dengan sentiment & fake detection
3. ✅ Auto-tag comments dengan keyword matching
4. ⏳ View trends & statistics per tag
5. ⏳ Export reports dengan tag breakdown
6. ⏳ Build recommendation system based on tags
