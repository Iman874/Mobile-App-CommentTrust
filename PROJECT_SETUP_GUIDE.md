# CommentTrust Full Project Setup Guide

## Project Overview

CommentTrust adalah platform terintegrasi untuk menganalisis kualitas, kepercayaan, dan deteksi fake reviews pada komentar produk e-commerce. Sistem terdiri dari 3 komponen utama yang saling terintegrasi:

```
┌─────────────────────────────────────────────────────────────┐
│                    Flutter Mobile App                       │
│         (User Interface & Frontend Logic)                   │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST + Bearer Token
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Laravel Backend (Port 8000)                    │
│  • User Authentication & Token Management                   │
│  • Product CRUD & Data Management                           │
│  • Comment Filtering & Statistics                           │
│  • Job Orchestration                                        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP
                     │
┌────────────────────▼────────────────────────────────────────┐
│           Flask Analysis Engine (Port 5000)                 │
│  • Web Scraping (Tokopedia, Shopee, etc.)                  │
│  • Text Preprocessing & Tokenization                        │
│  • Sentiment Analysis                                       │
│  • Fake Review Detection                                    │
│  • Trust Score Calculation                                  │
│  • Comment Summarization & Tagging                          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│         Data Storage (JSON + MySQL/SQLite)                  │
│  • Products: output/scrap-data/{product_id}/product.json   │
│  • Reviews: output/scrap-data/{product_id}/review.json     │
│  • Database: user_id, products, comments, api_tokens       │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
Mobile-App-CommentTrust/
├── backend/
│   ├── app-backend-flask/              # Python Flask Analysis Engine
│   │   ├── main.py                     # Flask app entry point
│   │   ├── requirements.txt            # Python dependencies
│   │   ├── service/
│   │   │   └── api.py                  # Flask API endpoints
│   │   ├── utils/
│   │   │   ├── pipeline.py             # Analysis pipeline
│   │   │   └── progress_bar.py         # Progress tracking
│   │   ├── static/                     # Web UI for progress
│   │   │   ├── index.html
│   │   │   ├── progress.html
│   │   │   └── visualisasi.html
│   │   └── output/
│   │       └── scrap-data/             # Analyzed data storage
│   │           └── {product_id}/
│   │               ├── product.json    # Product metadata
│   │               └── review.json     # Comments with analysis
│   │
│   ├── app-backend-laravel/            # PHP Laravel Orchestrator
│   │   ├── app/
│   │   │   ├── Http/
│   │   │   │   ├── Controllers/
│   │   │   │   │   ├── AuthController.php
│   │   │   │   │   ├── ProductController.php
│   │   │   │   │   ├── CommentController.php
│   │   │   │   │   └── AnalysisController.php
│   │   │   │   └── Middleware/
│   │   │   │       └── ValidateApiToken.php
│   │   │   ├── Models/
│   │   │   │   ├── User.php
│   │   │   │   ├── Product.php
│   │   │   │   └── Comment.php
│   │   │   └── Services/
│   │   │       └── FlaskService.php
│   │   ├── database/
│   │   │   └── migrations/
│   │   │       ├── create_users_table.php
│   │   │       ├── add_api_token_to_users_table.php
│   │   │       ├── add_user_id_to_products_table.php
│   │   │       └── add_user_id_to_comments_table.php
│   │   ├── routes/
│   │   │   └── api.php                 # API routes
│   │   ├── bootstrap/
│   │   │   └── app.php                 # Middleware registration
│   │   ├── config/
│   │   │   └── services.php            # Flask config
│   │   ├── storage/
│   │   │   └── database.sqlite         # Default database
│   │   ├── .env.example
│   │   ├── SETUP_GUIDE.md              # Laravel setup docs
│   │   └── API_DOCUMENTATION.md        # Complete API docs
│   │
│   └── Scrapper/                       # Python Data Collection
│       ├── main_analisis.py            # Analysis pipeline
│       ├── scrapper_comment.py         # Comment scraper
│       ├── scrapper_produk.py          # Product scraper
│       ├── requirements.txt            # Python dependencies
│       └── output/                     # Scraping results
│           ├── comment/
│           ├── produk/
│           └── review/
│
└── comment_trust_app/                  # Flutter Mobile App
    ├── lib/
    │   ├── main.dart                   # App entry point
    │   ├── services/
    │   │   └── api_service.dart        # Backend API client
    │   ├── providers/
    │   │   └── auth_provider.dart      # State management
    │   ├── screens/                    # UI screens
    │   │   ├── login_screen.dart
    │   │   ├── home_screen.dart
    │   │   └── ...
    │   └── frontend/                   # Flutter components
    ├── pubspec.yaml                    # Dart dependencies
    ├── android/                        # Android configuration
    ├── ios/                            # iOS configuration
    └── BACKEND_INTEGRATION_GUIDE.md    # Integration docs
```

