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
    // Try known API path first, then fall back to web guest endpoint
    final candidates = [
      Uri.parse('$baseUrl/api/guest/login'),
      Uri.parse('$baseUrl/guest-login'),
    ];

    for (final uri in candidates) {
      try {
        final res = await http.post(uri, headers: {'Content-Type': 'application/json'}).timeout(const Duration(seconds: 10));
        if (res.statusCode == 200 || res.statusCode == 201) {
          final body = json.decode(res.body) as Map<String, dynamic>;
          final token = body['api_token'] as String? ?? body['token'] as String?;
          final name = ((body['user']?['name']) ?? body['name'] ?? body['user_name'] ?? '') as String;

          // Expiry may be provided as seconds or absolute datetime
          int? expiresIn;
          if (body.containsKey('expires_in_seconds')) {
            expiresIn = body['expires_in_seconds'] as int?;
          } else if (body.containsKey('expires_at')) {
            try {
              final expiresAt = DateTime.parse(body['expires_at'].toString());
              final diff = expiresAt.difference(DateTime.now()).inSeconds;
              if (diff > 0) expiresIn = diff;
            } catch (_) {
              expiresIn = null;
            }
          }

          final isGuest = (body['user']?['is_guest'] ?? body['is_guest'] ?? true) as bool;
          if (token == null || token.isEmpty) return false;
          await _saveToken(token, name, expiresIn, isGuest);
          return true;
        } else {
          // If server responded with a payload that suggests an existing guest (e.g., user id/email), try to login as that guest
          try {
            final body = json.decode(res.body) as Map<String, dynamic>;
            // If backend returned a 'user' with id
            if (body['user'] is Map && body['user']['id'] != null) {
              final gid = body['user']['id'];
              final ok = await _loginAsExistingById(baseUrl, gid);
              if (ok) return true;
            }

            // If backend returned an email, try to find matching guest from list
            final email = body['email'] as String? ?? (body['user'] is Map ? (body['user']['email'] as String?) : null);
            if (email != null && email.isNotEmpty) {
              final id = await _findGuestIdByEmail(baseUrl, email);
              if (id != null) {
                final ok = await _loginAsExistingById(baseUrl, id);
                if (ok) return true;
              }
            }
          } catch (_) {
            // ignore parse errors and continue
          }
        }
      } catch (_) {
        // try next candidate
        continue;
      }
    }

    // Fallback: query guest list and pick a valid guest to reuse
    try {
      final listUri = Uri.parse('$baseUrl/api/guest/list');
      final lres = await http.get(listUri).timeout(const Duration(seconds: 10));
      if (lres.statusCode == 200) {
        final body = json.decode(lres.body) as Map<String, dynamic>;
        final List<dynamic> guests = (body['guests'] ?? []) as List<dynamic>;
        for (final g in guests) {
          if (g is Map && (g['is_valid'] == true || (g['token_expires_at'] != null && DateTime.tryParse(g['token_expires_at'].toString())?.isAfter(DateTime.now()) == true))) {
            final id = g['id'];
            final ok = await _loginAsExistingById(baseUrl, id);
            if (ok) return true;
          }
        }
      }
    } catch (_) {
      // ignore
    }

    return false;
  }

  static Future<bool> _loginAsExistingById(String baseUrl, dynamic guestId) async {
    try {
      final uri = Uri.parse('$baseUrl/api/guest/login-as-existing');
      final res = await http.post(uri, headers: {'Content-Type': 'application/json'}, body: json.encode({'guest_id': guestId})).timeout(const Duration(seconds: 10));
      if (res.statusCode != 200 && res.statusCode != 201) return false;
      final body = json.decode(res.body) as Map<String, dynamic>;
      final token = body['api_token'] as String? ?? body['token'] as String?;
      final name = ((body['user']?['name']) ?? body['name'] ?? '') as String;
      int? expiresIn;
      if (body.containsKey('expires_in_seconds')) {
        expiresIn = body['expires_in_seconds'] as int?;
      } else if (body.containsKey('expires_at')) {
        try {
          final expiresAt = DateTime.parse(body['expires_at'].toString());
          final diff = expiresAt.difference(DateTime.now()).inSeconds;
          if (diff > 0) expiresIn = diff;
        } catch (_) {}
      }
      final isGuest = (body['user']?['is_guest'] ?? body['is_guest'] ?? true) as bool;
      if (token == null || token.isEmpty) return false;
      await _saveToken(token, name, expiresIn, isGuest);
      return true;
    } catch (_) {
      return false;
    }
  }

  static Future<int?> _findGuestIdByEmail(String baseUrl, String email) async {
    try {
      final listUri = Uri.parse('$baseUrl/api/guest/list');
      final lres = await http.get(listUri).timeout(const Duration(seconds: 10));
      if (lres.statusCode != 200) return null;
      final body = json.decode(lres.body) as Map<String, dynamic>;
      final List<dynamic> guests = (body['guests'] ?? []) as List<dynamic>;
      for (final g in guests) {
        if (g is Map && (g['email']?.toString().toLowerCase() == email.toLowerCase())) {
          return g['id'] as int?;
        }
      }
    } catch (_) {}
    return null;
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
