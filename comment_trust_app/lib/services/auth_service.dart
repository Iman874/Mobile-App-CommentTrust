import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthService {
  static const _tokenKey = 'auth.token';
  static const _nameKey = 'auth.name';
  static const _expiresKey = 'auth.expires_at';
  static const _isGuestKey = 'auth.is_guest';

  /// Attempt a guest login. On success stores token and guest info and returns true.
  static Future<bool> guestLogin(String baseUrl) async {
    try {
      final uri = Uri.parse('$baseUrl/api/guest/login');
      final res = await http.post(uri, headers: {'Content-Type': 'application/json'}).timeout(const Duration(seconds: 10));
      if (res.statusCode != 200 && res.statusCode != 201) return false;
      final body = json.decode(res.body) as Map<String, dynamic>;
      final token = body['api_token'] as String? ?? body['token'] as String?;
      final name = (body['name'] ?? body['user_name'] ?? '') as String;
      final expiresIn = body['expires_in_seconds'] as int?;
      final isGuest = (body['is_guest'] ?? true) as bool;
      if (token == null || token.isEmpty) return false;
      await _saveToken(token, name, expiresIn, isGuest);
      return true;
    } catch (_) {
      return false;
    }
  }

  static Future<void> logout() async {
    final sp = await SharedPreferences.getInstance();
    await sp.remove(_tokenKey);
    await sp.remove(_nameKey);
    await sp.remove(_expiresKey);
    await sp.remove(_isGuestKey);
  }

  /// Refresh guest token (extends expiry). Returns true when refreshed.
  static Future<bool> refreshGuestToken(String baseUrl) async {
    try {
      final token = await AuthService.token;
      if (token == null) return false;
      final uri = Uri.parse('$baseUrl/api/guest/refresh-token');
      final res = await http.post(uri, headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'}).timeout(const Duration(seconds: 10));
      if (res.statusCode != 200) return false;
      final body = json.decode(res.body) as Map<String, dynamic>;
      final newToken = body['api_token'] as String? ?? body['api_token'] as String?;
      final expiresIn = body['expires_in_seconds'] as int?;
      if (newToken == null) return false;
      await _saveToken(newToken, body['name'] ?? '', expiresIn, body['is_guest'] ?? true);
      return true;
    } catch (_) {
      return false;
    }
  }

  static Future<void> _saveToken(String token, String name, int? expiresInSeconds, bool isGuest) async {
    final sp = await SharedPreferences.getInstance();
    await sp.setString(_tokenKey, token);
    if (name.isNotEmpty) await sp.setString(_nameKey, name);
    if (expiresInSeconds != null) {
      final expiresAt = DateTime.now().add(Duration(seconds: expiresInSeconds)).toIso8601String();
      await sp.setString(_expiresKey, expiresAt);
    }
    await sp.setBool(_isGuestKey, isGuest);
  }

  static Future<String?> get token async {
    final sp = await SharedPreferences.getInstance();
    return sp.getString(_tokenKey);
  }

  static Future<bool> get isGuest async {
    final sp = await SharedPreferences.getInstance();
    return sp.getBool(_isGuestKey) ?? false;
  }

  static Future<String?> get name async {
    final sp = await SharedPreferences.getInstance();
    return sp.getString(_nameKey);
  }

  static Future<bool> get tokenExpired async {
    final sp = await SharedPreferences.getInstance();
    final s = sp.getString(_expiresKey);
    if (s == null) return true;
    try {
      final dt = DateTime.parse(s);
      return DateTime.now().isAfter(dt);
    } catch (_) {
      return true;
    }
  }
}
