# Frontend Integration Guide - Comment Tags API

## Quick Start

Sistem tag komentar dengan relasi many-to-many antara Comments dan Tags. API ini memungkinkan frontend untuk mengambil, menampilkan, dan filter komentar berdasarkan tags.

## Base URL
```
http://localhost:8000/api
```

## Authentication
Semua endpoint memerlukan API Token di header:
```
Authorization: Bearer {api_token}
```

---

## API Endpoints

### 1. Get All Tags untuk Product
Dapatkan semua tags yang ada pada komentar produk tertentu.

**Endpoint:**
```
GET /api/products/{productId}/tags
```

**Response:**
```json
{
  "ok": true,
  "tags": [
    {
      "id": 1,
      "name": "Kualitas Baik",
      "slug": "kualitas-baik",
      "category": "kualitas",
      "color": "#4CAF50",
      "comments_count": 45
    },
    {
      "id": 2,
      "name": "Pengiriman Cepat",
      "slug": "pengiriman-cepat",
      "category": "pengiriman",
      "color": "#2196F3",
      "comments_count": 32
    }
  ],
  "total": 2
}
```

**Usage (JavaScript):**
```javascript
async function getProductTags(productId) {
  const response = await fetch(`/api/products/${productId}/tags`, {
    headers: {
      'Authorization': `Bearer ${apiToken}`,
      'Accept': 'application/json'
    }
  });
  const data = await response.json();
  return data.tags;
}
```

---

### 2. Get Comments dengan Tags (Relasi Database)
Dapatkan komentar dengan tags yang sudah di-attach melalui relasi M2M.

**Endpoint:**
```
GET /api/comments/{productId}/with-tags?page=1&per_page=15
```

**Query Parameters:**
- `page`: Halaman (default: 1)
- `per_page`: Items per halaman (default: 15)

**Response:**
```json
{
  "ok": true,
  "product_id": "129681898-2110555906",
  "comments": {
    "current_page": 1,
    "data": [
      {
        "id": 123,
        "comment": "Produk bagus, pengiriman cepat",
        "rating": 5,
        "sentiment": "positive",
        "trust_score": 85.5,
        "comment_tags": [
          {
            "id": 1,
            "name": "Kualitas Baik",
            "slug": "kualitas-baik",
            "color": "#4CAF50"
          },
          {
            "id": 2,
            "name": "Pengiriman Cepat",
            "slug": "pengiriman-cepat",
            "color": "#2196F3"
          }
        ]
      }
    ],
    "per_page": 15,
    "total": 265
  }
}
```

