# Flutter Integration Guide - CommentTrust Guest Login

This guide explains how to integrate the CommentTrust guest login system with your Flutter mobile/web app.

## Overview

The guest login system allows users to:
- Login instantly without registration
- Access features for 24 hours
- Refresh token before expiration
- Convert to permanent account anytime

## Setup

### 1. Add HTTP Client to pubspec.yaml

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  shared_preferences: ^2.2.0
  intl: ^0.18.0
```

Run `flutter pub get`

### 2. Create API Service

Create `lib/services/api_service.dart`:

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';
  static const String tokenKey = 'api_token';
  static const String userKey = 'user_data';
  static const String expiresAtKey = 'token_expires_at';

  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(tokenKey);
  }

  static Future<void> _saveToken(String token, DateTime expiresAt) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(tokenKey, token);
    await prefs.setString(expiresAtKey, expiresAt.toIso8601String());
  }

  static Future<void> _clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(tokenKey);
    await prefs.remove(userKey);
    await prefs.remove(expiresAtKey);
  }

  static Future<Map<String, dynamic>> loginAsGuest() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/guest/login'),
        headers: {'Content-Type': 'application/json'},
      );

      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        if (data['ok']) {
          // Save token and user info
          await _saveToken(
            data['api_token'],
            DateTime.parse(data['expires_at']),
          );
          
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(userKey, jsonEncode(data['user']));
          
          return {
            'success': true,
            'user': data['user'],
            'api_token': data['api_token'],
            'expires_at': data['expires_at'],
          };
        }
      }
      
      return {
        'success': false,
        'error': 'Failed to login as guest',
      };
    } catch (e) {
      return {
        'success': false,
        'error': e.toString(),
      };
    }
  }

  static Future<Map<String, dynamic>> checkTokenStatus() async {
    try {
      final token = await _getToken();
      if (token == null) {
        return {'success': false, 'error': 'No token found'};
      }

      final response = await http.get(
        Uri.parse('$baseUrl/guest/token-status'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return {
          'success': true,
          'is_valid': data['token_status']['is_valid'],
          'is_expired': data['token_status']['is_expired'],
          'expires_at': data['token_status']['expires_at'],
          'expires_in_seconds': data['token_status']['expires_in_seconds'],
        };
      } else if (response.statusCode == 401) {
        // Token expired
        final data = jsonDecode(response.body);
        if (data['error'] == 'token_expired') {
          return {
            'success': false,
            'error': 'token_expired',
            'message': data['message'],
          };
        }
      }

      return {'success': false, 'error': 'Failed to check token status'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<Map<String, dynamic>> refreshGuestToken() async {
    try {
      final token = await _getToken();
      if (token == null) {
        return {'success': false, 'error': 'No token found'};
      }

      final response = await http.post(
        Uri.parse('$baseUrl/guest/refresh-token'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['ok']) {
          // Save new token
          await _saveToken(
            data['api_token'],
            DateTime.parse(data['expires_at']),
          );
          
          return {
            'success': true,
            'api_token': data['api_token'],
            'expires_at': data['expires_at'],
            'expires_in_seconds': data['expires_in_seconds'],
          };
        }
      }

      return {'success': false, 'error': 'Failed to refresh token'};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<Map<String, dynamic>> convertToRegularUser({
    required String email,
    required String password,
    required String passwordConfirmation,
  }) async {
    try {
      final token = await _getToken();
      if (token == null) {
        return {'success': false, 'error': 'No token found'};
      }

      final response = await http.post(
        Uri.parse('$baseUrl/guest/convert-to-user'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'email': email,
          'password': password,
          'password_confirmation': passwordConfirmation,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['ok']) {
          // Update token for new permanent user
          await _saveToken(data['api_token'], DateTime(2099)); // No expiration
          
          return {
            'success': true,
            'user': data['user'],
            'message': data['message'],
          };
        }
      }

      final errorData = jsonDecode(response.body);
      return {
        'success': false,
        'error': errorData['message'] ?? 'Failed to convert account',
      };
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  static Future<void> logout() async {
    try {
      final token = await _getToken();
      if (token != null) {
        await http.post(
          Uri.parse('$baseUrl/guest/logout'),
          headers: {
            'Authorization': 'Bearer $token',
            'Content-Type': 'application/json',
          },
        );
      }
    } catch (e) {
      print('Logout error: $e');
    } finally {
      await _clearToken();
    }
  }

  static Future<Map<String, dynamic>?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final userData = prefs.getString(userKey);
    if (userData != null) {
      return jsonDecode(userData);
    }
    return null;
  }

  static Future<bool> isTokenExpiringSoon({int minutesBefore = 60}) async {
    final prefs = await SharedPreferences.getInstance();
    final expiresAtStr = prefs.getString(expiresAtKey);
    if (expiresAtStr == null) return false;

    final expiresAt = DateTime.parse(expiresAtStr);
    final now = DateTime.now();
    final secondsRemaining = expiresAt.difference(now).inSeconds;

    return secondsRemaining < (minutesBefore * 60);
  }

  static Future<int> getTokenExpiresInSeconds() async {
    final prefs = await SharedPreferences.getInstance();
    final expiresAtStr = prefs.getString(expiresAtKey);
    if (expiresAtStr == null) return 0;

    final expiresAt = DateTime.parse(expiresAtStr);
    final now = DateTime.now();
    final secondsRemaining = expiresAt.difference(now).inSeconds;

    return max(0, secondsRemaining);
  }

  static Future<Map<String, dynamic>> apiRequest({
    required String method,
    required String endpoint,
    Map<String, dynamic>? body,
  }) async {
    try {
      final token = await _getToken();
      
      // Check if token is expired
      final tokenStatus = await checkTokenStatus();
      if (tokenStatus['error'] == 'token_expired') {
        return {
          'success': false,
          'error': 'token_expired',
          'message': 'Please refresh your token or login again',
        };
      }

      final headers = {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };

      late http.Response response;
      final url = Uri.parse('$baseUrl$endpoint');

      if (method == 'GET') {
        response = await http.get(url, headers: headers);
      } else if (method == 'POST') {
        response = await http.post(
          url,
          headers: headers,
          body: body != null ? jsonEncode(body) : null,
        );
      } else if (method == 'PUT') {
        response = await http.put(
          url,
          headers: headers,
          body: body != null ? jsonEncode(body) : null,
        );
      } else if (method == 'DELETE') {
        response = await http.delete(url, headers: headers);
      }

      if (response.statusCode >= 200 && response.statusCode < 300) {
        return {
          'success': true,
          'data': jsonDecode(response.body),
        };
      }

      return {
        'success': false,
        'error': 'HTTP ${response.statusCode}',
        'message': jsonDecode(response.body)['message'] ?? 'Request failed',
      };
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }
}

import 'dart:math';
```

