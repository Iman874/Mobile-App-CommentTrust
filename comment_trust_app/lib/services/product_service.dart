import 'dart:convert';
import '../route/api_client.dart';

class ProductService {
  static Future<List<Map<String, dynamic>>> fetchLatest(String baseUrl, {int limit = 10}) async {
    // Use documented /api/products endpoint with per_page to request latest items
    final uri = Uri.parse('$baseUrl/api/products?per_page=$limit&page=1');
    final res = await ApiClient.get(uri, timeoutSeconds: 10);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> data = body['data'] ?? [];
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> fetchSimplified(String baseUrl, {int limit = 10}) async {
    // Align with API docs: use per_page param
    final uri = Uri.parse('$baseUrl/api/products?per_page=$limit');
    final res = await ApiClient.get(uri, timeoutSeconds: 10);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> data = body['data'] ?? [];
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> fetchAll(String baseUrl) async {
    // There is no /all in API docs — request a large per_page to fetch many items
    final uri = Uri.parse('$baseUrl/api/products?per_page=1000');
    final res = await ApiClient.get(uri, timeoutSeconds: 20);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> data = body['data'] ?? [];
    return data.cast<Map<String, dynamic>>();
  }
}