**Usage (React):**
```jsx
function CommentsList({ productId }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchComments() {
      const response = await fetch(`/api/comments/${productId}/with-tags?page=1&per_page=15`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('api_token')}`,
          'Accept': 'application/json'
        }
      });
      const data = await response.json();
      setComments(data.comments.data);
      setLoading(false);
    }
    fetchComments();
  }, [productId]);

  return (
    <div>
      {comments.map(comment => (
        <div key={comment.id}>
          <p>{comment.comment}</p>
          <div className="tags">
            {comment.comment_tags.map(tag => (
              <span 
                key={tag.id} 
                style={{ backgroundColor: tag.color }}
                className="tag-badge"
              >
                {tag.name}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

### 3. Get Tags untuk Comment Spesifik
Dapatkan semua tags dari satu komentar.

**Endpoint:**
```
GET /api/comments/{productId}/detail/{commentId}/tags
```

**Response:**
```json
{
  "ok": true,
  "comment_id": 123,
  "tags_from_relation": [
    {
      "id": 1,
      "name": "Kualitas Baik",
      "slug": "kualitas-baik",
      "category": "kualitas",
      "color": "#4CAF50"
    }
  ],
  "tags_from_json": ["Kualitas Baik", "Pengiriman Cepat"],
  "total_tags": 1
}
```

---

### 4. Get Comments dengan Tag Tertentu
Filter komentar berdasarkan tag slug.

**Endpoint:**
```
GET /api/tags/{tagSlug}/comments?page=1&per_page=15
```

**Response:**
```json
{
  "ok": true,
  "tag": {
    "id": 1,
    "name": "Kualitas Baik",
    "slug": "kualitas-baik",
    "category": "kualitas"
  },
  "comments": {
    "current_page": 1,
    "data": [...],
    "total": 45
  }
}
```

**Usage:**
```javascript
async function getCommentsByTag(tagSlug, page = 1) {
  const response = await fetch(`/api/tags/${tagSlug}/comments?page=${page}&per_page=15`, {
    headers: {
      'Authorization': `Bearer ${apiToken}`,
      'Accept': 'application/json'
    }
  });
  return await response.json();
}

// Example: Get comments dengan tag "kualitas-baik"
const data = await getCommentsByTag('kualitas-baik');
```

---

### 5. Get All Available Tags
Dapatkan semua tags yang tersedia (untuk filter UI).

**Endpoint:**
```
GET /api/tags?category=kualitas&active=true&per_page=50
```

**Query Parameters:**
- `category`: Filter by category (optional)
- `active`: true/false (default: true)
- `per_page`: Items per page (default: 50)

**Response:**
```json
{
  "ok": true,
  "data": {
    "current_page": 1,
    "data": [
      {
        "id": 1,
        "name": "Kualitas Baik",
        "slug": "kualitas-baik",
        "category": "kualitas",
        "color": "#4CAF50",
        "count": 124
      }
    ]
  }
}
```

---

### 6. Get Tags by Category
Dapatkan tags berdasarkan kategori (untuk filter dropdown).

**Endpoint:**
```
GET /api/tags/by-category/{category}
```

**Categories:**
- `kualitas` - Kualitas produk
- `pengiriman` - Layanan pengiriman
- `harga` - Harga produk
- `layanan` - Customer service
- `rekomendasi` - Rekomendasi
- `autentisitas` - Produk asli/palsu

**Response:**
```json
{
  "ok": true,
  "category": "kualitas",
  "tags": [
    {
      "id": 1,
      "name": "Kualitas Baik",
      "slug": "kualitas-baik",
      "color": "#4CAF50"
    },
    {
      "id": 2,
      "name": "Kualitas Jelek",
      "slug": "kualitas-jelek",
      "color": "#F44336"
    }
  ],
  "total": 2
}
```

---

## UI Component Examples

### Tag Badge Component (React)
```jsx
function TagBadge({ tag, onClick }) {
  return (
    <span 
      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium cursor-pointer"
      style={{ 
        backgroundColor: tag.color + '20',
        color: tag.color,
        border: `1px solid ${tag.color}`
      }}
      onClick={() => onClick && onClick(tag)}
    >
      {tag.name}
    </span>
  );
}
```

### Tag Filter Component (React)
```jsx
function TagFilter({ productId, onFilterChange }) {
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);

  useEffect(() => {
    // Fetch available tags
    fetch(`/api/products/${productId}/tags`, {
      headers: { 'Authorization': `Bearer ${apiToken}` }
    })
    .then(res => res.json())
    .then(data => setTags(data.tags));
  }, [productId]);

  const toggleTag = (tag) => {
    const newSelected = selectedTags.includes(tag.slug)
      ? selectedTags.filter(s => s !== tag.slug)
      : [...selectedTags, tag.slug];
    
    setSelectedTags(newSelected);
    onFilterChange(newSelected);
  };

  return (
    <div className="tag-filter">
      <h3>Filter by Tags</h3>
      <div className="flex flex-wrap gap-2">
        {tags.map(tag => (
          <TagBadge
            key={tag.id}
            tag={tag}
            onClick={() => toggleTag(tag)}
            selected={selectedTags.includes(tag.slug)}
          />
        ))}
      </div>
    </div>
  );
}
```

### Comment Card with Tags (Vue)
```vue
<template>
  <div class="comment-card">
    <div class="comment-content">
      <p>{{ comment.comment }}</p>
      <div class="comment-meta">
        <span>Rating: {{ comment.rating }}/5</span>
        <span>Trust Score: {{ comment.trust_score }}</span>
      </div>
    </div>
    
    <div class="comment-tags">
      <span 
        v-for="tag in comment.comment_tags" 
        :key="tag.id"
        class="tag-badge"
        :style="{ backgroundColor: tag.color }"
      >
        {{ tag.name }}
      </span>
    </div>
  </div>
</template>

<script>
export default {
  props: ['comment']
}
</script>

<style scoped>
.tag-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  margin: 2px;
  color: white;
}
</style>
```

---

## Complete Example: Product Comments Page

```jsx
import React, { useState, useEffect } from 'react';

function ProductCommentsPage({ productId }) {
  const [comments, setComments] = useState([]);
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  // Fetch product tags
  useEffect(() => {
    fetch(`/api/products/${productId}/tags`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('api_token')}`,
        'Accept': 'application/json'
      }
    })
    .then(res => res.json())
    .then(data => setTags(data.tags || []));
  }, [productId]);

  // Fetch comments with tags
  useEffect(() => {
    setLoading(true);
    fetch(`/api/comments/${productId}/with-tags?page=${page}&per_page=15`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('api_token')}`,
        'Accept': 'application/json'
      }
    })
    .then(res => res.json())
    .then(data => {
      setComments(data.comments.data || []);
      setLoading(false);
    });
  }, [productId, page, selectedTags]);

  const toggleTagFilter = (tagSlug) => {
    setSelectedTags(prev => 
      prev.includes(tagSlug) 
        ? prev.filter(s => s !== tagSlug)
        : [...prev, tagSlug]
    );
    setPage(1); // Reset to first page
  };

  if (loading) return <div>Loading...</div>;

  return (
    <div className="product-comments-page">
      {/* Tag Filter Section */}
      <div className="filters mb-4">
        <h3 className="text-lg font-semibold mb-2">Filter by Tags</h3>
        <div className="flex flex-wrap gap-2">
          {tags.map(tag => (
            <button
              key={tag.id}
              onClick={() => toggleTagFilter(tag.slug)}
              className={`px-3 py-1 rounded-full text-sm ${
                selectedTags.includes(tag.slug) ? 'ring-2 ring-offset-2' : ''
              }`}
              style={{ 
                backgroundColor: tag.color + '20',
                color: tag.color,
                border: `1px solid ${tag.color}`
              }}
            >
              {tag.name} ({tag.comments_count})
            </button>
          ))}
        </div>
      </div>

      {/* Comments List */}
      <div className="comments-list space-y-4">
        {comments.map(comment => (
          <div key={comment.id} className="bg-white p-4 rounded-lg shadow">
            <div className="flex justify-between items-start mb-2">
              <span className="font-semibold">{comment.username}</span>
              <span className="text-yellow-500">★ {comment.rating}/5</span>
            </div>
            
            <p className="text-gray-700 mb-3">{comment.comment}</p>
            
            <div className="flex flex-wrap gap-2 mb-2">
              {comment.comment_tags?.map(tag => (
                <span
                  key={tag.id}
                  className="px-2 py-1 rounded text-xs"
                  style={{ 
                    backgroundColor: tag.color + '30',
                    color: tag.color
                  }}
                >
                  {tag.name}
                </span>
              ))}
            </div>
            
            <div className="flex gap-4 text-sm text-gray-500">
              <span>Trust Score: {comment.trust_score?.toFixed(1)}</span>
              <span className={comment.sentiment === 'positive' ? 'text-green-600' : 'text-red-600'}>
                {comment.sentiment}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination */}
      <div className="pagination mt-4 flex justify-center gap-2">
        <button 
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
        >
          Previous
        </button>
        <span className="px-4 py-2">Page {page}</span>
        <button 
          onClick={() => setPage(p => p + 1)}
          className="px-4 py-2 bg-blue-500 text-white rounded"
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default ProductCommentsPage;
```

---

## Troubleshooting

### Tags tidak muncul di response
1. Pastikan sudah run migration: `php artisan migrate`
2. Seed default tags: `php artisan db:seed --class=TagSeeder`
3. Cek relasi di database tabel `comment_tag`

### Comments tidak memiliki tags
- Tags harus di-attach saat ingest dari Flask
- Flask harus mengirimkan field `tags` dalam array
- Alternatif: Attach tags manual via API atau database

### Performance slow saat load banyak comments dengan tags
- Gunakan `with('commentTags')` untuk eager loading
- Implementasi caching untuk product tags
- Batasi per_page ke 15-20 items

---

**Last Updated**: December 17, 2025
