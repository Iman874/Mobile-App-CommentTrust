# Laravel Backend Setup Guide

## Overview

Laravel backend bertindak sebagai orchestrator antara mobile app dan Flask analysis engine. Backend ini menangani:
- User authentication dan API token management
- Product data management
- Comment storage dan filtering
- Job status tracking
- Data isolation per user

## Prerequisites

- PHP 8.1 atau lebih tinggi
- Composer
- MySQL 8.0+ atau SQLite
- Node.js (untuk npm/yarn, optional untuk assets)
- Flask backend berjalan di `http://localhost:5000`

## Installation Steps

### 1. Setup Laravel Project

```bash
# Navigate to Laravel directory
cd backend/app-backend-laravel

# Install PHP dependencies
composer install

# Copy environment file
cp .env.example .env

# Generate application key
php artisan key:generate
```

### 2. Database Configuration

**Option A: SQLite (Default, Development)**

SQLite sudah dikonfigurasi di `.env.example`:
```dotenv
DB_CONNECTION=sqlite
```

Database file akan dibuat otomatis di `database/database.sqlite`

**Option B: MySQL (Production)**

Update `.env`:
```dotenv
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=comment_trust
DB_USERNAME=root
DB_PASSWORD=your_password
```

Buat database:
```bash
mysql -u root -p -e "CREATE DATABASE comment_trust CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 3. Run Migrations

```bash
# Run semua migrations
php artisan migrate

# Output:
# Migration: 2024_01_01_000000_create_users_table
# Migration: 2025_12_11_000001_add_api_token_to_users_table
# Migration: 2025_12_11_000002_add_user_id_to_products_table
# Migration: 2025_12_11_000003_add_user_id_to_comments_table
```

### 4. Configure Flask Backend

Update `.env`:
```dotenv
FLASK_API_URL=http://localhost:5000
```

Ensure Flask backend is running before starting Laravel.

### 5. Start Laravel Development Server

```bash
# Option 1: Built-in PHP server
php artisan serve
# Server running at: http://localhost:8000

# Option 2: Using Artisan with custom port
php artisan serve --port=8001

# Option 3: Using PHP directly
php -S localhost:8000 -t public
```

## Project Structure

```
app-backend-laravel/
├── app/
│   ├── Http/
│   │   ├── Controllers/
│   │   │   ├── AuthController.php       # User auth & token management
│   │   │   ├── ProductController.php    # Product CRUD & stats
│   │   │   ├── CommentController.php    # Comment filtering & search
│   │   │   └── AnalysisController.php   # Job management & analysis
│   │   └── Middleware/
│   │       └── ValidateApiToken.php     # Bearer token validation
│   ├── Models/
│   │   ├── User.php                     # User model with API token
│   │   ├── Product.php                  # Product model
│   │   └── Comment.php                  # Comment model
│   └── Services/
│       └── FlaskService.php             # HTTP client for Flask API
├── database/
│   └── migrations/
│       ├── 2024_01_01_000000_create_users_table.php
│       ├── 2025_12_11_000001_add_api_token_to_users_table.php
│       ├── 2025_12_11_000002_add_user_id_to_products_table.php
│       └── 2025_12_11_000003_add_user_id_to_comments_table.php
├── routes/
│   ├── api.php                          # API routes
│   └── web.php                          # Web routes
├── config/
│   ├── services.php                     # Flask service config
│   └── app.php                          # App config
├── bootstrap/
│   └── app.php                          # Middleware registration
├── storage/
│   ├── logs/                            # Application logs
│   └── database/                        # SQLite database (if used)
├── .env.example                         # Environment template
├── artisan                              # Laravel CLI
├── composer.json                        # PHP dependencies
└── API_DOCUMENTATION.md                 # Complete API docs
```

## API Routes Overview

### Public Routes (No Authentication)
```
POST /api/auth/register
POST /api/auth/login
GET  /api/ping
```

### Protected Routes (Require Bearer Token)
```
# Auth
GET  /api/auth/me
PUT  /api/auth/profile/update
POST /api/auth/logout
POST /api/auth/token/generate
POST /api/auth/token/revoke
POST /api/auth/token/validate

# Products
GET    /api/products
POST   /api/products
GET    /api/products/{id}
PUT    /api/products/{id}
DELETE /api/products/{id}
GET    /api/products/{id}/stats
GET    /api/products/{id}/sentiment-breakdown
GET    /api/products/{id}/rating-distribution

