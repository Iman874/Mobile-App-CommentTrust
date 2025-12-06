import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  static Future<bool> ping(String baseUrl) async {
    try {
      final uri = Uri.parse('$baseUrl/api/ping');
      final res = await http.get(uri).timeout(const Duration(seconds: 5));
      if (res.statusCode == 200) {
        final body = json.decode(res.body);
        return body is Map && (body['status']?.toString().toLowerCase() == 'ok');
      }
    } catch (_) {}
    return false;
  }
}
