import 'dart:convert';
import '../route/api_client.dart';

class AnalysisService {
  static Future<Map<String, dynamic>?> fetchAnalysis(String baseUrl, String productKey) async {
    try {
      // Use product stats endpoint documented in Laravel API
      final uri = Uri.parse('$baseUrl/api/products/$productKey/stats');
      final res = await ApiClient.get(uri, timeoutSeconds: 15);
      if (res.statusCode != 200) return null;
      final body = json.decode(res.body) as Map<String, dynamic>;
      final stats = body['stats'] as Map<String, dynamic>? ?? {};

      // Normalize backend stats into the frontend's expected `metrics` shape
      final metrics = <String, dynamic>{
        'count_reviews': stats['total_comments'] ?? 0,
        'avg_rating': stats['average_rating'] ?? 0.0,
        'avg_trust_percent_norm': stats['average_trust_score'] ?? 0.0,
        'sentiment_counts': {
          'positive': (stats['sentiment_distribution'] as Map<String, dynamic>?)?['positive'] ?? 0,
          'negative': (stats['sentiment_distribution'] as Map<String, dynamic>?)?['negative'] ?? 0,
          'neutral': (stats['sentiment_distribution'] as Map<String, dynamic>?)?['neutral'] ?? 0,
        },
        'rating_distribution': stats['rating_distribution'] ?? {},
        'fake_review_count': stats['fake_review_count'] ?? 0,
        'tagged_comment_count': stats['tagged_comment_count'] ?? 0,
        'most_common_tags': stats['most_common_tags'] ?? stats['tag_cloud'] ?? {},
      };

      return {'ok': body['ok'] ?? true, 'metrics': metrics, 'raw_stats': stats};
    } catch (_) {
      return null;
    }
  }

  static Future<List<Map<String, dynamic>>> fetchComments(String baseUrl, String productKey, {int limit = 20}) async {
    try {
      // Use documented comments endpoint
      final uri = Uri.parse('$baseUrl/api/comments/$productKey?per_page=$limit');
      final res = await ApiClient.get(uri, timeoutSeconds: 15);
      if (res.statusCode != 200) return [];
      final body = json.decode(res.body) as Map<String, dynamic>;
      // API may return comments in 'comments' or 'data'
      final data = (body['comments'] ?? body['data'] ?? []) as List<dynamic>;
      return data.cast<Map<String, dynamic>>();
    } catch (_) {
      return [];
    }
  }
}