# Comments
GET  /api/comments/{productId}
GET  /api/comments/{productId}/detail/{commentId}
POST /api/comments/{productId}/filter
GET  /api/comments/{productId}/search
GET  /api/comments/{productId}/stats

# Analysis
POST /api/analysis/start
GET  /api/analysis/job/{jobId}
GET  /api/analysis/products
GET  /api/analysis/product/{productId}
GET  /api/analysis/product/{productId}/comments
POST /api/analysis/scrape
POST /api/analysis/analyze/{productId}
POST /api/analysis/reanalyze/{productId}
```

## Testing API Endpoints

### Using cURL

```bash
# Register user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123",
    "password_confirmation": "password123"
  }'

# Response
{
  "ok": true,
  "api_token": "abc123xyz...",
  "token_type": "Bearer",
  "user": {...}
}

# Save token (replace with actual token)
TOKEN="abc123xyz..."

# List products
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/products

# Start analysis
curl -X POST http://localhost:8000/api/analysis/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"product_url": "https://tokopedia.com/product/123"}'

# Check job status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/analysis/job/job_123
```

### Using Postman

1. Import API routes into Postman
2. Set up environment variable: `base_url = http://localhost:8000/api`
3. Add Auth -> Bearer Token type
4. Set token variable: `{{api_token}}`
5. Run requests

See `API_DOCUMENTATION.md` for complete endpoint list.

## Guest Login Testing

### Test Guest Login via API

Guest login memungkinkan users login instantly tanpa registrasi. Akun otomatis dibuat dengan nama unik dan token berlaku 24 jam.

**1. Login as Guest**
```bash
curl -X POST http://localhost:8000/api/guest/login \
  -H "Content-Type: application/json"

# Response (HTTP 201):
{
  "ok": true,
  "message": "Guest account created and logged in",
  "user": {
    "id": 1,
    "name": "guest-2025-01-15-09-am-1",
    "email": "guest-2025-01-15-09-am-1@guest.local",
    "is_guest": true
  },
  "api_token": "guest_token_abc123xyz...",
  "token_type": "Bearer",
  "expires_at": "2025-01-16T09:00:00Z",
  "expires_in_seconds": 86400
}

# Save token
GUEST_TOKEN="guest_token_abc123xyz..."
```

**2. Check Token Status**
```bash
curl -X GET http://localhost:8000/api/guest/token-status \
  -H "Authorization: Bearer $GUEST_TOKEN"

# Response:
{
  "ok": true,
  "user": {
    "id": 1,
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

**3. Refresh Token (before expiration)**
```bash
curl -X POST http://localhost:8000/api/guest/refresh-token \
  -H "Authorization: Bearer $GUEST_TOKEN" \
  -H "Content-Type: application/json"

# Response:
{
  "ok": true,
  "message": "Token refreshed successfully",
  "api_token": "new_guest_token_def456...",
  "token_type": "Bearer",
  "expires_at": "2025-01-17T09:00:00Z",
  "expires_in_seconds": 86400
}
```

**4. Use API with Guest Token**
```bash
# After refresh, update token
GUEST_TOKEN="new_guest_token_def456..."

# Now use in any API request
curl -X GET http://localhost:8000/api/products \
  -H "Authorization: Bearer $GUEST_TOKEN"
```

**5. Convert Guest to Regular User**
```bash
curl -X POST http://localhost:8000/api/guest/convert-to-user \
  -H "Authorization: Bearer $GUEST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "mynewemail@example.com",
    "password": "NewPassword123!",
    "password_confirmation": "NewPassword123!"
  }'

# Response:
{
  "ok": true,
  "message": "Guest account converted to premium account",
  "user": {
    "id": 1,
    "name": "guest-2025-01-15-09-am-1",
    "email": "mynewemail@example.com",
    "is_guest": false
  },
  "api_token": "premium_token_ghi789...",
  "note": "Token no longer expires"
}
```

**6. Logout Guest User**
```bash
curl -X POST http://localhost:8000/api/guest/logout \
  -H "Authorization: Bearer $GUEST_TOKEN"

