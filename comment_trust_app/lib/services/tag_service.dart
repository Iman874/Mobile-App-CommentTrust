import 'dart:convert';
import '../route/api_client.dart';
import 'analysis_service.dart';

class TagService {
  static Future<List<Map<String,dynamic>>> fetchTagCounts(String baseUrl, String productKey) async {
    // The API may provide tags in multiple endpoints/shapes:
    // 1) product stats -> stats.data.tag_stats / most_common_tags (map or list)
    // 2) /api/products/{productKey}/tags -> returns {tags:[{name,comments_count}]}
    // 3) tag_cloud or other custom shapes
    try {
      final uri = Uri.parse('$baseUrl/api/products/$productKey/stats');
      final res = await ApiClient.get(uri, timeoutSeconds: 15);
      final List<Map<String, dynamic>> out = [];
      if (res.statusCode == 200) {
        final body = json.decode(res.body) as Map<String,dynamic>;
        final stats = body['stats'] as Map<String,dynamic>? ?? {};

        final dynamic tagsRaw = stats['most_common_tags'] ?? stats['tag_cloud'] ?? stats['tag_stats'] ?? [];

        if (tagsRaw is Map) {
          for (final e in tagsRaw.entries) {
            out.add({'tag': e.key.toString(), 'count': e.value is num ? e.value : int.tryParse(e.value.toString()) ?? 0});
          }
        } else if (tagsRaw is List) {
          for (final item in tagsRaw) {
            if (item is Map) {
              final name = (item['tag'] ?? item['name'] ?? item['label'])?.toString() ?? '';
              final count = item['count'] ?? item['value'] ?? 0;
              if (name.isNotEmpty) {
                out.add({'tag': name, 'count': count is num ? count : int.tryParse(count.toString()) ?? 0});
              }
            } else if (item is List && item.length >= 2) {
              out.add({'tag': item[0].toString(), 'count': item[1] is num ? item[1] : int.tryParse(item[1].toString()) ?? 0});
            }
          }
        }
      }

      // If nothing found in stats, try the dedicated tags endpoint
      if (out.isEmpty) {
        try {
          final uri2 = Uri.parse('$baseUrl/api/products/$productKey/tags');
          final r2 = await ApiClient.get(uri2, timeoutSeconds: 15);
          if (r2.statusCode == 200) {
            final b2 = json.decode(r2.body) as Map<String,dynamic>;
            final List<dynamic> tagsList = (b2['tags'] ?? b2['data'] ?? []) as List<dynamic>;
            for (final t in tagsList) {
              if (t is Map) {
                final name = (t['name'] ?? t['tag'] ?? t['label'])?.toString() ?? '';
                final count = t['comments_count'] ?? t['count'] ?? t['value'] ?? 0;
                if (name.isNotEmpty) {
                  out.add({'tag': name, 'count': count is num ? count : int.tryParse(count.toString()) ?? 0});
                }
              }
            }
          }
        } catch (e) {
          print('[TagService] Tags endpoint fallback failed: $e');
        }
      }

      return out;
    } catch (e) {
      print('[TagService] Error fetching tag counts: $e');
      return [];
    }
  }

  static Future<List<Map<String,dynamic>>> fetchCommentsByTag(String baseUrl, String productKey, String tag, {int limit=50}) async {
    // Use the documented comments endpoint and filter by tags (comma-separated)
    final uri = Uri.parse('$baseUrl/api/comments/$productKey?tags=${Uri.encodeComponent(tag)}&per_page=$limit');
    print('[TagService] GET $uri');
    final res = await ApiClient.get(uri, timeoutSeconds: 20);
    print('[TagService] Response (${res.statusCode}): ${res.body}');
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body) as Map<String,dynamic>;
    final List<dynamic> data = (body['comments'] ?? body['data'] ?? []) as List<dynamic>;
    final List<Map<String,dynamic>> normalized = [];
    for (final item in data) {
      if (item is Map) normalized.add(AnalysisService.normalizeComment(item));
    }
    print('[TagService] Normalized ${normalized.length} comments for tag=$tag');
    return normalized;
  }
}
