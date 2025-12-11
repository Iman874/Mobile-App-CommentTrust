# CommentTrust API Documentation

## Overview

CommentTrust adalah platform untuk menganalisis kualitas, kepercayaan, dan deteksi fake reviews pada komentar produk. API ini menyediakan endpoints untuk user registration, product analysis, comment filtering, dan sentiment analysis.

**Base URL:** `http://localhost:8000/api` (development)

## Architecture

```
Mobile App / Web Client
    ↓ (HTTP REST + Bearer Token)
Laravel Backend API (Orchestrator)
    ↓ (HTTP)
Flask Backend (Analysis Engine)
    ↓
Data Storage (JSON files in output/)
```

## Authentication

### API Token Authentication

Semua protected endpoints memerlukan Bearer token dalam header Authorization.

**Header Format:**
```
Authorization: Bearer {api_token}
```

**Mendapatkan Token:**

1. Register user baru:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "password_confirmation": "password123"
  }'
```

Response:
```json
{
  "ok": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com"
  },
  "api_token": "abc123xyz...",
  "token_type": "Bearer"
}
```

2. Login dengan email dan password:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "password123"
  }'
```

3. Simpan `api_token` di client dan gunakan untuk semua requests.

## API Endpoints

### 1. Authentication (Auth)

#### Register User
- **POST** `/api/auth/register`
- **Public** (No token required)

**Request:**
```json
{
  "name": "string (required)",
  "email": "string (required, unique)",
  "password": "string (required, min 8 chars)",
  "password_confirmation": "string (required, must match password)"
}
```

**Response (201):**
```json
{
  "ok": true,
  "message": "User registered successfully",
  "user": { "id": 1, "name": "...", "email": "..." },
  "api_token": "...",
  "token_type": "Bearer"
}
```

#### Login
- **POST** `/api/auth/login`
- **Public** (No token required)

**Request:**
```json
{
  "email": "string (required)",
  "password": "string (required)"
}
```

**Response (200):**
```json
{
  "ok": true,
  "message": "Login successful",
  "user": { "id": 1, "name": "...", "email": "..." },
  "api_token": "...",
  "token_type": "Bearer"
}
```

#### Get Current User
- **GET** `/api/auth/me`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2025-01-01T10:00:00Z",
    "updated_at": "2025-01-01T10:00:00Z"
  }
}
```

#### Update Profile
- **PUT** `/api/auth/profile/update`
- **Protected**

**Request:**
```json
{
  "name": "string (optional)",
  "email": "string (optional, unique)",
  "current_password": "string (required if changing password)",
  "password": "string (optional, min 8 chars)",
  "password_confirmation": "string (required if changing password)"
}
```

#### Generate New Token
- **POST** `/api/auth/token/generate`
- **Protected**

**Request:**
```json
{
  "token_name": "string (optional, default: 'default')"
}
```

**Response (200):**
```json
{
  "ok": true,
  "message": "New API token generated",
  "api_token": "...",
  "token_type": "Bearer",
  "token_name": "..."
}
```

#### Revoke Token
- **POST** `/api/auth/token/revoke`
- **Protected**

#### Validate Token
- **POST** `/api/auth/token/validate`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "message": "Token is valid",
  "user_id": 1,
  "user_name": "John Doe"
}
```

#### Logout
- **POST** `/api/auth/logout`
- **Protected**
- Alias untuk `/api/auth/token/revoke`

---

### 1.5. Guest Authentication (NEW)

Guest users dapat login tanpa registrasi. Akun guest otomatis dibuat dengan nama unik dan token yang berlaku 24 jam.

#### How Guest Login Works

```
1. User requests /api/guest/login (no credentials needed)
2. System generates unique guest username: guest-2025-01-15-09-am-1
3. Guest account created with is_guest=true, token_expires_at=now()+24h
4. API token returned (valid for exactly 24 hours)
5. Token auto-expires after 24 hours
6. Guest can refresh token or convert to regular account
```

#### Login as Guest
- **POST** `/api/guest/login`
- **Public** (No authentication required)

**Request:**
```json
{}
```
(Empty request body - no credentials needed)

**Response (201):**
```json
{
  "ok": true,
  "message": "Guest account created and logged in",
  "user": {
    "id": 5,
    "name": "guest-2025-01-15-09-am-1",
    "email": "guest-2025-01-15-09-am-1@guest.local",
    "is_guest": true,
    "created_at": "2025-01-15T09:00:00Z"
  },
  "api_token": "guest_token_abc123xyz...",
  "token_type": "Bearer",
  "expires_at": "2025-01-16T09:00:00Z",
  "expires_in_seconds": 86400
}
```

