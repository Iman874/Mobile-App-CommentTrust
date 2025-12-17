# Dokumentasi Sistem Tag Komentar

## Overview
Sistem tagging untuk komentar produk yang memungkinkan kategorisasi otomatis dan manual terhadap setiap komentar. Sistem ini mendukung relasi many-to-many antara Comments dan Tags.

## Database Schema

### Table: `tags`
Menyimpan definisi tag yang tersedia.

```sql
- id (PK)
- name (string, unique)      -- Nama tag (e.g., "Kualitas Baik", "Pengiriman Cepat")
- slug (string, unique)      -- URL-friendly identifier (auto-generated)
- description (text)         -- Deskripsi tag
- category (string)          -- Kategori tag (e.g., "kualitas", "layanan", "harga", "pengiriman")
- color (string)             -- Hex color code untuk UI (#FF5733)
- count (integer)            -- Cache jumlah komentar dengan tag ini
- is_active (boolean)        -- Flag untuk enable/disable tag
- timestamps
```

### Table: `comment_tag`
Pivot table untuk relasi many-to-many antara Comments dan Tags.

```sql
- id (PK)
- comment_id (FK) -> comments.id (CASCADE DELETE)
- tag_id (FK) -> tags.id (CASCADE DELETE)
- unique(comment_id, tag_id)  -- Cegah duplikat
- timestamps
```

## Models

### Tag Model (`app/Models/Tag.php`)
```php
// Relasi
$tag->comments()    // Dapatkan semua komentar dengan tag ini

// Methods
Tag::findOrCreateByName($name, $category)  // Cari atau buat tag
$tag->scopeActive($query)                  // Filter active tags
$tag->scopeByCategory($query, $category)   // Filter by category
```

### Comment Model (`app/Models/Comment.php`)
```php
// Relasi
$comment->commentTags()         // Dapatkan tags untuk komentar
$comment->tags()                // Shortcut untuk commentTags()

// Methods
$comment->attachTagsByName(['tag1', 'tag2'], $category)
$comment->syncTagsByName(['tag1', 'tag2'], $category)  // Replace existing
```

## API Endpoints

### Tags Management

#### 1. List All Tags
```
GET /api/tags
Query Parameters:
  - category: Filter by category (optional)
  - active: true/false (default: true)
  - per_page: Pagination size (default: 50)
  - page: Page number

Response:
{
  "ok": true,
  "data": [
    {
      "id": 1,
      "name": "Kualitas Baik",
      "slug": "kualitas-baik",
      "category": "kualitas",
      "color": "#4CAF50",
      "count": 124,
      "is_active": true
    }
  ]
}
```

#### 2. Get Tags by Category
```
GET /api/tags/by-category/{category}
Example: /api/tags/by-category/kualitas

Response:
{
  "ok": true,
  "category": "kualitas",
  "tags": [
    { "id": 1, "name": "Kualitas Baik", ... },
    { "id": 2, "name": "Kualitas Jelek", ... }
  ],
  "total": 2
}
```

#### 3. Get Tag Statistics
```
GET /api/tags/stats/summary

Response:
{
  "ok": true,
  "stats": {
    "total_tags": 45,
    "active_tags": 40,
    "total_tagged_comments": 5234,
    "top_tags": [...],
    "tags_by_category": [...]
  }
}
```

#### 4. Get Comments with Specific Tag
```
GET /api/tags/{tagSlug}/comments
Query Parameters:
  - page: Page number
  - per_page: Items per page (default: 15)

Example: /api/tags/kualitas-baik/comments

Response:
{
  "ok": true,
  "tag": { "id": 1, "name": "Kualitas Baik", ... },
  "comments": {
    "data": [...],
    "current_page": 1,
    "total": 124,
    "per_page": 15
  }
}
```

#### 5. Get Product Tags
```
GET /api/products/{productId}/tags

Response:
{
  "ok": true,
  "tags": [
    {
      "id": 1,
      "name": "Kualitas Baik",
      "comments_count": 45
    }
  ],
  "total": 3
}
```

#### 6. Create Tag
```
POST /api/tags
Content-Type: application/json

Request:
{
  "name": "Kualitas Baik",
  "description": "Produk berkualitas baik dan sesuai deskripsi",
  "category": "kualitas",
  "color": "#4CAF50"
}

Response:
{
  "ok": true,
  "tag": { ... },
  "message": "Tag created or retrieved successfully"
}
```

#### 7. Update Tag
```
PUT /api/tags/{tagId}
Content-Type: application/json

Request:
{
  "name": "Kualitas Sangat Baik",
  "color": "#8BC34A",
  "is_active": true
}

Response:
{
  "ok": true,
  "tag": { ... },
  "message": "Tag updated successfully"
}
```

#### 8. Delete Tag
```
DELETE /api/tags/{tagId}

Response:
{
  "ok": true,
  "message": "Tag deleted successfully"
}
```

## Integration dengan Flask

### Dari Flask ke Laravel

Flask dapat mengirimkan tags dalam struktur review data:

```json
{
  "comment": "Produk bagus, cepat sampai",
  "tags": ["Kualitas Baik", "Pengiriman Cepat"],
  "rating": 5,
  ...
}
```