## Setup Instructions

### Phase 1: Flask Backend Setup (5-10 minutes)

The Flask backend provides the analysis engine. It must run on port 5000.

```bash
# 1. Navigate to Flask project
cd backend/app-backend-flask

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run Flask server
python main.py
# Output: Flask running at http://localhost:5000

# 5. Verify it's working
curl http://localhost:5000/api/ping
# Response: {"status": "ok"}
```

**Troubleshooting:**
- If Selenium/Edge driver fails: Check `edgedriver_linux64/` or `edgedriver_win64/`
- If port 5000 in use: `lsof -i :5000` then kill process or use `--port 5001`
- Check logs in `backend/app-backend-flask/log/`

### Phase 2: Laravel Backend Setup (10-15 minutes)

The Laravel backend orchestrates communication between the mobile app and Flask.

```bash
# 1. Navigate to Laravel project
cd backend/app-backend-laravel

# 2. Install dependencies
composer install

# 3. Setup environment
cp .env.example .env
php artisan key:generate

# 4. Configure database (default: SQLite)
# .env already configured for SQLite at database/database.sqlite
# For MySQL, update .env with your credentials

# 5. Run database migrations
php artisan migrate
# Output:
# Migration: 2024_01_01_000000_create_users_table
# Migration: 2025_12_11_000001_add_api_token_to_users_table
# Migration: 2025_12_11_000002_add_user_id_to_products_table
# Migration: 2025_12_11_000003_add_user_id_to_comments_table

# 6. Start Laravel server (in new terminal)
php artisan serve
# Output: Laravel development server started: http://127.0.0.1:8000
```

**Verify Installation:**
```bash
# Test API is running
curl http://localhost:8000/api/ping
# Response: {"status":"ok"}

# Test database connection
php artisan tinker
# Type: User::count()
# Should return: 0 (no users yet)
# Type: exit
```

### Phase 3: Flask Backend Configuration

Update Laravel to know where Flask is running:

```bash
# Edit .env in Laravel directory
FLASK_API_URL=http://localhost:5000

# If Flask is on different machine:
FLASK_API_URL=http://192.168.1.100:5000
```

### Phase 4: Flutter App Setup (5-10 minutes)

```bash
# 1. Navigate to Flutter project
cd comment_trust_app

# 2. Get dependencies
flutter pub get

# 3. Update API server address
# Edit lib/services/api_service.dart:
# const String baseUrl = 'http://YOUR_LARAVEL_IP:8000/api';

# For physical device, use your machine's IP:
# const String baseUrl = 'http://192.168.1.100:8000/api';

# 4. Run app
flutter run

# For web:
flutter run -d chrome

# For specific device:
flutter devices
flutter run -d <device_id>
```

**Network Configuration:**
- **Emulator to localhost:** Use `10.0.2.2:8000` instead of `localhost:8000`
- **Physical device:** Use machine's IP address (e.g., `192.168.1.100:8000`)
- **iOS:** Requires special setup, see `BACKEND_INTEGRATION_GUIDE.md`

