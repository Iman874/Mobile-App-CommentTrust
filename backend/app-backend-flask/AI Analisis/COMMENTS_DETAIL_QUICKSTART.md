# 🚀 Comment Detail Feature - Quick Start

Panduan cepat untuk menggunakan halaman detail komentar dengan filter advanced.

## 📌 Quick Access

**Dari Progress Page:**
```
1. Buka → http://127.0.0.1:5001/progress
2. Scroll ke "Histori Produk"
3. Cari produk yang sudah di-scrape
4. Klik button "💬 View Comments"
```

**Direct URL:**
```
http://127.0.0.1:5001/static/comments-detail.html?product=30169103-19027487468
```
Ganti `30169103-19027487468` dengan product ID yang diinginkan.

---

## 🎯 Common Tasks

### Task 1: Lihat Semua Komentar
1. Buka halaman Comments Detail
2. Sidebar sudah dengan default semua filter active
3. Scroll untuk melihat semua komentar
4. Use pagination untuk navigasi halaman

### Task 2: Filter by Tag (Cari Komplain Pengiriman)
1. Di sidebar kiri, cari section "Tag"
2. Lihat list semua tag dengan jumlah kemunculan
3. **Centang** "Pengiriman Buruk"
4. Lihat hanya komentar dengan tag ini

**Result:** Halaman otomatis filter dan tampilkan hanya komentar berkaitan pengiriman buruk.

### Task 3: Multiple Tag Filter (Logical AND)
Mencari komentar yang komplain tentang **pengiriman AND kualitas**:

1. Centang "Pengiriman Buruk"
2. Centang "Kualitas Buruk"
3. Halaman tampilkan **hanya** komentar dengan **KEDUA** tag
4. Ini untuk mencari komplain multi-aspek

### Task 4: Filter by Sentimen
Lihat hanya komentar positif (happy customers):

1. Di sidebar, section "Sentimen"
2. **Uncheck** "Netral" dan "Negatif"
3. Hanya "Positif" yang checked
4. Lihat komentar happy customers aja

### Task 5: Search Username
Cari semua komentar dari user tertentu:

1. Di Search Box paling atas sidebar
2. Ketik username: `budi123`
3. Halaman filter real-time dan tampilkan komentar dari user ini
4. Bisa combine dengan tag/sentiment filter

### Task 6: Bulk Select Semua Tag
Untuk statistik lengkap atau reset filter:

1. Di Tag section, klik **"Pilih Semua"**
2. Semua tag ter-check ✓
3. Lihat semua komentar with all tag combinations
4. Klik **"Hapus Semua"** untuk uncheck semua sekaligus

### Task 7: Quick Filter dari Tag Badge
Di komentar card, ada tag badges (blue pills):

1. Lihat komentar dengan multiple tags
2. **Klik salah satu tag badge** (misal: "pengiriman buruk")
3. Filter otomatis toggle untuk tag itu
4. View update instant

---

## 📊 Understanding the UI

### Header Section
```
Komentar - 30169103-19027487468          [← Kembali]
(Product ID yang sedang dilihat)         (Back button)
```

### Sidebar (Left Column - 300px)
```
┌─────────────────────┐
│    SEARCH BOX       │  ← Type untuk cari username/comment
├─────────────────────┤
│  TAG (Pilih/Hapus)  │  ← Multi-select tag filter
│  ☑ pengiriman (...) │     Angka = jumlah komentar
│  ☑ kualitas (...)   │
│  ☐ harga (...)      │
├─────────────────────┤
│  SENTIMEN           │  ← Single/multi sentiment
│  ☑ ● Positif (120)  │
│  ☑ ● Netral (45)    │
│  ☑ ● Negatif (85)   │
└─────────────────────┘
```

### Main Content (Right Column)
```
┌─────────────────────────────────────┐
│ Menampilkan 45 dari 250 komentar    │  ← Result counter
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ @budi123                    ●   │ │
│ │ 10 Dec 2024              Positif │ │
│ │                                  │ │
│ │ "Barang bagus, seller ramah"    │ │
│ │                                  │ │
│ │ [pengiriman cepat] [puas]        │ │  ← Tags
│ │ 📊 Trust: 95% 🔍 Fake: No       │ │
│ └─────────────────────────────────┘ │
│                                      │
│ [More comments...] (9 total/page)   │
│                                      │
│ [← Prev] [1] [2] [3] [Next →]       │  ← Pagination
└─────────────────────────────────────┘
```

