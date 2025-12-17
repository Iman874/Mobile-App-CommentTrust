# Panduan Implementasi Sistem Tags

## 🚀 Quick Start

### 1. Jalankan Database Migrations
```bash
cd backend/app-backend-laravel
php artisan migrate
```

Migrations yang dijalankan:
- `2025_12_17_000001_create_tags_table.php` - Tabel tags
- `2025_12_17_000002_create_comment_tag_table.php` - Pivot table comment_tag

### 2. Seed Default Tags
```bash
php artisan db:seed --class=TagSeeder
```

Tags yang di-seed:
- **Kualitas**: Kualitas Baik, Kualitas Jelek, Produk Rusak, Sesuai Deskripsi
- **Pengiriman**: Pengiriman Cepat, Pengiriman Lambat, Packaging Baik, Packaging Jelek
- **Harga**: Harga Terjangkau, Harga Mahal, Harga Kompetitif
- **Layanan**: Layanan Baik, Layanan Jelek, Responsif
- **Rekomendasi**: Rekomendasi, Tidak Direkomendasikan
- **Autentisitas**: Produk Asli, Produk Palsu

**Total: 18 default tags**

### 3. Clear Cache (Jika Perlu)
```bash
php artisan cache:clear
php artisan config:cache
```

---

## 📝 Auto-Tagging Comments

### Menggunakan Console Command

**Tag semua comments di semua products:**
```bash
php artisan comments:tag
```

**Tag specific product:**
```bash
php artisan comments:tag 129681898-2110555906
```

**Force re-tag (replace existing tags):**
```bash
php artisan comments:tag --force
php artisan comments:tag 129681898-2110555906 --force
```

### Tagging Logic
Tags dibuat berdasarkan:
1. **Sentiment**: positive → "Kualitas Baik", negative → "Kualitas Jelek"
2. **Trust Score**: ≥80 → "Terpercaya", ≤30 → "Mencurigakan"
3. **Rating**: ≥4 → "Rating Tinggi", ≤2 → "Rating Rendah"
4. **Fake Prediction**: true → "Mencurigakan"
5. **Text Length**: ≥200 → "Ulasan Detail", ≤30 → "Ulasan Singkat"
6. **Duplicate Score**: ≥0.7 → "Mencurigakan"
7. **Likes/Engagement**: ≥100 → "Ulasan Populer"

---

## 🔌 API Endpoints

### Dapatkan Tags untuk Product
```
GET /api/products/{productId}/tags
Authorization: Bearer <token>
```

Response:
```json
{
  "ok": true,
  "tags": [
    {
      "id": 1,
      "name": "Kualitas Baik",
      "comments_count": 45
    },
    {
      "id": 2,
      "name": "Pengiriman Cepat",
      "comments_count": 32
    }
  ],
  "total": 2
}
```

### Dapatkan Semua Tags
```
GET /api/tags?category=kualitas&active=true&per_page=50
Authorization: Bearer <token>
```

### Dapatkan Comments dengan Tag Tertentu
```
GET /api/tags/{tagSlug}/comments?page=1&per_page=15
Authorization: Bearer <token>

Example: /api/tags/kualitas-baik/comments
```

### Tag Statistics
```
GET /api/tags/stats/summary
Authorization: Bearer <token>
```

Response:
```json
{
  "ok": true,
  "stats": {
    "total_tags": 18,
    "active_tags": 18,
    "total_tagged_comments": 2345,
    "top_tags": [
      { "id": 1, "name": "Kualitas Baik", "count": 450 }
    ],
    "tags_by_category": [
      { "category": "kualitas", "count": 4 }
    ]
  }
}
```

---

## 🔍 Debugging & Logs

### Monitor Tagging Logs
```bash
tail -f storage/logs/laravel.log | grep -i "tag\|comment"
```

### Expected Log Output (Saat Tag Attachment)

```
[timestamp] local.INFO: _insertCommentsWithTags START
  {
    "buffer_count": 1000,
    "tags_queue_count": 450,
    "product_key": "129681898-2110555906"
  }

[timestamp] local.DEBUG: Tags attached to comment
  {
    "comment_id": 12345,
    "tags": ["Kualitas Baik", "Pengiriman Cepat"],
    "tag_count": 2
  }

[timestamp] local.INFO: _insertCommentsWithTags tag attachment completed
  {
    "tags_attached_total": 1250,
    "errors": 0,
    "queue_items_processed": 450
  }
```