**Guest Username Format:**
```
guest-{YYYY-MM-DD}-{HH}-{am/pm}-{increment}

Examples:
- guest-2025-01-15-09-am-1   (First guest login at 09:00 AM on Jan 15)
- guest-2025-01-15-09-am-2   (Second guest login at 09:00 AM on Jan 15)
- guest-2025-01-15-02-pm-1   (First guest login at 02:00 PM on Jan 15)
```

#### Refresh Guest Token
- **POST** `/api/guest/refresh-token`
- **Protected** (Guest user only)

Used to extend guest token for another 24 hours before it expires.

**Response (200):**
```json
{
  "ok": true,
  "message": "Token refreshed successfully",
  "api_token": "new_guest_token_def456...",
  "token_type": "Bearer",
  "expires_at": "2025-01-17T09:00:00Z",
  "expires_in_seconds": 86400
}
```

#### Check Token Status
- **GET** `/api/guest/token-status`
- **Protected** (Guest user only)

Check if token is still valid and when it expires.

**Response (200):**
```json
{
  "ok": true,
  "user": {
    "id": 5,
    "name": "guest-2025-01-15-09-am-1",
    "is_guest": true
  },
  "token_status": {
    "is_valid": true,
    "is_expired": false,
    "expires_at": "2025-01-16T09:00:00Z",
    "expires_in_seconds": 43200
  }
}
```

**If Token Expired (401):**
```json
{
  "ok": false,
  "error": "token_expired",
  "message": "Guest token has expired. Please refresh or login again.",
  "refresh_url": "/api/guest/refresh-token",
  "login_url": "/api/guest/login"
}
```

#### Convert Guest to Regular User
- **POST** `/api/guest/convert-to-user`
- **Protected** (Guest user only)

Convert temporary guest account to permanent account with password.

**Request:**
```json
{
  "email": "user@example.com (optional, must be unique)",
  "password": "string (required, min 8 chars)",
  "password_confirmation": "string (required, must match password)"
}
```

**Response (200):**
```json
{
  "ok": true,
  "message": "Guest account converted to premium account",
  "user": {
    "id": 5,
    "name": "guest-2025-01-15-09-am-1",
    "email": "user@example.com",
    "is_guest": false,
    "created_at": "2025-01-15T09:00:00Z"
  },
  "api_token": "premium_token_ghi789...",
  "token_type": "Bearer",
  "note": "Token no longer expires. Valid indefinitely."
}
```

#### Logout Guest
- **POST** `/api/guest/logout`
- **Protected** (Guest user only)

Revoke guest token immediately.

**Response (200):**
```json
{
  "ok": true,
  "message": "Guest logged out successfully. Token revoked."
}
```

---

### Error Responses for Guest Operations

**Missing or Expired Token (401):**
```json
{
  "ok": false,
  "error": "token_expired",
  "message": "Your guest token has expired. Refresh it or login again.",
  "refresh_url": "/api/guest/refresh-token",
  "login_url": "/api/guest/login"
}
```

**Not a Guest User (403):**
```json
{
  "ok": false,
  "error": "not_guest_user",
  "message": "This operation is only available for guest users"
}
```

**Account Already Exists (409):**
```json
{
  "ok": false,
  "error": "account_exists",
  "message": "Email already registered. Please use login instead."
}
```

---

### 2. Products Management

#### List Products
- **GET** `/api/products`
- **Protected**

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 10, max: 100)
- `search` (string, optional) - Search by name or product_key

**Response (200):**
```json
{
  "ok": true,
  "products": [
    {
      "id": 1,
      "user_id": 1,
      "product_key": "product_123",
      "name": "Product Name",
      "avg_rating": 4.81,
      "count_reviews": 150,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "total": 50,
    "per_page": 10,
    "current_page": 1,
    "last_page": 5,
    "from": 1,
    "to": 10
  }
}
```

#### Create Product / Start Analysis
- **POST** `/api/products`
- **Protected**

**Request:**
```json
{
  "product_url": "string (required, valid URL)"
}
```

**Response (201):**
```json
{
  "ok": true,
  "job_id": "job_123",
  "message": "Analysis job started",
  "product_url": "https://...",
  "check_status_url": "/api/analysis/job/job_123"
}
```

