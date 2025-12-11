# Implementasi Fitur: Product History & Comment Tagging

## Ringkasan Perubahan

### 1. **Comment Tagger Module** (`utils/comment_tagger.py`)
Modul baru yang mengekstrak tag/label dari komentar berdasarkan keyword extraction.

**Fitur:**
- Extract keywords dari komentar (preprocessing text, case-insensitive, remove punctuation)
- Map keyword ke tag predefined (e.g., "pengiriman lambat" → "Pengiriman Buruk")
- Support multi-word keywords dan single words
- Hitung statistik tag di seluruh reviews

**Tag Categories yang Tersedia:**
```
📦 Pengiriman (Shipping):
   - Pengiriman Buruk
   - Barang Rusak

⭐ Kualitas (Quality):
   - Kualitas Buruk
   - Kualitas Bagus

🎁 Barang (Product):
   - Barang Tidak Sesuai
   - Warna Tidak Sesuai
   - Masalah Ukuran
   - Barang Cacat
   - Tidak Berfungsi
   - Produk Expired

💰 Harga (Price):
   - Harga Mahal
   - Harga Murah
   - Promo/Diskon

👨‍💼 Penjual (Seller):
   - Masalah Penjual
   - Respon Lambat
   - Layanan Customer Service
   - Komunikasi Buruk

👍 Positif (Positive):
   - Direkomendasikan
   - Akan Beli Lagi
   - Puas
   - Senang
```

**Penggunaan:**
```python
from utils.comment_tagger import tag_comments, get_tag_statistics

reviews = [...]  # list of review dicts with 'comment' field

# Add tags to reviews
tagged_reviews = tag_comments(reviews, source_field='comment')

# Get statistics
stats = get_tag_statistics(tagged_reviews)
# Output: {'Pengiriman Buruk': 5, 'Kualitas Bagus': 3, ...}

# Get top N tags
top_tags = get_tag_statistics(reviews, top_n=10)
```

---

### 2. **API Endpoints** (di `service/api.py`)

#### A. `/api/history/products` (GET)
Menampilkan daftar semua produk yang sudah di-scrape dengan statistik.

**Response:**
```json
{
  "products": [
    {
      "product_id": "12345-67890",
      "product_name": "Sepatu Olahraga Premium",
      "shop_name": "Toko Elektronik XYZ",
      "price": 150000,
      "review_count": 245,
      "analysis_done": true,
      "rating": 4.5
    },
    ...
  ]
}
```

#### B. `/api/product/<product_id>/stats` (GET)
Dapatkan statistik detail untuk satu produk (sentiment, tags, etc).

**Response:**
```json
{
  "product_id": "12345-67890",
  "product_name": "Sepatu Olahraga Premium",
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
    "Barang Tidak Sesuai": 8,
    ...
  }
}
```

#### C. `/api/reanalyze/<product_id>` (POST)
Re-run analisis pada produk yang sudah ada tanpa perlu scrape ulang.

**Proses:**
1. Load reviews dari `output/review/{product_id}/review.json`
2. Extract tags dari setiap comment
3. Save updated reviews dengan tag field
4. Generate `review_tagged.csv` di analysis folder
5. Save tag statistics ke `tag_statistics.json`

**Response:**
```json
{
  "ok": true,
  "job_id": "a1b2c3d4"
}
```

**Job Status:**
```json
{
  "id": "a1b2c3d4",
  "product_id": "12345-67890",
  "phase": "analysis",
  "analysis_progress": 40,
  "analysis_step_name": "[Processing] Updating analysis outputs..."
}
```

---

### 3. **Progress Page UI** (`static/progress.html`)

#### Fitur Baru:
1. **Histori Produk Section** (bagian bawah halaman)
   - Menampilkan semua produk yang pernah di-scrape
   - Show jumlah comments per produk
   - Show rating produk
   - Show analysis status (✓ Analyzed / ○ Pending)

2. **Product Cards** dengan aksi:
   - **Re-Analyze Button**: Trigger re-analysis untuk re-tag comments
   - **View Details Button**: Popup dengan statistik lengkap (sentiment, top tags)