## Quick Start Demo

### 1. Create Test User

```bash
# Register new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "password_confirmation": "password123"
  }'

# Save the returned api_token
TOKEN="abc123xyz..."
```

### 2. Start Analysis

```bash
# Start analyzing a product
curl -X POST http://localhost:8000/api/analysis/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"product_url": "https://tokopedia.com/example/product-123"}'

# Response contains job_id: "job_123abc..."
```

### 3. Check Progress

```bash
# Poll job status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analysis/job/job_123abc

# Check status: queued → processing → completed
```

### 4. View Results

```bash
# List products
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/products

# Get comments for product
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/comments/{productId}?page=1&per_page=10&sentiment=positive"

# Get statistics
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/products/{productId}/stats
```

## API Authentication Flow

1. **Register/Login:**
   ```
   POST /api/auth/register
   → Response: {api_token: "...", user: {...}}
   ```

2. **Store Token:**
   ```
   Client stores api_token in SharedPreferences/localStorage
   ```

3. **Use Token:**
   ```
   GET /api/products
   Header: Authorization: Bearer abc123xyz...
   ```

4. **Token Validation:**
   ```
   Laravel ValidateApiToken middleware:
   1. Extract token from header
   2. Hash token
   3. Look up in users.api_token column
   4. Attach user to request if found
   5. Return 401 if not found
   ```

## Data Flow Example

### Complete Analysis Flow

```
1. Mobile App sends product URL
   POST /api/analysis/start
   {product_url: "https://..."}

2. Laravel receives request
   → Validates token → Gets user_id
   → Passes to Flask

3. Flask backend:
   a. Scrapes product & comments
   b. Preprocesses text
   c. Sentiment analysis
   d. Fake review detection
   e. Trust score calculation
   f. Saves to output/scrap-data/{product_id}/

4. Laravel receives job completion
   → Stores product in database
   → Links to user_id

5. Mobile App polls for status
   GET /api/analysis/job/{jobId}
   → Status: completed

6. Mobile App fetches results
   GET /api/comments/{productId}
   ← Returns analyzed comments with:
     - sentiment (positive/negative/neutral)
     - trust_score (0-100)
     - is_fake (true/false)
     - tags (quality, value, shipping, etc.)

7. Mobile App displays results
   - Comments sorted by sentiment
   - Trust score indicators
   - Fake review warnings
   - Statistical breakdown
```

## Database Schema

### Users Table
```sql
id (PK)
name
email (UNIQUE)
password
api_token (UNIQUE, NULLABLE) -- hashed
api_token_name
created_at
updated_at
```

### Products Table
```sql
id (PK)
user_id (FK) -- user ownership
product_key (UNIQUE) -- from Flask
name
shopid
itemid
ratings (JSON)
summaries (JSON)
avg_rating
count_reviews
avg_trust_score
fake_rate
created_at
updated_at
```

### Comments Table
```sql
id (PK)
user_id (FK) -- data isolation
product_id (FK)
comment_id (UNIQUE)
text
rating_star (1-5)
sentiment (enum)
trust_score (0-100)
is_fake (boolean)
tags (JSON array)
created_at
updated_at
```

## Environment Variables

### Laravel (.env)

```dotenv
# App Configuration
APP_NAME=CommentTrust
APP_ENV=local
APP_KEY=base64:...
APP_DEBUG=true
APP_URL=http://localhost:8000

# Database
DB_CONNECTION=sqlite
# OR for MySQL:
# DB_CONNECTION=mysql
# DB_HOST=127.0.0.1
# DB_DATABASE=comment_trust
# DB_USERNAME=root
# DB_PASSWORD=

# Flask Backend
FLASK_API_URL=http://localhost:5000
```