#### Get Product Details
- **GET** `/api/products/{id}`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "product": {
    "id": 1,
    "product_key": "product_123",
    "name": "Product Name",
    "avg_rating": 4.81,
    ...
  },
  "stats": {
    "ok": true,
    "metrics": {
      "count_reviews": 150,
      "avg_rating": 4.81,
      "avg_trust_score": 76.5,
      "fake_rate": 0.05
    }
  }
}
```

#### Update Product
- **PUT** `/api/products/{id}`
- **Protected**

**Request:**
```json
{
  "name": "string (optional)",
  "notes": "string (optional)"
}
```

#### Delete Product
- **DELETE** `/api/products/{id}`
- **Protected**

#### Get Product Stats
- **GET** `/api/products/{id}/stats`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "product_key": "product_123",
  "stats": {
    "ok": true,
    "metrics": {
      "count_reviews": 150,
      "avg_rating": 4.81,
      "avg_trust_score": 76.5,
      "fake_rate": 0.05
    }
  }
}
```

#### Get Sentiment Breakdown
- **GET** `/api/products/{id}/sentiment-breakdown`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "sentiment_breakdown": {
    "positive": 100,
    "negative": 30,
    "neutral": 20
  },
  "sentiment_percentages": {
    "positive": 66.67,
    "negative": 20.0,
    "neutral": 13.33
  },
  "total_comments": 150
}
```

#### Get Rating Distribution
- **GET** `/api/products/{id}/rating-distribution`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "rating_distribution": {
    "1": 5,
    "2": 10,
    "3": 15,
    "4": 60,
    "5": 60
  },
  "rating_percentages": {
    "1": 3.33,
    "2": 6.67,
    "3": 10.0,
    "4": 40.0,
    "5": 40.0
  },
  "total_comments": 150,
  "average_rating": 4.81
}
```

---

### 3. Comments Management

#### Get Comments for Product
- **GET** `/api/comments/{productId}`
- **Protected**

**Query Parameters:**
- `page` (int, default: 1)
- `per_page` (int, default: 15)
- `sentiment` (string) - Filter: positive, negative, neutral
- `tags` (string) - Comma-separated tag list
- `search` (string) - Text search
- `sort_by` (string) - newest, oldest, rating_asc, rating_desc, trust_asc, trust_desc

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "product_key": "product_123",
  "comments": [
    {
      "comment_id": "comment_1",
      "user_name": "User Name",
      "rating_star": 5,
      "text": "Great product!",
      "sentiment": "positive",
      "trust_score": 85.3,
      "is_fake": false,
      "tags": ["quality", "value"],
      "created_at": "2025-01-01T10:00:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "per_page": 15,
  "tag_stats": {
    "quality": 45,
    "value": 38,
    ...
  },
  "filters_applied": {
    "sentiment": "positive",
    "tags": ["quality"],
    "search": null,
    "sort_by": "newest"
  }
}
```

#### Get Single Comment
- **GET** `/api/comments/{productId}/detail/{commentId}`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "comment": {
    "comment_id": "comment_1",
    "user_name": "User Name",
    "rating_star": 5,
    "text": "Great product!",
    "sentiment": "positive",
    "trust_score": 85.3,
    "is_fake": false,
    "tags": ["quality"],
    ...
  }
}
```

#### Advanced Filter
- **POST** `/api/comments/{productId}/filter`
- **Protected**

**Request:**
```json
{
  "sentiment": "string (optional)",
  "rating_min": "int (optional, 1-5)",
  "rating_max": "int (optional, 1-5)",
  "has_tags": "boolean (optional)",
  "is_fake": "boolean (optional)",
  "trust_score_min": "float (optional, 0-100)",
  "trust_score_max": "float (optional, 0-100)"
}
```

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "comments": [...],
  "count": 50,
  "filters_applied": {
    "sentiment": "positive",
    "rating_min": 4,
    "rating_max": 5,
    ...
  }
}
```

#### Search Comments
- **GET** `/api/comments/{productId}/search`
- **Protected**

**Query Parameters:**
- `q` (string, required, min 2 chars) - Search query

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "search_query": "quality",
  "comments": [...],
  "count": 45
}
```

