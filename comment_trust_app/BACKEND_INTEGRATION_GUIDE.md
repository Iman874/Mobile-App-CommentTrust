# Flutter Mobile App - Backend Integration Guide

## Overview

Flutter app akan berkomunikasi dengan Laravel API menggunakan HTTP client. Backend menangani authentication, product management, dan comment analysis.

**Backend URL:** `http://localhost:8000/api` (development)

## Setup

### 1. Add Dependencies

Update `pubspec.yaml`:

```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  shared_preferences: ^2.2.0
  intl: ^0.19.0
```

Run:
```bash
flutter pub get
```

### 2. Create API Service Class

Create `lib/services/api_service.dart`:

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';
  late SharedPreferences _prefs;
  String? _apiToken;

  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    _apiToken = _prefs.getString('api_token');
  }

  // ========================================================================
  // Authentication
  // ========================================================================

  /// Register new user
  Future<Map<String, dynamic>> register({
    required String name,
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'name': name,
        'email': email,
        'password': password,
        'password_confirmation': password,
      }),
    );

    final data = jsonDecode(response.body);
    if (data['ok'] == true) {
      _apiToken = data['api_token'];
      await _prefs.setString('api_token', _apiToken!);
    }
    return data;
  }

  /// Login with email and password
  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );

    final data = jsonDecode(response.body);
    if (data['ok'] == true) {
      _apiToken = data['api_token'];
      await _prefs.setString('api_token', _apiToken!);
    }
    return data;
  }

  /// Get current user info
  Future<Map<String, dynamic>> getCurrentUser() async {
    return _getRequest('/auth/me');
  }

  /// Logout (revoke token)
  Future<Map<String, dynamic>> logout() async {
    final response = await _postRequest('/auth/logout', {});
    if (response['ok'] == true) {
      _apiToken = null;
      await _prefs.remove('api_token');
    }
    return response;
  }

  /// Update user profile
  Future<Map<String, dynamic>> updateProfile({
    String? name,
    String? email,
    String? currentPassword,
    String? password,
  }) async {
    return _putRequest('/auth/profile/update', {
      if (name != null) 'name': name,
      if (email != null) 'email': email,
      if (currentPassword != null) 'current_password': currentPassword,
      if (password != null) 'password': password,
      if (password != null) 'password_confirmation': password,
    });
  }

  // ========================================================================
  // Products
  // ========================================================================

  /// Get list of products
  Future<Map<String, dynamic>> getProducts({
    int page = 1,
    int perPage = 10,
    String? search,
  }) async {
    return _getRequest('/products', {
      'page': page,
      'per_page': perPage,
      if (search != null) 'search': search,
    });
  }

  /// Start analysis for a product URL
  Future<Map<String, dynamic>> startAnalysis({
    required String productUrl,
  }) async {
    return _postRequest('/products', {
      'product_url': productUrl,
    });
  }

  /// Get product details
  Future<Map<String, dynamic>> getProduct(String id) async {
    return _getRequest('/products/$id', {});
  }

  /// Update product
  Future<Map<String, dynamic>> updateProduct({
    required String id,
    String? name,
    String? notes,
  }) async {
    return _putRequest('/products/$id', {
      if (name != null) 'name': name,
      if (notes != null) 'notes': notes,
    });
  }

  /// Delete product
  Future<Map<String, dynamic>> deleteProduct(String id) async {
    return _deleteRequest('/products/$id');
  }

  /// Get product statistics
  Future<Map<String, dynamic>> getProductStats(String id) async {
    return _getRequest('/products/$id/stats', {});
  }

  /// Get sentiment breakdown for product
  Future<Map<String, dynamic>> getSentimentBreakdown(String id) async {
    return _getRequest('/products/$id/sentiment-breakdown', {});
  }

  /// Get rating distribution for product
  Future<Map<String, dynamic>> getRatingDistribution(String id) async {
    return _getRequest('/products/$id/rating-distribution', {});
  }

  // ========================================================================
  // Comments
  // ========================================================================

  /// Get comments for a product
  Future<Map<String, dynamic>> getComments(
    String productId, {
    int page = 1,
    int perPage = 15,
    String? sentiment,
    List<String>? tags,
    String? search,
    String sortBy = 'newest',
  }) async {
    return _getRequest('/comments/$productId', {
      'page': page,
      'per_page': perPage,
      if (sentiment != null) 'sentiment': sentiment,
      if (tags != null) 'tags': tags.join(','),
      if (search != null) 'search': search,
      'sort_by': sortBy,
    });
  }

  /// Get single comment detail
  Future<Map<String, dynamic>> getComment(
    String productId,
    String commentId,
  ) async {
    return _getRequest('/comments/$productId/detail/$commentId', {});
  }

  /// Advanced comment filtering
  Future<Map<String, dynamic>> filterComments(
    String productId, {
    String? sentiment,
    int? ratingMin,
    int? ratingMax,
    bool? hasTags,
    bool? isFake,
    double? trustScoreMin,
    double? trustScoreMax,
  }) async {
    return _postRequest('/comments/$productId/filter', {
      if (sentiment != null) 'sentiment': sentiment,
      if (ratingMin != null) 'rating_min': ratingMin,
      if (ratingMax != null) 'rating_max': ratingMax,
      if (hasTags != null) 'has_tags': hasTags,
      if (isFake != null) 'is_fake': isFake,
      if (trustScoreMin != null) 'trust_score_min': trustScoreMin,
      if (trustScoreMax != null) 'trust_score_max': trustScoreMax,
    });
  }

  /// Search comments
  Future<Map<String, dynamic>> searchComments(
    String productId, {
    required String query,
  }) async {
    return _getRequest('/comments/$productId/search', {
      'q': query,
    });
  }

  /// Get comment statistics
  Future<Map<String, dynamic>> getCommentStats(String productId) async {
    return _getRequest('/comments/$productId/stats', {});
  }

  // ========================================================================
  // Analysis & Jobs
  // ========================================================================

  /// Start full analysis (scrape + analyze)
  Future<Map<String, dynamic>> startFullAnalysis({
    required String productUrl,
  }) async {
    return _postRequest('/analysis/start', {
      'product_url': productUrl,
    });
  }

  /// Check job status
  Future<Map<String, dynamic>> checkJobStatus(String jobId) async {
    return _getRequest('/analysis/job/$jobId', {});
  }

  /// Get all analyzed products
  Future<Map<String, dynamic>> getAnalyzedProducts() async {
    return _getRequest('/analysis/products', {});
  }

  /// Get product analysis details
  Future<Map<String, dynamic>> getProductAnalysis(String productId) async {
    return _getRequest('/analysis/product/$productId', {});
  }

  /// Scrape only (no analysis)
  Future<Map<String, dynamic>> scrapeOnly({
    required String productUrl,
  }) async {
    return _postRequest('/analysis/scrape', {
      'product_url': productUrl,
    });
  }

  /// Analyze only (from existing data)
  Future<Map<String, dynamic>> analyzeOnly(String productId) async {
    return _postRequest('/analysis/analyze/$productId', {});
  }

  /// Re-analyze product
  Future<Map<String, dynamic>> reanalyzeProduct(String productId) async {
    return _postRequest('/analysis/reanalyze/$productId', {});
  }

  // ========================================================================
  // Helper Methods
  // ========================================================================

  Future<Map<String, dynamic>> _getRequest(
    String endpoint,
    Map<String, dynamic> params,
  ) async {
    final uri = Uri.parse('$baseUrl$endpoint').replace(
      queryParameters: params.cast<String, String>(),
    );

    try {
      final response = await http.get(
        uri,
        headers: _getHeaders(),
      ).timeout(const Duration(seconds: 30));

      return jsonDecode(response.body);
    } catch (e) {
      return {'ok': false, 'message': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> _postRequest(
    String endpoint,
    Map<String, dynamic> body,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl$endpoint'),
        headers: _getHeaders(),
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 30));

      return jsonDecode(response.body);
    } catch (e) {
      return {'ok': false, 'message': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> _putRequest(
    String endpoint,
    Map<String, dynamic> body,
  ) async {
    try {
      final response = await http.put(
        Uri.parse('$baseUrl$endpoint'),
        headers: _getHeaders(),
        body: jsonEncode(body),
      ).timeout(const Duration(seconds: 30));

      return jsonDecode(response.body);
    } catch (e) {
      return {'ok': false, 'message': 'Network error: $e'};
    }
  }

  Future<Map<String, dynamic>> _deleteRequest(String endpoint) async {
    try {
      final response = await http.delete(
        Uri.parse('$baseUrl$endpoint'),
        headers: _getHeaders(),
      ).timeout(const Duration(seconds: 30));

      return jsonDecode(response.body);
    } catch (e) {
      return {'ok': false, 'message': 'Network error: $e'};
    }
  }

  Map<String, String> _getHeaders() {
    return {
      'Content-Type': 'application/json',
      if (_apiToken != null) 'Authorization': 'Bearer $_apiToken',
    };
  }

  bool isAuthenticated() => _apiToken != null;
  String? getToken() => _apiToken;
}
```

### 3. Create Provider/State Management

Create `lib/providers/auth_provider.dart`:

```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  bool _isLoading = false;
  String? _error;
  Map<String, dynamic>? _user;
  bool _isAuthenticated = false;

  bool get isLoading => _isLoading;
  String? get error => _error;
  Map<String, dynamic>? get user => _user;
  bool get isAuthenticated => _isAuthenticated;

  Future<void> init() async {
    await _apiService.init();
    _isAuthenticated = _apiService.isAuthenticated();
    if (_isAuthenticated) {
      await getCurrentUser();
    }
  }

  Future<bool> register({
    required String name,
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.register(
        name: name,
        email: email,
        password: password,
      );

      if (response['ok'] == true) {
        _user = response['user'];
        _isAuthenticated = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = response['message'] ?? 'Registration failed';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<bool> login({
    required String email,
    required String password,
  }) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      final response = await _apiService.login(
        email: email,
        password: password,
      );

      if (response['ok'] == true) {
        _user = response['user'];
        _isAuthenticated = true;
        _isLoading = false;
        notifyListeners();
        return true;
      } else {
        _error = response['message'] ?? 'Login failed';
        _isLoading = false;
        notifyListeners();
        return false;
      }
    } catch (e) {
      _error = 'Error: $e';
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _isLoading = true;
    notifyListeners();

    try {
      await _apiService.logout();
      _user = null;
      _isAuthenticated = false;
      _error = null;
    } catch (e) {
      _error = 'Error: $e';
    }

    _isLoading = false;
    notifyListeners();
  }

  Future<void> getCurrentUser() async {
    try {
      final response = await _apiService.getCurrentUser();
      if (response['ok'] == true) {
        _user = response['user'];
      }
    } catch (e) {
      _error = 'Failed to get user';
    }
    notifyListeners();
  }
}
```

### 4. Update Main App

Update `lib/main.dart`:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/api_service.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize API service
  final apiService = ApiService();
  await apiService.init();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()..init()),
      ],
      child: MaterialApp(
        title: 'CommentTrust',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          useMaterial3: true,
        ),
        home: Consumer<AuthProvider>(
          builder: (context, auth, child) {
            if (auth.isAuthenticated) {
              return const HomeScreen();
            } else {
              return const LoginScreen();
            }
          },
        ),
      ),
    );
  }
}
```

## Usage Examples

### Login Screen

```dart
class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: Consumer<AuthProvider>(
        builder: (context, auth, child) {
          return Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                TextField(
                  controller: _emailController,
                  decoration: const InputDecoration(labelText: 'Email'),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Password'),
                ),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: auth.isLoading
                      ? null
                      : () async {
                          final success = await auth.login(
                            email: _emailController.text,
                            password: _passwordController.text,
                          );
                          if (success && mounted) {
                            Navigator.of(context).pushReplacementNamed('/home');
                          }
                        },
                  child: Text(auth.isLoading ? 'Loading...' : 'Login'),
                ),
                if (auth.error != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 16),
                    child: Text(
                      auth.error!,
                      style: const TextStyle(color: Colors.red),
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

### Products List Screen

```dart
class ProductsScreen extends StatefulWidget {
  const ProductsScreen({Key? key}) : super(key: key);

  @override
  State<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends State<ProductsScreen> {
  late Future<Map<String, dynamic>> _productsFuture;
  final _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _apiService.init();
    _productsFuture = _apiService.getProducts();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Products')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: _productsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (!snapshot.data?['ok'] ?? false) {
            return Center(
              child: Text('Error: ${snapshot.data?['message']}'),
            );
          }

          final products = List<Map<String, dynamic>>.from(
            snapshot.data?['products'] ?? [],
          );

          return ListView.builder(
            itemCount: products.length,
            itemBuilder: (context, index) {
              final product = products[index];
              return ListTile(
                title: Text(product['name']),
                subtitle: Text('Rating: ${product['avg_rating']}'),
                onTap: () {
                  // Navigate to product details
                },
              );
            },
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Show dialog to enter product URL
          _showAnalysisDialog();
        },
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAnalysisDialog() {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Start Analysis'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Product URL',
            hintText: 'https://...',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final response = await _apiService.startAnalysis(
                productUrl: controller.text,
              );
              if (response['ok'] == true) {
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Analysis started')),
                  );
                  Navigator.pop(context);
                  setState(() {
                    _productsFuture = _apiService.getProducts();
                  });
                }
              }
            },
            child: const Text('Start'),
          ),
        ],
      ),
    );
  }
}
```

## Network Configuration

### Update Android (android/app/AndroidManifest.xml)

For development with localhost:

```xml
<manifest ...>
    <uses-permission android:name="android.permission.INTERNET" />
    
    <application ...>
        ...
        <!-- Allow cleartext (HTTP) traffic for localhost -->
        <domain-config cleartextTrafficPermitted="true">
            <domain includeSubdomains="true">localhost</domain>
            <domain includeSubdomains="true">127.0.0.1</domain>
        </domain-config>
    </application>
