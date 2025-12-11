# Testing & Running Guide

## 🏃 Cara Menjalankan Sistem

### 1. Setup Environment

```bash
# Navigate to Flask backend
cd backend/app-backend-flask

# Create/activate virtual environment (if not already done)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install requirements
pip install -r requirements.txt
```

### 2. Run Flask Backend

```bash
# Make sure Edge is running with remote debugging (in separate terminal)
/usr/bin/microsoft-edge-stable --remote-debugging-port=9222

# In Flask terminal
source venv/bin/activate
python main.py

# Or using start script
./start.sh
```

Server akan berjalan di: `http://127.0.0.1:5001`

### 3. Open Progress Page

Buka browser ke: `http://127.0.0.1:5001/progress`

---

## 🧪 Testing Scenarios

### Test 1: View Product History (No Scrape)

**Prerequisite:** Sudah ada minimal 1 produk di `output/review/`

**Steps:**
```
1. Open progress page
2. Scroll ke bawah → lihat "Histori Produk"
3. Seharusnya muncul card-card produk
4. Verify:
   - Product name muncul ✓
   - Comment count correct ✓
   - Analysis status badge muncul ✓
   - Rating tertera ✓
```

**Expected Result:**
```
[Product Card]
Sepatu Olahraga Premium ✓ Analyzed
Toko Elektronik XYZ
Comments: 245  |  Rating: 4.5
[Re-Analyze] [View Details]
```

---

### Test 2: Check API Endpoints

**Using curl atau browser:**

```bash
# Get product history
curl http://127.0.0.1:5001/api/history/products

# Get product stats
curl http://127.0.0.1:5001/api/product/12345-67890/stats
```

**Expected Response:**
```json
{
  "products": [
    {
      "product_id": "12345-67890",
      "product_name": "Sepatu Olahraga",
      "shop_name": "Toko ABC",
      "review_count": 245,
      "analysis_done": true,
      "rating": 4.5
    }
  ]
}
```

---

### Test 3: View Product Details Popup

**Steps:**
```
1. Find product in history
2. Click "View Details" button
3. Popup muncul dengan:
   - Product name ✓
   - Review count ✓
   - Sentiment breakdown ✓
   - Top 5 tags dengan count ✓
```

**Expected Popup:**
```
Product: Sepatu Olahraga Premium
Product ID: 12345-67890
Total Reviews: 245
Rating: 4.5

Sentiment Distribution:
- Positive: 180
- Neutral: 45
- Negative: 20

Top Tags:
Kualitas Bagus: 120
Pengiriman Buruk: 15
Barang Tidak Sesuai: 8
Puas: 5
Respon Lambat: 3
```

---

### Test 4: Re-Analyze Existing Product

**Steps:**
```
1. Find product in history
2. Click "Re-Analyze" button
3. Button berubah → "Processing..."
4. Job muncul di job queue (di atas history)
5. Watch progress bar:
   - Analysis Progress naik (0% → 100%)
   - Step name berubah
6. Setelah done:
   - Job status → "done"
   - History di-refresh auto
   - Lihat file-file yang diupdate
```

**Files yang berubah:**
- ✓ `output/review/{product_id}/review.json` - tags ditambah
- ✓ `output/review/{product_id}/tag_statistics.json` - dibuat baru
- ✓ `output/review/{product_id}/indobert/review_tagged.csv` - dibuat baru

**Verify files:**
```bash
# Check if tags were added to review.json
cat output/review/12345-67890/review.json | head -20

# Check tag statistics
cat output/review/12345-67890/tag_statistics.json

# Check tagged CSV
head -5 output/review/12345-67890/indobert/review_tagged.csv
```

---

### Test 5: Test Comment Tagger Standalone

**In Python shell:**

```python
from utils.comment_tagger import tag_comments, get_tag_statistics

# Test data
test_reviews = [
    {'comment': 'Pengiriman lambat, barang rusak'},
    {'comment': 'Kualitas bagus, puas banget!'},
    {'comment': 'Tidak sesuai deskripsi, harga mahal'},
]

# Tag comments
tagged = tag_comments(test_reviews, source_field='comment')
print(tagged)

# Get statistics
stats = get_tag_statistics(tagged)
print(f"Tag statistics: {stats}")
```

**Expected Output:**
```python
[
  {
    'comment': 'Pengiriman lambat, barang rusak',
    'tags': ['Pengiriman Buruk', 'Barang Rusak']
  },
  {
    'comment': 'Kualitas bagus, puas banget!',
    'tags': ['Kualitas Bagus', 'Puas']
  },
  {
    'comment': 'Tidak sesuai deskripsi, harga mahal',
    'tags': ['Barang Tidak Sesuai', 'Harga Mahal']
  }
]

Tag statistics: {'Pengiriman Buruk': 1, 'Barang Rusak': 1, 'Kualitas Bagus': 1, 'Puas': 1, 'Barang Tidak Sesuai': 1, 'Harga Mahal': 1}
```

---

### Test 6: Add New Keyword & Re-analyze

**Steps:**