### Color Coding

| Element | Color | Meaning |
|---------|-------|---------|
| Positive sentiment | 🟢 Green | Happy customer |
| Neutral sentiment | 🟠 Orange | Mixed opinion |
| Negative sentiment | 🔴 Red | Unhappy customer |
| Tag badges | 🔵 Blue | Topic/aspect |
| Card border | 🔵 Blue left | Selected/active |
| Hover | ↑ Lighter | Interactive element |

---

## 💡 Pro Tips

### Tip 1: Bulk Analysis
```
1. Click "Pilih Semua" untuk include all tags
2. Uncheck specific tag untuk exclude
3. Lihat impact dari exclude tag tertentu
```

### Tip 2: Combine Filters
```
1. Search: "lambat" (cari kata lambat)
2. Tag: "pengiriman buruk" (filter)
3. Sentiment: Uncheck positif
4. Result: Komentar negative tentang pengiriman lambat
```

### Tip 3: Find Fake Reviews
```
1. Filter tag: "promo/diskon" 
2. Sentiment: Positif ONLY
3. Check is_fake field
4. Identifies suspicious overly-positive discount comments
```

### Tip 4: Pagination Smart Navigation
```
- Click page number untuk jump langsung
- "..." muncul untuk hide middle pages
- Prev/Next button auto-disable di edge pages
- Auto-scroll to top saat ganti page
```

### Tip 5: Real-time Search
```
- Type di search box: instant filter
- No need tombol "Search" atau reload
- Works with tag/sentiment filter simultaneously
```

---

## 🔧 Data Fields Reference

Setiap komentar card menampilkan:

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| username | string | budi123 | User yang komentari |
| comment | string | "Barang bagus..." | Isi komentar |
| sentiment | enum | positive/neutral/negative | AI sentiment analysis |
| tags | array | ["pengiriman cepat", "puas"] | Auto-extracted topics |
| timestamp | ISO 8601 | 2024-12-10T10:30:00 | Waktu komentar |
| trust_score | 0-1 | 0.85 | Kredibilitas komentar (0-100%) |
| is_fake | boolean | false | Suspected fake review? |

---

## 🐛 Common Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Tags tidak tampil | Empty tag list | Run Re-Analyze di Progress page |
| No results | Blank page | Adjust filters, try "Hapus Semua" |
| Slow loading | Takes >5 sec | Product too large, use search/filter |
| Pagination broken | Button tidak function | Refresh page (Ctrl+F5) |
| Warna salah | Sentiment badge hijau tapi... | Clear cache, hard refresh |
| Back button error | Can't go back | Use browser back button instead |

---

## 📱 Mobile/Tablet View

Halaman ini responsive:

**Desktop (> 1024px):**
- 2-column: Sidebar (kiri) + Main (kanan)
- Sidebar sticky saat scroll
- Optimal untuk filtering

**Tablet/Mobile (≤ 1024px):**
- Full-width stacked layout
- Sidebar di atas, main content di bawah
- Scroll untuk lihat semua
- Still fully functional

---

## 🔗 Related Pages

- **Progress Page** → `/progress` - Main dashboard
- **Visualisasi** → `/static/visualisasi.html` - Data visualization
- **Home** → `/` - Landing page

---

## 📞 API Endpoints Used

Frontend menggunakan endpoint ini:

### Fetch Comments Data
```
GET /api/comments/{product_id}
```
Returns: comments array + tag statistics

**Example:**
```bash
curl http://127.0.0.1:5001/api/comments/30169103-19027487468
```

---

## ⚡ Performance Notes

- **First load:** ~1-2 seconds (API call + render)
- **Filter apply:** < 100ms (local JS, no API call)
- **Pagination:** Instant (no reload)
- **Search:** Real-time as you type

Untuk produk dengan 5000+ comments, initial load bisa lebih lama tapi filtering tetap fast.

---

## 🎓 Learning Path

1. **Dasar:** Buka halaman, explore default view
2. **Filter:** Coba individual tag/sentiment filter
3. **Combine:** Combine multiple filters
4. **Search:** Gunakan search box
5. **Advanced:** Mix search + filter + pagination

---

**Happy Analyzing! 🎉**

Last Updated: December 11, 2024
