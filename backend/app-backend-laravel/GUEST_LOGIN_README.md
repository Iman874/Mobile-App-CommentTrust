# CommentTrust Guest Login System

Complete guide to the guest login system in CommentTrust. This system allows users to instantly access the platform without registration.

## Overview

**What is Guest Login?**
- Instant login without registration
- Auto-generated account with unique username
- API token valid for exactly 24 hours
- Token can be refreshed to extend access
- Can be converted to permanent account anytime

**Why Guest Login?**
- Lower friction for new users
- Try before registration
- Temporary access for analysis
- Easy path to conversion

## System Architecture

### Database Schema

```sql
users table:
- id (primary key)
- name (string, unique)
- email (string, unique)
- password (string, hashed)
- api_token (string, hashed)
- api_token_name (string)
- is_guest (boolean, default: false)
- token_expires_at (timestamp, nullable)
- is_active (boolean, default: true)
- created_at, updated_at

Migration: 2025_12_11_000004_add_guest_fields_to_users_table.php
```

### Token Lifecycle

```
Timeline:
[0h]        User logs in as guest
            → Unique account created
            → Token generated
            → token_expires_at = now() + 24h

[12h]       User still active
            → Token still valid
            → Can make API requests

[24h]       Token expires automatically
            → API returns 401 error
            → User must refresh or re-login

[24h+]      User clicks "Refresh Token"
            → New token generated
            → token_expires_at = now() + 24h
            → Another 24 hours of access

[∞]         User converts to regular account
            → is_guest set to false
            → token_expires_at set to null
            → Token never expires
```

### Middleware Stack

```
Request Flow:
    ↓
ValidateApiToken Middleware
├─ Extract Bearer token from header
├─ Hash token with SHA256
├─ Compare with database hash
└─ Reject if not found

    ↓
CheckTokenExpiration Middleware
├─ Check token_expires_at column
├─ Return 401 if expired
└─ Allow if valid

    ↓
Controller Method
└─ Process authenticated request
```

## API Endpoints

### Public Endpoints (No Authentication)

**POST /api/guest/login**
- Auto-create guest account
- Return API token
- Token valid 24 hours

### Protected Endpoints (Bearer Token Required)

**GET /api/guest/token-status**
- Check token validity
- Return expiration info

**POST /api/guest/refresh-token**
- Generate new token
- Extend access 24 more hours

**POST /api/guest/convert-to-user**
- Convert to permanent account
- Set password
- Token expires_at → null (never expires)

**POST /api/guest/logout**
- Revoke token
- Clear api_token field

## Web Interface Routes

### Public Routes (No Authentication)

```
GET  /login               → Show login form
GET  /register            → Show registration form
POST /login               → Login with email/password
POST /register            → Create new account
POST /guest-login         → Create guest account (from web)
```

### Protected Routes (Auth Middleware)

```
GET  /dashboard           → User dashboard with token status
GET  /profile             → Edit user profile
PUT  /profile/update      → Update profile details
POST /logout              → Logout and revoke token

GET  /convert-to-user     → Show conversion form (guest only)
POST /convert-to-user     → Convert guest to regular user
POST /api/guest/refresh-token → Web endpoint for token refresh
```

## Controllers

### GuestAuthController (API)

**Purpose:** Handle guest authentication via API

**Key Methods:**
```php
loginAsGuest()           // POST /api/guest/login
refreshGuestToken()      // POST /api/guest/refresh-token
checkTokenStatus()       // GET /api/guest/token-status
convertToRegularUser()   // POST /api/guest/convert-to-user
logoutGuest()            // POST /api/guest/logout
```

### GuestWebController (Web UI)

**Purpose:** Handle guest login via web forms

**Key Methods:**
```php
showLoginForm()          // GET /login
showRegisterForm()       // GET /register
login()                  // POST /login
register()               // POST /register
guestLogin()             // POST /guest-login (auto-creates guest)
```

### DashboardController (Web UI)

**Purpose:** Show dashboard and manage profile

**Key Methods:**
```php
index()                  // GET /dashboard (show token status)
showProfile()            // GET /profile
updateProfile()          // PUT /profile/update
logout()                 // POST /logout
showConvertForm()        // GET /convert-to-user
convertToUser()          // POST /convert-to-user
deleteProfile()          // DELETE /profile/delete
refreshGuestToken()      // POST /api/guest/refresh-token
```

## Blade Templates

### Layout Hierarchy

```
resources/views/layouts/app.blade.php
├─ Navigation bar (if authenticated)
├─ Flash messages
├─ @yield('content')
└─ Footer

Extends:
├─ guest/login.blade.php
├─ guest/register.blade.php
├─ guest/dashboard.blade.php
├─ guest/profile.blade.php
└─ guest/convert.blade.php
```

### Key Features per Template

**login.blade.php**
- Email/password login form
- "Login as Guest" button
- Link to register page

**register.blade.php**
- Name/email/password registration
- "Continue as Guest" button
- Link to login page