#### Get Comment Statistics
- **GET** `/api/comments/{productId}/stats`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "product_id": 1,
  "stats": {
    "total_comments": 150,
    "average_rating": 4.81,
    "average_trust_score": 76.5,
    "sentiment_distribution": {
      "positive": 100,
      "negative": 30,
      "neutral": 20,
      "percentages": {
        "positive": 66.67,
        "negative": 20.0,
        "neutral": 13.33
      }
    },
    "rating_distribution": { "1": 5, "2": 10, ... },
    "fake_review_count": 8,
    "tagged_comment_count": 95,
    "tag_cloud": {
      "quality": 45,
      "value": 38,
      ...
    },
    "most_common_tags": {
      "quality": 45,
      "value": 38,
      ...
    }
  }
}
```

---

### 4. Analysis & Jobs

#### Start Full Analysis (Scrape + Analyze)
- **POST** `/api/analysis/start`
- **Protected**

**Request:**
```json
{
  "product_url": "string (required, valid URL)"
}
```

**Response (200):**
```json
{
  "ok": true,
  "job_id": "job_123",
  "message": "Analysis job started",
  "product_url": "https://..."
}
```

#### Check Job Status
- **GET** `/api/analysis/job/{jobId}`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "job": {
    "job_id": "job_123",
    "status": "completed", // queued, processing, completed, failed
    "progress": 100,
    "product_id": "product_123",
    "error": null,
    "started_at": "2025-01-01T10:00:00Z",
    "completed_at": "2025-01-01T10:05:00Z"
  }
}
```

#### Get All User Products
- **GET** `/api/analysis/products`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "products": [...],
  "count": 5
}
```

#### Get Product Analysis
- **GET** `/api/analysis/product/{productId}`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "product_id": "product_123",
  "product": { ... },
  "analysis": { ... },
  "in_database": true
}
```

#### Get Product Comments
- **GET** `/api/analysis/product/{productId}/comments`
- **Protected**

Same as `/api/comments/{productId}`

#### Scrape Only (No Analysis)
- **POST** `/api/analysis/scrape`
- **Protected**

**Request:**
```json
{
  "product_url": "string (required)"
}
```

#### Analyze Only (From Existing Data)
- **POST** `/api/analysis/analyze/{productId}`
- **Protected**

#### Re-analyze Product
- **POST** `/api/analysis/reanalyze/{productId}`
- **Protected**

**Response (200):**
```json
{
  "ok": true,
  "job_id": "job_456",
  "message": "Re-analysis started",
  "product_id": "product_123"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "ok": false,
  "message": "Failed to get comments",
  "error": "Product data not found"
}
```

### 401 Unauthorized
```json
{
  "ok": false,
  "message": "Unauthorized"
}
```

### 403 Forbidden
```json
{
  "ok": false,
  "message": "Unauthorized access to this product"
}
```

### 404 Not Found
```json
{
  "ok": false,
  "message": "Product not found or unauthorized"
}
```

### 422 Validation Error
```json
{
  "ok": false,
  "message": "Validation failed",
  "errors": {
    "email": ["The email field is required."],
    "password": ["The password must be at least 8 characters."]
  }
}
```

### 500 Server Error
```json
{
  "ok": false,
  "message": "Internal server error",
  "error": "..."
}
```

---

## Implementation Examples

### JavaScript/TypeScript (Fetch API)

```javascript
const API_BASE_URL = 'http://localhost:8000/api';
let apiToken = null;

// Register
async function register(name, email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name, email, password,
      password_confirmation: password
    })
  });
  const data = await response.json();
  if (data.ok) {
    apiToken = data.api_token;
    localStorage.setItem('api_token', apiToken);
  }
  return data;
}

// Login
async function login(email, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await response.json();
  if (data.ok) {
    apiToken = data.api_token;
    localStorage.setItem('api_token', apiToken);
  }
  return data;
}

// Get Products
async function getProducts(page = 1, search = '') {
  const params = new URLSearchParams({ page, search });
  const response = await fetch(
    `${API_BASE_URL}/products?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${apiToken}`
      }
    }
  );
  return response.json();
}

// Start Analysis
async function startAnalysis(productUrl) {
  const response = await fetch(`${API_BASE_URL}/analysis/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiToken}`
    },
    body: JSON.stringify({ product_url: productUrl })
  });
  return response.json();
}

// Get Comments
async function getComments(productId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(
    `${API_BASE_URL}/comments/${productId}?${params}`,
    {
      headers: {
        'Authorization': `Bearer ${apiToken}`
      }
    }
  );
  return response.json();
}
```