### Check Comment Tags via Tinker
```bash
php artisan tinker
```

```php
# Get tags for specific comment
$comment = Comment::find(12345);
$comment->commentTags()->get();

# Get comments with specific tag
$tag = Tag::where('slug', 'kualitas-baik')->first();
$tag->comments()->get();

# Check if tags exists
$comment->commentTags()->count();
```

---

## 🗄️ Database Queries

### View Comment-Tag Relationships
```sql
-- Jumlah tags per comment
SELECT c.id, c.username, COUNT(t.id) as tag_count
FROM comments c
LEFT JOIN comment_tag ct ON c.id = ct.comment_id
LEFT JOIN tags t ON ct.tag_id = t.id
GROUP BY c.id;

-- Top tags
SELECT t.name, COUNT(ct.id) as count
FROM tags t
LEFT JOIN comment_tag ct ON t.id = ct.tag_id
GROUP BY t.id
ORDER BY count DESC;

-- Comments with multiple tags
SELECT c.id, c.comment, GROUP_CONCAT(t.name SEPARATOR ', ') as tags
FROM comments c
LEFT JOIN comment_tag ct ON c.id = ct.comment_id
LEFT JOIN tags t ON ct.tag_id = t.id
GROUP BY c.id
HAVING COUNT(t.id) > 0;
```

---

## 🛠️ Maintenance

### Add New Tag
```bash
php artisan tinker
```

```php
Tag::findOrCreateByName('Tag Baru', 'kategori');
```

Atau via API:
```bash
curl -X POST http://localhost:8000/api/tags \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tag Baru",
    "category": "kategori",
    "color": "#FF5733"
  }'
```

### Update Tag Count Cache
```bash
php artisan tinker
```

```php
// Update all tag counts
use App\Models\Tag;
Tag::all()->each(function($tag) {
  $tag->update(['count' => $tag->comments()->count()]);
});
```

### Clean Orphaned Tags (Tags tanpa comments)
```bash
php artisan tinker
```

```php
use App\Models\Tag;
Tag::doesntHave('comments')->delete();
```

---

## ⚠️ Known Issues & Workarounds

### Issue: Tidak ada tags di-attach ke comments
**Penyebab**: Flask tidak mengirimkan field `tags` dalam data analysis

**Solusi**: Gunakan console command untuk auto-tagging
```bash
php artisan comments:tag
```

### Issue: Tags query lambat
**Solusi**: 
- Pastikan indexes ada (migrations sudah membuat index)
- Gunakan `->active()` scope
- Gunakan `->withCount()` untuk menghindari N+1 queries

### Issue: Duplicate tags di-attach
**Solusi**: `syncTagsByName()` dan `attachTagsByName()` sudah handle deduplication

---

## 📚 File References

| File | Deskripsi |
|------|-----------|
| `app/Models/Tag.php` | Model untuk tags |
| `app/Models/Comment.php` | Model untuk comments (updated dengan tag relations) |
| `app/Http/Controllers/TagController.php` | API endpoints untuk tags |
| `database/migrations/2025_12_17_000001_create_tags_table.php` | Migration tabel tags |
| `database/migrations/2025_12_17_000002_create_comment_tag_table.php` | Migration pivot table |
| `database/seeders/TagSeeder.php` | Seeder default tags |
| `app/Console/Commands/TagComments.php` | Console command untuk auto-tagging |
| `TAG_SYSTEM_DOCUMENTATION.md` | Dokumentasi lengkap |
| `TAG_SYSTEM_IMPLEMENTATION_STATUS.md` | Status implementasi & next steps |

---

## 🚀 Next Steps - Flask Integration

Saat ini, tags hanya bisa ditambahkan melalui:
1. Console command `php artisan comments:tag`
2. Manual via API
3. Bulk operations

### TODO: Integrate Flask
Untuk membuat tags otomatis dari Flask:

1. Update `backend/app-backend-flask/service/api.py`
   - Generate tags dari sentiment/trust/rating
   - Include tags dalam response JSON

2. Test end-to-end
3. Monitor dengan logs

**Reference**: `TAG_SYSTEM_IMPLEMENTATION_STATUS.md`

---

## 📞 Support

Jika ada masalah:
1. Check logs: `storage/logs/laravel.log`
2. Run: `php artisan comments:tag --verbose`
3. Verify database: `php artisan tinker`
4. Check migrations: `php artisan migrate:status`

---

**Last Updated**: December 17, 2025
