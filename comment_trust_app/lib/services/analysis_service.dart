import 'dart:convert';
import '../route/api_client.dart';

class AnalysisService {
  static Future<Map<String, dynamic>?> fetchAnalysis(String baseUrl, String productKey) async {
    try {
      // Use product stats endpoint documented in Laravel API
      final uri = Uri.parse('$baseUrl/api/products/$productKey/stats');
      print('[AnalysisService] GET $uri');
      final res = await ApiClient.get(uri, timeoutSeconds: 15);
      print('[AnalysisService] Response (${res.statusCode}): ${res.body}');
      if (res.statusCode != 200) return null;
      final body = json.decode(res.body) as Map<String, dynamic>;

      // Stats may be nested under body['stats']['data'] or directly under body['stats']
      final rawStats = body['stats'] ?? body;
      final Map<String, dynamic> stats = rawStats is Map ? Map<String, dynamic>.from(rawStats) : {};
      final Map<String, dynamic> data = (stats['data'] is Map)
          ? Map<String, dynamic>.from(stats['data'])
          : (body['data'] is Map ? Map<String, dynamic>.from(body['data']) : Map<String, dynamic>.from(stats));

      // Safely extract values with fallbacks and normalize shapes
      // Normalize numeric fields safely (handle int/double/string shapes)
      final rawCount = data['review_count'] ?? data['count_reviews'] ?? data['total_comments'] ?? data['reviewCount'] ?? 0;
      int countReviews;
      if (rawCount is num) countReviews = rawCount.toInt();
      else countReviews = int.tryParse(rawCount?.toString() ?? '0') ?? 0;

      final rawRating = data['rating'] ?? data['avg_rating'] ?? data['average_rating'] ?? 0;
      double avgRating;
      if (rawRating is num) avgRating = rawRating.toDouble();
      else avgRating = double.tryParse(rawRating?.toString() ?? '0') ?? 0.0;

      final rawTrust = data['avg_trust_score'] ?? data['average_trust_score'] ?? data['avg_trust_percent_norm'] ?? data['avg_trust_percent'] ?? 0;
      double avgTrust;
      if (rawTrust is num) avgTrust = rawTrust.toDouble();
      else avgTrust = double.tryParse(rawTrust?.toString() ?? '0') ?? 0.0;

      // Sentiment counts can appear under different keys
      final dynamic sentimentRaw = data['sentiment_count'] ?? data['sentiment_distribution'] ?? data['sentiment_counts'] ?? {};
      Map<String, dynamic> sentimentMap = {};
      if (sentimentRaw is Map) {
        sentimentMap = Map<String, dynamic>.from(sentimentRaw.map((k, v) => MapEntry(k.toString(), v)));
      }

      final sentimentCounts = <String,int>{
        'positive': (() {
          final v = sentimentMap['positive'] ?? sentimentMap['pos'] ?? 0;
          if (v is num) return v.toInt();
          return int.tryParse(v?.toString() ?? '0') ?? 0;
        })(),
        'negative': (() {
          final v = sentimentMap['negative'] ?? sentimentMap['neg'] ?? 0;
          if (v is num) return v.toInt();
          return int.tryParse(v?.toString() ?? '0') ?? 0;
        })(),
        'neutral': (() {
          final v = sentimentMap['neutral'] ?? sentimentMap['neu'] ?? 0;
          if (v is num) return v.toInt();
          return int.tryParse(v?.toString() ?? '0') ?? 0;
        })(),
      };

      // Other fields
      final ratingDistribution = data['rating_distribution'] ?? data['ratingDistribution'] ?? {};
      final rawFake = data['fake_rate'] ?? data['fake_review_count'] ?? 0;
      final fakeCount = rawFake is num ? rawFake : (num.tryParse(rawFake?.toString() ?? '0') ?? 0);
      final taggedCount = (data['tag_stats'] is List) ? (data['tag_stats'] as List).length : (data['tagged_comment_count'] ?? 0);
      final mostCommonTags = data['tag_stats'] ?? data['most_common_tags'] ?? data['tag_cloud'] ?? [];

      final metrics = <String, dynamic>{
        'count_reviews': countReviews,
        'avg_rating': avgRating,
        'avg_trust_percent_norm': avgTrust,
        'sentiment_counts': sentimentCounts,
        'rating_distribution': ratingDistribution,
        'fake_review_count': fakeCount,
        'tagged_comment_count': taggedCount,
        'most_common_tags': mostCommonTags,
      };

      print('[AnalysisService] Parsed metrics: $metrics');
      // Also print raw data for debugging so we can compare shapes
      print('[AnalysisService] Raw stats object: $data');

      return {'ok': body['ok'] ?? true, 'metrics': metrics, 'raw_stats': data};
    } catch (e) {
      print('[AnalysisService] Error fetching analysis: $e');
      return null;
    }
  }