</manifest>
```

### Update iOS (ios/Runner/Info.plist)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC ...>
<plist version="1.0">
<dict>
    ...
    <key>NSLocalNetworkUsageDescription</key>
    <string>App needs to access local network for development</string>
    <key>NSBonjourServices</key>
    <array>
        <string>_http._tcp</string>
    </array>
    ...
</dict>
</plist>
```

## Error Handling

```dart
Future<void> safeApiCall(
  Future<Map<String, dynamic>> Function() apiCall,
  VoidCallback onSuccess,
) async {
  try {
    final response = await apiCall();
    
    if (response['ok'] == true) {
      onSuccess();
    } else {
      final error = response['message'] ?? 'Unknown error';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error),
          backgroundColor: Colors.red,
        ),
      );
    }
  } catch (e) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Error: $e'),
        backgroundColor: Colors.red,
      ),
    );
  }
}
```

## Best Practices

1. **Token Management**
   - Store token securely with flutter_secure_storage
   - Refresh token before expiration
   - Clear token on logout

2. **Error Handling**
   - Always check `response['ok']` before using data
   - Display user-friendly error messages
   - Log errors for debugging

3. **Network**
   - Implement retry logic for failed requests
   - Use offline caching when possible
   - Show loading indicators

4. **State Management**
   - Use Provider for global state
   - Keep API responses in state
   - Refresh state when needed

5. **UI/UX**
   - Show progress indicators during API calls
   - Disable buttons during loading
   - Provide clear error messages
   - Implement proper navigation flows

---

Generated: 2025-01-01
Last Updated: 2025-01-01
Version: 1.0.0
