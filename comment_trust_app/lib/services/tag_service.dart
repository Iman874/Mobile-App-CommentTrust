import 'dart:convert';
import '../route/api_client.dart';

class TagService {
  static Future<List<Map<String,dynamic>>> fetchTagCounts(String baseUrl, String productKey) async {
    // The API exposes tag info inside product stats (most_common_tags / tag_cloud)
    final uri = Uri.parse('$baseUrl/api/products/$productKey/stats');
    final res = await ApiClient.get(uri, timeoutSeconds: 15);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body) as Map<String,dynamic>;
    final stats = body['stats'] as Map<String,dynamic>? ?? {};
    final tagsMap = (stats['most_common_tags'] ?? stats['tag_cloud'] ?? {}) as Map<String,dynamic>;
    final tags = tagsMap.entries.map((e) => {'tag': e.key, 'count': e.value}).toList();
    return tags.cast<Map<String,dynamic>>();
  }

  static Future<List<Map<String,dynamic>>> fetchCommentsByTag(String baseUrl, String productKey, String tag, {int limit=50}) async {
    // Use the documented comments endpoint and filter by tags (comma-separated)
    final uri = Uri.parse('$baseUrl/api/comments/$productKey?tags=${Uri.encodeComponent(tag)}&per_page=$limit');
    final res = await ApiClient.get(uri, timeoutSeconds: 20);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body) as Map<String,dynamic>;
    final List<dynamic> data = (body['comments'] ?? body['data'] ?? []) as List<dynamic>;
    return data.cast<Map<String,dynamic>>();
  }
}