### Flask (environment)

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
export FLASK_APP=main.py
export FLASK_RUN_PORT=5000
```

## Common Tasks

### Add New Analysis Feature

1. **Implement in Flask** (`backend/app-backend-flask/utils/`)
2. **Wire in pipeline** (`utils/pipeline.py`)
3. **Expose endpoint** (`service/api.py`)
4. **Add Laravel method** (`app/Services/FlaskService.php`)
5. **Create route** (`routes/api.php`)
6. **Add controller action** (`app/Http/Controllers/*.php`)
7. **Update mobile app** (`comment_trust_app/lib/services/api_service.dart`)

### Analyze New E-commerce Platform

1. Add scraper in `Scrapper/` or `backend/app-backend-flask/`
2. Update product URL patterns
3. Configure Selenium driver
4. Test locally: `python scrapper_comment.py --url "..."`
5. Wire into Flask API endpoints

### Deploy to Production

1. **Laravel:**
   ```bash
   composer install --no-dev
   php artisan migrate --force
   php artisan cache:clear
   # Set APP_DEBUG=false, use HTTPS
   ```

2. **Flask:**
   ```bash
   pip install -r requirements.txt
   gunicorn -w 4 -b 0.0.0.0:5000 main:app
   # Use production WSGI server
   ```

3. **Flutter:**
   ```bash
   flutter build apk --release
   flutter build ios --release
   # Update API_URL to production server
   ```

## Monitoring & Debugging

### Check Service Status

```bash
# Flask is running?
curl http://localhost:5000/api/ping

# Laravel is running?
curl http://localhost:8000/api/ping

# Token valid?
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/auth/me
```

### View Logs

```bash
# Flask
tail -f backend/app-backend-flask/log/output.log

# Laravel
tail -f backend/app-backend-laravel/storage/logs/laravel.log

# Database queries
php artisan tinker
DB::listen(function($query) { echo $query->sql; });
```

### Test Database

```bash
# Check migrations
php artisan migrate:status

# Fresh database
php artisan migrate:fresh

# View tables
php artisan tinker
Schema::getTables();

# Count records
User::count();
Product::where('user_id', 1)->count();
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid/missing token | Check Authorization header format: `Bearer {token}` |
| 403 Forbidden | User doesn't own product | Verify product belongs to authenticated user |
| 404 Not Found | Product/comment missing | Check product_id exists in database |
| Connection timeout | Flask not running | Start Flask: `python main.py` |
| CORS errors | Origin not allowed | Update CORS in Laravel config |
| Database locked | SQLite concurrency | Use MySQL for production |
| Port in use | Another process using port | Kill existing process or use different port |

## Documentation Files

- **`API_DOCUMENTATION.md`** - Complete API reference with examples
- **`SETUP_GUIDE.md`** - Detailed Laravel setup instructions
- **`BACKEND_INTEGRATION_GUIDE.md`** - Flutter app integration guide
- **`README.md`** (Flask) - Flask backend documentation
- **`README.md`** (Laravel) - Laravel backend documentation

## Support & Resources

### Key Contact Points
- **Flask Issues:** Check `backend/app-backend-flask/log/`
- **Laravel Issues:** Check `backend/app-backend-laravel/storage/logs/`
- **Mobile App Issues:** Check Flutter console output
- **Network Issues:** Use `curl` to test endpoints directly

### Learning Resources
- Laravel Documentation: https://laravel.com/docs
- Flask Documentation: https://flask.palletsprojects.com/
- Flutter Documentation: https://flutter.dev/docs
- REST API Concepts: https://restfulapi.net/

### Example Workflows
See `API_DOCUMENTATION.md` for:
- JavaScript/TypeScript examples
- Python examples
- cURL examples
- Postman collection setup

## Next Steps

1. ✅ Setup Flask backend (port 5000)
2. ✅ Setup Laravel backend (port 8000)
3. ✅ Setup Flutter app
4. ✅ Test authentication flow
5. ✅ Start analyzing products
6. ✅ View results in mobile app
7. Deploy to production

---

**Generated:** 2025-01-01
**Version:** 1.0.0
**Last Updated:** 2025-01-01

For detailed information on any component, see the relevant documentation file in the component directory.