### 3. Create Login Screen

Create `lib/screens/guest_login_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:comment_trust_app/services/api_service.dart';

class GuestLoginScreen extends StatefulWidget {
  @override
  State<GuestLoginScreen> createState() => _GuestLoginScreenState();
}

class _GuestLoginScreenState extends State<GuestLoginScreen> {
  bool isLoading = false;

  void loginAsGuest() async {
    setState(() => isLoading = true);

    final result = await ApiService.loginAsGuest();

    if (result['success']) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Welcome, ${result['user']['name']}!'),
          backgroundColor: Colors.green,
        ),
      );
      Navigator.of(context).pushReplacementNamed('/dashboard');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Login failed: ${result['error']}'),
          backgroundColor: Colors.red,
        ),
      );
    }

    setState(() => isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('CommentTrust')),
      body: Center(
        child: Padding(
          padding: EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.security, size: 80, color: Colors.indigo),
              SizedBox(height: 24),
              Text(
                'Analyze Product Reviews',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              SizedBox(height: 48),
              ElevatedButton.icon(
                onPressed: isLoading ? null : loginAsGuest,
                icon: Icon(Icons.rocket),
                label: Text('Login as Guest'),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 48, vertical: 16),
                  backgroundColor: Colors.green,
                ),
              ),
              SizedBox(height: 16),
              Text(
                'No account needed\nValid for 24 hours',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

### 4. Create Dashboard Screen

Create `lib/screens/dashboard_screen.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:comment_trust_app/services/api_service.dart';

class DashboardScreen extends StatefulWidget {
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  late Future<Map<String, dynamic>> tokenStatusFuture;
  late Future<Map<String, dynamic>?> userFuture;

  @override
  void initState() {
    super.initState();
    tokenStatusFuture = ApiService.checkTokenStatus();
    userFuture = ApiService.getCurrentUser();
  }

  void refreshToken() async {
    final result = await ApiService.refreshGuestToken();
    
    setState(() {
      tokenStatusFuture = ApiService.checkTokenStatus();
    });

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(result['success'] 
          ? 'Token refreshed! Valid for 24 more hours.'
          : 'Failed to refresh token'),
        backgroundColor: result['success'] ? Colors.green : Colors.red,
      ),
    );
  }

  void logout() async {
    await ApiService.logout();
    Navigator.of(context).pushReplacementNamed('/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Dashboard'),
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: logout,
          ),
        ],
      ),
      body: FutureBuilder(
        future: Future.wait([tokenStatusFuture, userFuture]),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return Center(child: Text('Error: ${snapshot.error}'));
          }

          final tokenStatus = snapshot.data?[0] as Map<String, dynamic>?;
          final user = snapshot.data?[1] as Map<String, dynamic>?;

          return SingleChildScrollView(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // User Card
                Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('User', style: Theme.of(context).textTheme.labelSmall),
                        Text(user?['name'] ?? 'Unknown', 
                          style: Theme.of(context).textTheme.headlineSmall),
                        if (user?['is_guest'] == true)
                          Chip(label: Text('Guest User'))
                      ],
                    ),
                  ),
                ),
                SizedBox(height: 16),
                
                // Token Status Card (if guest)
                if (tokenStatus != null && tokenStatus['success'])
                  Card(
                    color: Colors.green[50],
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text('Token Status', 
                            style: Theme.of(context).textTheme.labelSmall),
                          SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Expires In'),
                                  Text(
                                    '${tokenStatus['expires_in_seconds'] ~/ 3600}h ${(tokenStatus['expires_in_seconds'] % 3600) ~/ 60}m',
                                    style: Theme.of(context).textTheme.headlineSmall,
                                  ),
                                ],
                              ),
                              ElevatedButton(
                                onPressed: refreshToken,
                                child: Text('Refresh'),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}