# Response:
{
  "ok": true,
  "message": "Guest logged out successfully. Token revoked."
}
```

### Test Guest Web Interface

**1. Access Login Page**
```
http://localhost:8000/login
```

**2. Click "Login as Guest" Button**
- Automatically creates guest account
- Redirects to `/dashboard`
- Shows token status and expiration countdown

**3. Guest Dashboard Features**
- Token expiration timer
- "Refresh Token" button (extends 24h)
- "Upgrade to Premium" button (convert to regular user)
- Logout button

**4. Access Register Page**
```
http://localhost:8000/register
```
- Has "Continue as Guest" button
- Can create regular account or login as guest

### Test Token Expiration

**Simulate Expired Token**
```bash
# Get a guest token first
GUEST_TOKEN=$(curl -s -X POST http://localhost:8000/api/guest/login \
  -H "Content-Type: application/json" | jq -r '.api_token')

# Wait until token expires (24 hours) OR
# Manually set expiration in database:
sqlite3 database/database.sqlite \
  "UPDATE users SET token_expires_at = datetime('now', '-1 minute') WHERE is_guest = 1;"

# Try to use expired token
curl -X GET http://localhost:8000/api/products \
  -H "Authorization: Bearer $GUEST_TOKEN"

# Response (HTTP 401):
{
  "ok": false,
  "error": "token_expired",
  "message": "Your guest token has expired",
  "refresh_url": "/api/guest/refresh-token",
  "login_url": "/api/guest/login"
}
```

### Guest Username Format

Guest usernames follow this format:
```
guest-{YYYY-MM-DD}-{HH}-{am/pm}-{increment}

Examples:
- guest-2025-01-15-09-am-1   (1st guest at 09:00 AM)
- guest-2025-01-15-09-am-2   (2nd guest at 09:00 AM)
- guest-2025-01-15-02-pm-1   (1st guest at 02:00 PM)
```

Each guest gets unique email: `{username}@guest.local`

### Testing with Multiple Guest Accounts

```bash
# First guest login
curl -s -X POST http://localhost:8000/api/guest/login \
  -H "Content-Type: application/json" | jq '.user.name'
# Output: guest-2025-01-15-09-am-1

# Second guest login (same second)
curl -s -X POST http://localhost:8000/api/guest/login \
  -H "Content-Type: application/json" | jq '.user.name'
# Output: guest-2025-01-15-09-am-2

# Each gets unique account with own token
```

## Database Migrations

### View Migration Status
```bash
php artisan migrate:status
```

### Create New Migration
```bash
php artisan make:migration create_jobs_table
```

### Rollback Last Batch
```bash
php artisan migrate:rollback
```

### Fresh Migrate (Resets DB)
```bash
php artisan migrate:fresh
```

### Refresh (Rollback & Migrate)
```bash
php artisan migrate:refresh
```

## User Management

### Register via Artisan Tinker
```bash
php artisan tinker

# Inside Tinker:
$user = \App\Models\User::create([
    'name' => 'John Doe',
    'email' => 'john@example.com',
    'password' => bcrypt('password123')
]);

# Generate token
$token = Str::random(80);
$user->update(['api_token' => hash('sha256', $token)]);
echo "Token: $token";
```

### View Users in Database
```bash
php artisan tinker
\App\Models\User::all();
```

### Reset API Token
```bash
php artisan tinker
$user = \App\Models\User::find(1);
$token = Str::random(80);
$user->update(['api_token' => hash('sha256', $token)]);
echo "New token: $token";
```

## Logging & Debugging

### View Logs
```bash
# Real-time log monitoring
tail -f storage/logs/laravel.log

# Last 50 lines
tail -50 storage/logs/laravel.log

# Search for errors
grep ERROR storage/logs/laravel.log
```

### Enable Debug Mode
```dotenv
APP_DEBUG=true
```

### Check Database Queries
```bash
php artisan tinker
DB::listen(function($query) {
    echo $query->sql . "\n";
});

\App\Models\Product::where('user_id', 1)->get();
```

## Performance Optimization

### Clear Caches
```bash
# Clear all caches
php artisan cache:clear

# Clear config cache
php artisan config:clear

# Clear route cache
php artisan route:clear

# Optimize autoloader
composer dump-autoload
```

### Database Optimization
```bash
# Create indexes for frequently queried columns
php artisan make:migration add_indexes_to_products_table

# Inside migration:
Schema::table('products', function (Blueprint $table) {
    $table->index('user_id');
    $table->index('product_key');
});
```

## Integration with Flask

### Flask Backend Communication

The `FlaskService` class handles all HTTP communication with Flask:

```php
// In controller
private FlaskService $flaskService;