  static Map<String,dynamic> normalizeComment(Map raw) {
    // Normalize comment fields into a consistent shape used by UI
    final Map<String,dynamic> out = {};
    out['raw'] = raw;
    // Prefer nested user object if present
    String _extractUserName(dynamic r) {
      if (r is Map) {
        if (r['user'] is Map) {
          final u = r['user'] as Map;
          return (u['name'] ?? u['username'] ?? u['full_name'] ?? u['display_name'])?.toString() ?? '';
        }
        if (r['author'] is Map) {
          final a = r['author'] as Map;
          return (a['name'] ?? a['username'] ?? a['display_name'])?.toString() ?? '';
        }
      }
      return (r['user_name'] ?? r['username'] ?? r['name'] ?? r['author'] ?? '')?.toString() ?? '';
    }

    out['user_name'] = _extractUserName(raw);
    if ((out['user_name'] as String).isEmpty) out['user_name'] = 'Anon';
    out['text'] = (raw['text'] ?? raw['comment'] ?? raw['body'] ?? '')?.toString();
    out['rating'] = (raw['rating_star'] ?? raw['rating'] ?? raw['rate'] ?? raw['score']) is num
        ? (raw['rating_star'] ?? raw['rating'] ?? raw['rate'] ?? raw['score']) as num
        : double.tryParse((raw['rating_star'] ?? raw['rating'] ?? raw['rate'] ?? raw['score'])?.toString() ?? '0') ?? 0;
    out['likes'] = (raw['likes'] ?? raw['like_count'] ?? 0) is num
        ? (raw['likes'] ?? raw['like_count'] ?? 0) as int
        : int.tryParse((raw['likes'] ?? raw['like_count'] ?? 0).toString()) ?? 0;
    out['sentiment'] = (raw['sentiment'] ?? raw['sentiment_label'] ?? '')?.toString();
    out['is_fake'] = (raw['is_fake'] ?? raw['fake'] ?? raw['fake_pred'] ?? false) is bool
        ? (raw['is_fake'] ?? raw['fake'] ?? raw['fake_pred'] ?? false) as bool
        : ((raw['is_fake'] ?? raw['fake'] ?? raw['fake_pred'])?.toString().toLowerCase() == 'true');
    out['tags'] = (raw['tags'] ?? raw['tag_list'] ?? raw['labels'] ?? []) as List? ?? [];
    return out;
  }

  static Future<List<Map<String, dynamic>>> fetchComments(String baseUrl, String productKey, {int limit = 20}) async {
    try {
      // Use documented comments endpoint
      final uri = Uri.parse('$baseUrl/api/comments/$productKey?per_page=$limit');
      print('[AnalysisService] GET $uri');
      final res = await ApiClient.get(uri, timeoutSeconds: 15);
      print('[AnalysisService] Response (${res.statusCode}): ${res.body}');
      if (res.statusCode != 200) return [];
      final body = json.decode(res.body) as Map<String, dynamic>;
      // API may return comments in 'comments' or 'data'
      final data = (body['comments'] ?? body['data'] ?? []) as List<dynamic>;
      final List<Map<String,dynamic>> normalized = [];
      for (final item in data) {
        if (item is Map) {
          final n = normalizeComment(item);
          normalized.add(n);
        }
      }
      print('[AnalysisService] Normalized ${normalized.length} comments, sample: ${normalized.isNotEmpty ? normalized.take(3).toList() : []}');
      return normalized;
    } catch (e) {
      print('[AnalysisService] Error fetching comments: $e');
      return [];
    }
  }
}
