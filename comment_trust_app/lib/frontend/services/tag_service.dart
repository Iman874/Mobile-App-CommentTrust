import 'dart:convert';
import 'package:http/http.dart' as http;

class TagService {
  static Future<List<Map<String,dynamic>>> fetchTagCounts(String baseUrl, String productKey) async {
    final uri = Uri.parse('$baseUrl/api/products/$productKey/tags');
    final res = await http.get(uri).timeout(const Duration(seconds: 15));
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> tags = body['tags'] ?? [];
    return tags.cast<Map<String,dynamic>>();
  }

  static Future<List<Map<String,dynamic>>> fetchCommentsByTag(String baseUrl, String productKey, String tag, {int limit=50}) async {
    final uri = Uri.parse('$baseUrl/api/products/$productKey/comments?tag=${Uri.encodeComponent(tag)}&limit=$limit');
    final res = await http.get(uri).timeout(const Duration(seconds: 20));
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> data = body['data'] ?? [];
    return data.cast<Map<String,dynamic>>();
  }
}