public function __construct(FlaskService $flaskService)
{
    $this->flaskService = $flaskService;
}

// Methods available
$this->flaskService->analyzeFullUrl($productUrl);
$this->flaskService->scrapeProduct($productUrl);
$this->flaskService->analyzeProduct($productId);
$this->flaskService->reanalyzeProduct($productId);
$this->flaskService->getProductStats($productId);
$this->flaskService->getComments($productId, $page, $perPage);
$this->flaskService->getProductHistory();
$this->flaskService->getJobStatus($jobId);
```

### Flask URL Configuration

Update `.env`:
```dotenv
FLASK_API_URL=http://localhost:5000
```

Or set in `config/services.php`:
```php
'flask' => [
    'url' => env('FLASK_API_URL', 'http://localhost:5000'),
],
```

## Troubleshooting

### Issue: "SQLSTATE[HY000] [2002] No such file or directory"

**Solution:** Set absolute path to SQLite database:
```dotenv
DB_DATABASE=/full/path/to/database/database.sqlite
```

Or use absolute path in `.env`:
```bash
DB_DATABASE=/home/iman874/Documents/GitHub/Mobile-App-CommentTrust/backend/app-backend-laravel/database/database.sqlite
```

### Issue: "Class not found" when accessing controllers

**Solution:** Clear and regenerate autoloader:
```bash
composer dump-autoload -o
php artisan cache:clear
```

### Issue: "Unauthorized" error on protected routes

**Check:**
1. Token is included in Authorization header: `Bearer {token}`
2. Token hasn't been revoked
3. Token belongs to requesting user
4. Token is hashed correctly in database

**Debug:**
```bash
php artisan tinker
$user = \App\Models\User::find(1);
echo "Token hash: " . $user->api_token;

# Verify token
$plainToken = "your-token-here";
hash('sha256', $plainToken) === $user->api_token; // Should be true
```

### Issue: Flask backend connection timeout

**Check:**
1. Flask is running: `curl http://localhost:5000/api/ping`
2. `FLASK_API_URL` is correct in `.env`
3. Network connectivity: `ping localhost`
4. Firewall rules allow port 5000

**Increase timeout:**
In `FlaskService.php`, adjust timeout:
```php
private int $timeout = 300; // 5 minutes
```

### Issue: Database migration fails

**Solution:**
```bash
# Drop all tables and fresh start
php artisan migrate:fresh

# Or specific table
php artisan migrate:rollback --step=1

# Check migration status
php artisan migrate:status
```

## Security Best Practices

1. **API Tokens**
   - Store tokens securely on client (encrypted)
   - Regenerate tokens periodically
   - Revoke token before logout

2. **CORS Configuration**
   - Update `config/cors.php` for production domains:
   ```php
   'allowed_origins' => ['https://yourdomain.com'],
   ```

3. **HTTPS Only**
   - Force HTTPS in production:
   ```php
   // In AppServiceProvider
   if (env('APP_ENV') === 'production') {
       URL::forceScheme('https');
   }
   ```

4. **Environment Variables**
   - Never commit `.env` to repository
   - Use `.env.example` as template
   - Keep secrets in `.env` only

## Deployment

### Production Environment

```dotenv
APP_ENV=production
APP_DEBUG=false
APP_KEY=base64:...
APP_URL=https://yourdomain.com

DB_CONNECTION=mysql
DB_HOST=database.example.com
DB_DATABASE=comment_trust
DB_USERNAME=user
DB_PASSWORD=secure_password

FLASK_API_URL=https://flask-api.yourdomain.com
```

### Pre-deployment Checklist

- [ ] Run `composer install --no-dev`
- [ ] Run `php artisan migrate --force`
- [ ] Clear caches: `php artisan cache:clear`
- [ ] Generate key: `php artisan key:generate`
- [ ] Set file permissions: `chmod -R 775 storage bootstrap/cache`
- [ ] Test all API endpoints
- [ ] Verify Flask backend connection
- [ ] Set up monitoring/logging

## Support

For issues or questions:
1. Check logs: `storage/logs/laravel.log`
2. Read API_DOCUMENTATION.md
3. Check Flask backend status
4. Review .env configuration
5. Run migrations fresh if needed

---

Last Updated: 2025-01-01
Version: 1.0.0