3. **Auto-refresh**: 
   - History di-refresh setiap 10 detik
   - Di-refresh juga saat job selesai

**Tampilan:**
```
[Product Card]
┌─────────────────────────────────────────────────┐
│ Sepatu Olahraga Premium ✓ Analyzed              │
│ Toko Elektronik XYZ                             │
│ Comments: 245  |  Rating: 4.5                   │
│ [Re-Analyze] [View Details]                     │
└─────────────────────────────────────────────────┘
```

---

### 4. **Data Storage Structure**

```
output/
├── review/
│   └── {product_id}/
│       ├── review.json                 # Reviews dengan tags
│       ├── product.json                # Product info
│       ├── tag_statistics.json         # Tag statistics (dari re-analyze)
│       └── (analysis outputs)
├── review.json                         # Aggregate semua reviews
└── product.json                        # Aggregate product info
```

---

## Workflow Penggunaan

### Scenario 1: Scrape & Analyze Produk Baru
```
1. Masukkan link Shopee → Submit
2. Tunggu Scraper selesai
3. Analysis berjalan otomatis (termasuk tagging)
4. Review dengan tags otomatis tersimpan
5. Produk muncul di Histori dengan badge "✓ Analyzed"
```

### Scenario 2: Re-Analyze Produk Lama
```
1. Lihat Histori Produk
2. Klik tombol "Re-Analyze" pada produk
3. Job berjalan (20% → 40% → 80% → 100%)
4. Review di-re-tag dengan keyword mapping terbaru
5. CSV `review_tagged.csv` diupdate
6. Tag statistics tersimpan
```

### Scenario 3: View Product Statistics
```
1. Lihat Histori Produk
2. Klik "View Details" pada produk
3. Popup menampilkan:
   - Total reviews
   - Sentiment breakdown (positive/neutral/negative)
   - Top 5 tags dengan count
```

---

## Keyword Mapping yang Tersedia

Untuk menambah keyword baru, edit `KEYWORD_MAPPING` di `utils/comment_tagger.py`:

```python
KEYWORD_MAPPING = {
    'keyword_baru': 'Nama Tag',
    'pengiriman lambat': 'Pengiriman Buruk',
    'barang rusak': 'Barang Rusak',
    # ... dst
}
```

### Tips:
- Gunakan huruf kecil (case akan di-normalize otomatis)
- Support multi-word keywords: `'tidak sesuai': 'Barang Tidak Sesuai'`
- Satu keyword → satu tag (no multi-tag per keyword)
- Satu komentar bisa punya multiple tags

---

## Technical Details

### Comment Tagging Algorithm
```
1. Normalize text: lowercase, remove punctuation, split to words
2. Check multi-word phrases (2-3 words) against KEYWORD_MAPPING
3. Check single words against KEYWORD_MAPPING
4. Return unique tags
5. Count all tags across reviews for statistics
```

### Performance
- Fast: Simple string matching, no ML models
- Scalable: Can handle thousands of reviews
- Extensible: Easy to add new keywords/tags

### Data Consistency
- Original `review.json` updated with tags (append field)
- New `review_tagged.csv` created for easier viewing
- `tag_statistics.json` auto-generated for frontend

---

## Troubleshooting

### Q: Re-analyze tidak update tags?
A: Pastikan `review.json` ada di folder product. Cek di:
```
output/review/{product_id}/review.json
```

### Q: Keyword baru tidak ter-extract?
A: Pastikan:
1. Keyword sudah ditambah ke `KEYWORD_MAPPING`
2. Case-nya lowercase
3. Text di-normalize (punctuation dihapus)

### Q: History tidak muncul?
A: Cek:
1. Ada file di `output/review/` ?
2. Ada `review.json` di setiap product folder?
3. API `/api/history/products` return data?

---

## Future Enhancements
- [ ] Custom tag creation dari UI
- [ ] Tag filtering & search
- [ ] Tag export to CSV
- [ ] Sentiment + Tag combination analysis
- [ ] Fake review detection dengan tags
- [ ] Tag-based recommendation system