1. **Edit keyword mapping:**
```bash
nano backend/app-backend-flask/utils/comment_tagger.py
```

Find `KEYWORD_MAPPING` and add:
```python
'baik banget': 'Kualitas Bagus Sekali',
'tidak puas': 'Tidak Puas',
'rapi': 'Kemasan Rapi',
```

2. **Re-analyze product:**
```
- Find product in history
- Click "Re-Analyze"
- Wait for completion
```

3. **Verify new tags:**
```bash
# Check tag_statistics.json for new tags
cat output/review/12345-67890/tag_statistics.json
# Should include: "Kualitas Bagus Sekali", "Tidak Puas", etc
```

---

## 🔍 Debugging Tips

### Problem: History not showing

**Checklist:**
```
[ ] Check if output/review/ folder exists
    → ls output/review/
    
[ ] Check if there are product folders
    → ls output/review/12345-67890/
    
[ ] Check if review.json exists
    → ls output/review/12345-67890/review.json
    
[ ] Check API response
    → curl http://127.0.0.1:5001/api/history/products
    
[ ] Check browser console for JS errors
    → F12 → Console tab
```

### Problem: Re-analyze fails

**Check logs:**
```bash
# Check Flask output for errors
# Look at: /tmp/logs/process-*.log files

# Check if review.json is valid JSON
python3 -m json.tool output/review/12345-67890/review.json

# Try re-analyze in Python shell
from utils.comment_tagger import tag_comments
import json

with open('output/review/12345-67890/review.json') as f:
    reviews = json.load(f)

tagged = tag_comments(reviews)
print(f"Tagged {len(tagged)} reviews")
```

### Problem: Tags not extracted

**Debug keyword matching:**
```python
from utils.comment_tagger import _extract_keywords, _clean_text

text = "Pengiriman lambat, barang rusak"
cleaned = _clean_text(text)
keywords = _extract_keywords(text)

print(f"Original: {text}")
print(f"Cleaned: {cleaned}")
print(f"Keywords found: {keywords}")
```

---

## 📊 Verification Checklist

After implementation, verify:

- [ ] `utils/comment_tagger.py` exists and has functions:
  - tag_comments()
  - get_tag_statistics()
  - get_top_tags()

- [ ] API endpoints working:
  - GET `/api/history/products` → returns products array
  - GET `/api/product/{id}/stats` → returns stats with tag_stats
  - POST `/api/reanalyze/{id}` → returns job_id

- [ ] Frontend updated:
  - progress.html shows history section
  - Re-Analyze button works
  - View Details popup shows
  - Auto-refresh every 10s

- [ ] Data files created:
  - review.json with 'tags' field
  - tag_statistics.json (new)
  - review_tagged.csv (new)

---

## ⚡ Performance Benchmarks

Expected performance:

| Operation | Reviews | Time | Notes |
|-----------|---------|------|-------|
| Tag 100 comments | 100 | <1s | Fast |
| Tag 1000 comments | 1000 | 2-3s | Depends on comment length |
| Re-analyze small product | 50 | 2-5s | Includes file I/O |
| Re-analyze medium product | 500 | 5-10s | Normal case |
| Re-analyze large product | 2000+ | 20-30s | May take time |

---

## 🐛 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Tags empty | Keywords not in KEYWORD_MAPPING | Add to mapping, re-analyze |
| API returns 404 | Product folder doesn't exist | Check output/review/ folder |
| History page blank | No products yet | Scrape a product first |
| Re-analyze stuck | Long comments or many reviews | Wait or check logs |
| Tags lowercase | Normal | Keywords normalized to lowercase |

---

## 📝 Logs Location

```
backend/app-backend-flask/log/
├── incoming.log           # All requests
├── process-{pid}-*.log    # Job processing
└── input-{pid}-*.log      # Input handling
```

Check logs:
```bash
tail -f log/process-*.log       # Follow latest job log
grep "REANALYZE" log/*.log      # Find reanalyze logs
grep "ERROR" log/*.log          # Find errors
```

---

## ✅ Success Criteria

System is working correctly when:

✅ History page shows all scraped products
✅ Product cards display correct stats
✅ Re-Analyze button triggers analysis
✅ View Details popup shows tag statistics
✅ review.json contains tags field
✅ tag_statistics.json is created
✅ review_tagged.csv includes tags column
✅ Auto-refresh updates history every 10s
✅ New keywords added to KEYWORD_MAPPING are recognized
✅ No errors in browser console or Flask logs

---

## 🚀 Next Steps After Verification

1. **Customize Keywords**
   - Review KEYWORD_MAPPING in comment_tagger.py
   - Add domain-specific keywords

2. **Fine-tune Tags**
   - Run re-analysis on test products
   - Check if tag extraction is accurate

3. **Setup Automation**
   - Setup cron job for periodic re-analysis
   - Setup notification alerts

4. **Integrate with Frontend**
   - Use tag statistics in visualizations
   - Build tag filtering interface

5. **Monitor Performance**
   - Track analysis times
   - Optimize for large products

---

**Happy testing! 🎉**