**dashboard.blade.php**
- User profile card
- Guest token status (if guest):
  - Expiration countdown
  - Progress bar
  - "Refresh Token" button
  - "Upgrade to Premium" button
- Statistics (products, comments)
- Products list
- API token display (dev only)

**profile.blade.php**
- Edit name, email
- Change password
- Guest-specific actions (if guest)
- "Delete Account" button

**convert.blade.php**
- Benefits comparison (guest vs premium)
- Current token status
- Email and password setup form
- Terms checkbox

## Guest Username Generation

### Format
```
guest-{YYYY-MM-DD}-{HH}-{am/pm}-{increment}

Components:
- YYYY-MM-DD    : Date of login (2025-01-15)
- HH            : Hour (01-12)
- am/pm         : Morning or afternoon
- increment     : Counter for same hour
```

### Examples
```
guest-2025-01-15-09-am-1     First guest at 09:00 AM on Jan 15
guest-2025-01-15-09-am-2     Second guest at 09:00 AM on Jan 15
guest-2025-01-15-02-pm-1     First guest at 02:00 PM on Jan 15
guest-2025-01-15-12-am-1     First guest at 12:00 AM (midnight)
guest-2025-01-16-01-am-1     First guest at 01:00 AM on Jan 16
```

### Implementation
```php
// In GuestAuthController and GuestWebController
$now = Carbon::now();
$date = $now->format('Y-m-d');           // 2025-01-15
$time = $now->format('h');               // 09
$period = $now->format('a');             // am/pm

$baseUsername = "guest-{$date}-{$time}-{$period}";
$existingCount = User::where('name', 'like', "{$baseUsername}-%")
    ->count();
$increment = $existingCount + 1;
$guestUsername = "{$baseUsername}-{$increment}";
```

## Token Management

### Token Generation

```php
// In User model
public function generateApiToken(?string $tokenName = null, bool $isGuest = false)
{
    $plainToken = Str::random(80);
    $hashedToken = hash('sha256', $plainToken);
    
    $this->api_token = $hashedToken;
    $this->api_token_name = $tokenName ?? 'default';
    
    if ($isGuest) {
        $this->token_expires_at = now()->addDay();  // 24 hours
    } else {
        $this->token_expires_at = null;  // Never expires
    }
    
    $this->save();
    
    return $plainToken;  // Return plaintext only once
}
```

### Token Validation

```php
// In ValidateApiToken middleware
$incomingToken = $request->bearerToken();
$hashedIncoming = hash('sha256', $incomingToken);
$user = User::where('api_token', $hashedIncoming)->first();

if (!$user) {
    return $this->unauthorized('Invalid token');
}
```

### Token Expiration Check

```php
// In CheckTokenExpiration middleware
if ($user->isTokenExpired()) {
    return response()->json([
        'ok' => false,
        'error' => 'token_expired',
        'message' => 'Token expired',
        'refresh_url' => '/api/guest/refresh-token'
    ], 401);
}

// In User model
public function isTokenExpired(): bool
{
    if ($this->token_expires_at === null) {
        return false;  // No expiration for regular users
    }
    return $this->token_expires_at < now();
}
```

## Session Management

### Web Session Cache

When user logs in via web interface, session stores:

```php
session([
    'login_type' => 'guest',           // or 'regular'
    'logged_in_at' => now(),           // Login timestamp
    'api_token' => $token,             // For displays
    'token_expires_at' => $expiresAt,  // For countdowns
]);
```

### Session Retrieval

```php
$loginType = session('login_type');
$token = session('api_token');
$expiresAt = session('token_expires_at');
```

## Error Handling

### 401 Unauthorized - Token Expired

```json
{
  "ok": false,
  "error": "token_expired",
  "message": "Your guest token has expired",
  "refresh_url": "/api/guest/refresh-token",
  "login_url": "/api/guest/login"
}
```

**Client Action:**
1. Show refresh prompt
2. Call refresh endpoint
3. Update token in storage
4. Retry original request

### 401 Unauthorized - Invalid Token

```json
{
  "ok": false,
  "error": "invalid_token",
  "message": "Token not found or invalid"
}
```

**Client Action:**
1. Clear stored token
2. Redirect to login page

### 403 Forbidden - Not Guest User

```json
{
  "ok": false,
  "error": "not_guest_user",
  "message": "This operation is only available for guest users"
}
```

**Scenario:** Regular user trying to refresh or convert

## Testing Checklist

### Guest Login Flow
- [ ] Guest login creates unique account
- [ ] Username follows format: `guest-YYYY-MM-DD-HH-am/pm-increment`
- [ ] Token generated with 24h expiration
- [ ] Email set to `{username}@guest.local`
- [ ] is_guest flag set to true

### Token Management
- [ ] Token valid within 24h window
- [ ] Token rejected after 24h
- [ ] Refresh extends token by 24h
- [ ] Token remains hashed in database