### Proses Penyimpanan Tags

1. **Bulk Insert Comments**: Comments diinsert ke database
2. **Queue Tags**: Tags dari setiap comment di-queue
3. **Attach Tags**: Setelah insert, tags di-attach menggunakan `syncTagsByName()`
4. **Auto Create**: Tags yang belum ada akan dibuat otomatis

### Flow Diagram

```
Flask          Laravel Controller       Database
  |                  |                     |
  |--send data------>|                     |
  |                  |--bulk insert------->|
  |                  |  comments           |
  |                  |<--comment IDs-------|
  |                  |                     |
  |                  |--create tags------->|
  |                  | if not exist        |
  |                  |<--tag IDs-----------|
  |                  |                     |
  |                  |--attach tags------->|
  |                  | to comments         |
  |                  |<--done--------------|
  |<--response-------|
```

## Usage Examples

### Dari Controller
```php
// Attach tags ke komentar
$comment->attachTagsByName(['Kualitas Baik', 'Pengiriman Cepat'], 'umum');

// Replace existing tags
$comment->syncTagsByName(['Kualitas Bagus']);

// Query comments dengan tag tertentu
$tag = Tag::where('slug', 'kualitas-baik')->first();
$comments = $tag->comments()->get();

// Query comments dengan multiple tags
$comments = Comment::whereHas('commentTags', function ($q) {
    $q->whereIn('tag_id', [1, 2, 3]);
})->get();

// Get tags untuk product
$product = Product::find(1);
$tags = Tag::whereHas('comments', function ($query) use ($product) {
    $query->where('product_id', $product->id);
})->get();
```

### Dari Frontend (JavaScript)
```javascript
// Get comments dengan tag tertentu
const response = await fetch('/api/tags/kualitas-baik/comments?page=1&per_page=15');
const data = await response.json();

// Get all tags untuk product
const response = await fetch('/api/products/12345-67890/tags');

// Get tag statistics
const response = await fetch('/api/tags/stats/summary');
```

## Setup & Deployment

### 1. Jalankan Migrations
```bash
cd backend/app-backend-laravel
php artisan migrate
```

Migrations yang akan dijalankan:
- `2025_12_17_000001_create_tags_table.php`
- `2025_12_17_000002_create_comment_tag_table.php`

### 2. Seed Default Tags (Optional)
Buat file seeder di `database/seeders/TagSeeder.php`:

```php
<?php
namespace Database\Seeders;

use Illuminate\Database\Seeder;
use App\Models\Tag;

class TagSeeder extends Seeder
{
    public function run()
    {
        $tags = [
            ['name' => 'Kualitas Baik', 'category' => 'kualitas', 'color' => '#4CAF50'],
            ['name' => 'Kualitas Jelek', 'category' => 'kualitas', 'color' => '#F44336'],
            ['name' => 'Pengiriman Cepat', 'category' => 'pengiriman', 'color' => '#2196F3'],
            ['name' => 'Pengiriman Lambat', 'category' => 'pengiriman', 'color' => '#FF9800'],
            ['name' => 'Harga Terjangkau', 'category' => 'harga', 'color' => '#8BC34A'],
            ['name' => 'Harga Mahal', 'category' => 'harga', 'color' => '#E91E63'],
        ];

        foreach ($tags as $tag) {
            Tag::firstOrCreate(
                ['slug' => \Illuminate\Support\Str::slug($tag['name'])],
                $tag
            );
        }
    }
}
```

Jalankan seeder:
```bash
php artisan db:seed --class=TagSeeder
```

### 3. Update Flask API (Optional)
Jika Flask perlu mengirimkan tags, update `api.py` untuk include tags dalam response dari scraper.

## Best Practices

1. **Kategori Tags**: Gunakan kategori yang konsisten:
   - `kualitas`: Kualitas produk
   - `pengiriman`: Layanan pengiriman
   - `harga`: Harga produk
   - `layanan`: Customer service
   - `packaging`: Kemasan

2. **Tag Naming**: Gunakan nama yang deskriptif dan user-friendly:
   - ✅ "Kualitas Baik"
   - ❌ "qual_good"

3. **Caching**: Kolom `count` di-cache untuk performa query. Update setelah bulk operations.

4. **Soft Deletes**: Pertimbangkan gunakan soft deletes untuk tags agar tidak merusak historical data.

5. **Indexes**: Pastikan index ada di:
   - `tags.slug`
   - `tags.category`
   - `tags.is_active`
   - `comment_tag.comment_id`
   - `comment_tag.tag_id`

## Troubleshooting

### Tags tidak muncul setelah ingest
1. Check Laravel logs untuk error
2. Verifikasi bahwa Flask mengirim field `tags` dalam payload
3. Check tabel `comment_tag` untuk relasi yang tersimpan

### Query tags sangat lambat
1. Pastikan indexes sudah ada
2. Gunakan `->active()` scope untuk filter hanya active tags
3. Gunakan `withCount()` untuk menghindari N+1 queries

### Tags duplikat
1. Slug field unique akan mencegah duplikat exact name
2. Gunakan `findOrCreateByName()` untuk memastikan tidak ada duplikat

---

**Last Updated**: December 17, 2025
