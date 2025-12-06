import 'dart:convert';
import 'package:http/http.dart' as http;

class AnalysisService {
  static Future<Map<String, dynamic>?> fetchAnalysis(String baseUrl, String productKey) async {
    try {
      final uri = Uri.parse('$baseUrl/api/analysis/$productKey');
      final res = await http.get(uri).timeout(const Duration(seconds: 15));
      if (res.statusCode != 200) return null;
      return json.decode(res.body) as Map<String, dynamic>;
    } catch (_) {
      return null;
    }
  }

  static Future<List<Map<String, dynamic>>> fetchComments(String baseUrl, String productKey, {int limit = 20}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/products/$productKey/comments?limit=$limit');
      final res = await http.get(uri).timeout(const Duration(seconds: 15));
      if (res.statusCode != 200) return [];
      final body = json.decode(res.body) as Map<String, dynamic>;
      final data = (body['data'] ?? []) as List<dynamic>;
      return data.cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }
}
