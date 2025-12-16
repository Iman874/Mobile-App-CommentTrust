import 'dart:convert';
import 'package:http/http.dart' as http;
import '../services/auth_service.dart';

class ApiClient {
  static Future<Map<String,String>> _authHeaders() async {
    final token = await AuthService.token;
    if (token == null) return {};
    return {'Authorization': 'Bearer $token'};
  }

  static Future<bool> ping(String baseUrl) async {
    try {
      final uri = Uri.parse('$baseUrl/api/ping');
      final headers = await _authHeaders();
      final res = await http.get(uri, headers: headers).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final body = json.decode(res.body);
        return body is Map && (body['status']?.toString().toLowerCase() == 'ok');
      }
    } catch (_) {}
    return false;
  }

  static Future<http.Response> get(Uri uri, {Map<String,String>? extraHeaders, int timeoutSeconds = 15}) async {
    final h = await _authHeaders();
    if (extraHeaders != null) h.addAll(extraHeaders);
    return http.get(uri, headers: h).timeout(Duration(seconds: timeoutSeconds));
  }

  static Future<http.Response> post(Uri uri, {Map<String,String>? extraHeaders, Object? body, int timeoutSeconds = 15}) async {
    final h = await _authHeaders();
    h.addAll({'Content-Type':'application/json'});
    if (extraHeaders != null) h.addAll(extraHeaders);
    return http.post(uri, headers: h, body: body == null ? null : json.encode(body)).timeout(Duration(seconds: timeoutSeconds));
  }
}