```

### 5. Update main.dart

```dart
import 'package:flutter/material.dart';
import 'package:comment_trust_app/screens/guest_login_screen.dart';
import 'package:comment_trust_app/screens/dashboard_screen.dart';
import 'package:comment_trust_app/services/api_service.dart';

void main() {
  runApp(CommentTrustApp());
}

class CommentTrustApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CommentTrust',
      theme: ThemeData(primarySwatch: Colors.indigo),
      home: AuthGate(),
      routes: {
        '/login': (_) => GuestLoginScreen(),
        '/dashboard': (_) => DashboardScreen(),
      },
    );
  }
}

class AuthGate extends StatefulWidget {
  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  late Future<bool> isLoggedInFuture;

  @override
  void initState() {
    super.initState();
    isLoggedInFuture = _checkLogin();
  }

  Future<bool> _checkLogin() async {
    final user = await ApiService.getCurrentUser();
    return user != null;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: isLoggedInFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        if (snapshot.data == true) {
          return DashboardScreen();
        }

        return GuestLoginScreen();
      },
    );
  }
}
```

## API Token Expiration Handling

When a guest token expires (24 hours), the API will return a 401 error:

```dart
// In your API request handler:
if (response.statusCode == 401) {
  final data = jsonDecode(response.body);
  if (data['error'] == 'token_expired') {
    // Show refresh token screen or auto-refresh
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Token Expired'),
        content: Text('Your session has expired. Refresh to continue.'),
        actions: [
          TextButton(
            onPressed: () {
              ApiService.refreshGuestToken().then((_) {
                Navigator.pop(context);
                // Retry the request
              });
            },
            child: Text('Refresh'),
          ),
          TextButton(
            onPressed: () {
              ApiService.logout().then((_) {
                Navigator.pushNamedAndRemoveUntil(context, '/login', (_) => false);
              });
            },
            child: Text('Login Again'),
          ),
        ],
      ),
    );
  }
}
```

## Convert to Regular Account

```dart
void convertToRegularUser() async {
  final result = await ApiService.convertToRegularUser(
    email: 'newmail@example.com',
    password: 'SecurePassword123!',
    passwordConfirmation: 'SecurePassword123!',
  );

  if (result['success']) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Account upgraded! No more token expiration.'),
        backgroundColor: Colors.green,
      ),
    );
    // Reload dashboard
    setState(() {});
  }
}
```

## Token Status Display

Display token expiration warning when less than 6 hours remain:

```dart
FutureBuilder(
  future: ApiService.isTokenExpiringSoon(minutesBefore: 360),
  builder: (context, snapshot) {
    if (snapshot.data == true) {
      return Container(
        color: Colors.orange,
        padding: EdgeInsets.all(8),
        child: Row(
          children: [
            Icon(Icons.warning, color: Colors.white),
            SizedBox(width: 8),
            Text('Token expiring soon. Refresh to extend.', 
              style: TextStyle(color: Colors.white)),
          ],
        ),
      );
    }
    return SizedBox.shrink();
  },
)
```

## Best Practices

1. **Auto-refresh tokens** before expiration (set reminder at 6 hours)
2. **Store tokens securely** in SharedPreferences (consider encrypted storage)
3. **Handle 401 responses** gracefully with refresh or re-login prompts
4. **Check token status** on app resume
5. **Cache user data** locally to reduce API calls
6. **Show expiration countdown** to encourage conversion to regular accounts

## Testing

```bash
# Test guest login
curl -X POST http://localhost:8000/api/guest/login \
  -H "Content-Type: application/json"

# Check token status (replace TOKEN)
curl -X GET http://localhost:8000/api/guest/token-status \
  -H "Authorization: Bearer TOKEN"

# Refresh token
curl -X POST http://localhost:8000/api/guest/refresh-token \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json"
```

## Troubleshooting

**"No token found" error:**
- User hasn't logged in yet or token was cleared
- Clear SharedPreferences and login again

**"Token expired" on first request:**
- Clock on device/server is misaligned
- Check system time on both client and server

**Convert to user fails:**
- Email already registered under another account
- Choose a different email address