### Web Interface
- [ ] Login page displays guest button
- [ ] Register page shows "Continue as Guest"
- [ ] Dashboard shows token countdown
- [ ] Dashboard shows refresh button (if guest)
- [ ] Dashboard shows upgrade button (if guest)

### API Endpoints
- [ ] POST /api/guest/login works without auth
- [ ] GET /api/guest/token-status requires token
- [ ] POST /api/guest/refresh-token requires token
- [ ] POST /api/guest/convert-to-user requires token
- [ ] POST /api/guest/logout requires token
- [ ] Expired token returns 401 with refresh_url

### Token Expiration
- [ ] Token valid for exactly 24 hours
- [ ] Expired token rejected by middleware
- [ ] Refresh generates new 24h token
- [ ] Regular users never expire

### Guest Conversion
- [ ] Guest can convert to regular user
- [ ] Email can be changed during conversion
- [ ] Password set during conversion
- [ ] is_guest changed to false
- [ ] token_expires_at set to null
- [ ] Token no longer expires

### Logout
- [ ] Logout clears api_token
- [ ] Session invalidated
- [ ] User redirected to login

## Quick Start Commands

### Register and Login (API)

```bash
# 1. Login as guest (creates account)
curl -X POST http://localhost:8000/api/guest/login

# 2. Save token from response
TOKEN="guest_token_..."

# 3. Check token status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/guest/token-status

# 4. Use token for any API request
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/products

# 5. Before expiration, refresh token
curl -X POST http://localhost:8000/api/guest/refresh-token \
  -H "Authorization: Bearer $TOKEN"
```

### Web Interface

```
1. Go to http://localhost:8000/login
2. Click "Login as Guest"
3. See auto-created account in dashboard
4. View token status with countdown
5. Click "Refresh Token" to extend
6. Click "Upgrade to Premium" to convert
```

## Troubleshooting

### "Token Expired" on First Request
- **Cause:** Clock skew between client and server
- **Solution:** Check system time on both machines

### Multiple Guest Accounts
- **Cause:** Guest login called multiple times
- **Expected:** Each creates new account with unique name
- **Verify:** Check username increment

### Cannot Convert Guest Account
- **Cause:** Email already registered
- **Solution:** Use different email address during conversion

### Token Not Stored Locally
- **Cause:** Hashing issue or database save failed
- **Solution:** Check ValidateApiToken error response

### Dashboard Not Showing Token Status
- **Cause:** Session not storing token info
- **Solution:** Check session cache in GuestWebController::guestLogin()

## Security Considerations

### Token Security
- ✓ Tokens hashed with SHA256 before storage
- ✓ Only plaintext token returned to user once
- ✓ Bearer token required in Authorization header
- ✓ Token expiration enforced by middleware

### Guest Account Security
- ✓ No password stored (random 32-char password generated)
- ✓ Converted to regular account when password set
- ✓ Token revoked on logout
- ✓ Email set to unique @guest.local domain

### CSRF Protection
- ✓ Blade forms use @csrf token
- ✓ Session middleware validates tokens
- ✓ API endpoints use Bearer tokens

### Recommendations
1. Implement rate limiting on /api/guest/login
2. Monitor for mass guest account creation
3. Auto-cleanup expired guest accounts (optional)
4. Consider requiring email for guest conversion

## Performance Optimization

### Database Indexes
```sql
-- Add for faster lookups
CREATE INDEX idx_guests ON users(is_guest, token_expires_at);
CREATE INDEX idx_tokens ON users(api_token);
```

### Caching
```php
// Cache guest username increment to reduce queries
Cache::remember("guest_count_{$baseUsername}", 3600, function () {
    return User::where('name', 'like', "{$baseUsername}-%")->count();
});
```

### Background Jobs (Optional)
```php
// Clean up expired guest accounts daily
php artisan schedule:run
// Runs: DeleteExpiredGuestAccounts::dispatch()
```

## Next Steps

1. **Test Locally**
   - Run migrations
   - Test API endpoints with cURL
   - Test web interface in browser
   - Check database records

2. **Deploy to Staging**
   - Setup environment
   - Run migrations
   - Test in staging environment
   - Verify token expiration

3. **Integrate with Flutter**
   - Use ApiService class from FLUTTER_INTEGRATION.md
   - Implement token refresh logic
   - Handle 401 responses

4. **Monitor Production**
   - Track guest login success rate
   - Monitor token refresh frequency
   - Watch conversion rate
   - Analyze average session duration

## References

- **API Documentation:** `API_DOCUMENTATION.md` (section 1.5)
- **Setup Guide:** `SETUP_GUIDE.md` (guest testing section)
- **Flutter Integration:** `FLUTTER_INTEGRATION.md`
- **Database Schema:** Migration `2025_12_11_000004`
- **Controllers:** `app/Http/Controllers/{GuestAuthController,GuestWebController,DashboardController}.php`
- **Middleware:** `app/Http/Middleware/{ValidateApiToken,CheckTokenExpiration}.php`
- **Templates:** `resources/views/guest/*.blade.php`