### Python (Requests)

```python
import requests

API_BASE_URL = 'http://localhost:8000/api'
api_token = None

def register(name, email, password):
    global api_token
    response = requests.post(
        f'{API_BASE_URL}/auth/register',
        json={
            'name': name,
            'email': email,
            'password': password,
            'password_confirmation': password
        }
    )
    data = response.json()
    if data['ok']:
        api_token = data['api_token']
    return data

def login(email, password):
    global api_token
    response = requests.post(
        f'{API_BASE_URL}/auth/login',
        json={'email': email, 'password': password}
    )
    data = response.json()
    if data['ok']:
        api_token = data['api_token']
    return data

def get_products(page=1, search=''):
    headers = {'Authorization': f'Bearer {api_token}'}
    response = requests.get(
        f'{API_BASE_URL}/products',
        params={'page': page, 'search': search},
        headers=headers
    )
    return response.json()

def start_analysis(product_url):
    headers = {'Authorization': f'Bearer {api_token}'}
    response = requests.post(
        f'{API_BASE_URL}/analysis/start',
        json={'product_url': product_url},
        headers=headers
    )
    return response.json()
```

---

## Data Models

### User Model
```json
{
  "id": "integer",
  "name": "string",
  "email": "string (unique)",
  "api_token": "string (hashed)",
  "api_token_name": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Product Model
```json
{
  "id": "integer",
  "user_id": "integer (foreign key)",
  "product_key": "string (unique)",
  "name": "string",
  "shopid": "string",
  "itemid": "string",
  "ratings": "json",
  "summaries": "json",
  "avg_rating": "float",
  "count_reviews": "integer",
  "avg_trust_score": "float",
  "fake_rate": "float",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Comment Model
```json
{
  "id": "integer",
  "user_id": "integer (foreign key)",
  "product_id": "integer (foreign key)",
  "comment_id": "string",
  "text": "string",
  "rating_star": "float (1-5)",
  "sentiment": "enum: positive, negative, neutral",
  "trust_score": "float (0-100)",
  "is_fake": "boolean",
  "tags": "json array",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## Environment Configuration

File: `.env`

```dotenv
# Laravel Configuration
APP_NAME=CommentTrust
APP_ENV=local
APP_KEY=base64:...
APP_DEBUG=true
APP_URL=http://localhost:8000

# Database
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=comment_trust
DB_USERNAME=root
DB_PASSWORD=

# Flask Backend
FLASK_API_URL=http://localhost:5000
```

---

## Development Setup

### Prerequisites
- PHP 8.1+
- Composer
- MySQL/SQLite
- Flask backend running on port 5000

### Installation

```bash
# 1. Install dependencies
cd backend/app-backend-laravel
composer install

# 2. Create .env file
cp .env.example .env

# 3. Generate app key
php artisan key:generate

# 4. Run migrations
php artisan migrate

# 5. Start server
php artisan serve
```

### Database Migrations

```bash
# Run all pending migrations
php artisan migrate

# Roll back last migration
php artisan migrate:rollback

# Fresh migration (WARNING: drops all tables)
php artisan migrate:fresh
```

---

## Rate Limiting & Best Practices

### Recommendations
- Cache token validation on client side
- Implement exponential backoff for failed requests
- Poll job status every 2-5 seconds
- Paginate large result sets
- Use search/filter to reduce data transfer

### Common Patterns

**Polling Job Status:**
```javascript
async function pollJobStatus(jobId, maxAttempts = 60) {
  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(
      `${API_BASE_URL}/analysis/job/${jobId}`,
      { headers: { 'Authorization': `Bearer ${apiToken}` } }
    );
    const data = await response.json();
    
    if (data.job.status === 'completed') return data.job;
    if (data.job.status === 'failed') throw new Error(data.job.error);
    
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  throw new Error('Job timeout');
}
```

---

## Support & Troubleshooting

### Common Issues

**Token Invalid / 401 Unauthorized**
- Verify token is included in Authorization header
- Check token hasn't expired or been revoked
- Regenerate token if needed

**Product Not Found / 403 Forbidden**
- Ensure product belongs to authenticated user
- Check product_key/product_id spelling
- Product may still be processing

**Analysis Job Stuck**
- Check job status endpoint
- Verify Flask backend is running
- Check Flask logs for errors

---

Generated: 2025-01-01
Last Updated: 2025-01-01
Version: 1.0.0
