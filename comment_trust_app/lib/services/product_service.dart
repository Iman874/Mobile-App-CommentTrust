import 'dart:convert';
import '../route/api_client.dart';

class ProductService {
  static Future<List<Map<String, dynamic>>> fetchLatest(String baseUrl, {int limit = 10}) async {
    // Use documented /api/products endpoint with per_page to request latest items
    final uri = Uri.parse('$baseUrl/api/products?per_page=$limit&page=1');
    final res = await ApiClient.get(uri, timeoutSeconds: 10);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body) as Map<String, dynamic>;
    final List<dynamic> data = (body['products'] ?? body['data'] ?? []) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> fetchSimplified(String baseUrl, {int limit = 10}) async {
    // Align with API docs: use per_page param
    final uri = Uri.parse('$baseUrl/api/products?per_page=$limit');
    final res = await ApiClient.get(uri, timeoutSeconds: 10);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body) as Map<String, dynamic>;
    final List<dynamic> data = (body['products'] ?? body['data'] ?? []) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> fetchAll(String baseUrl) async {
    // There is no /all in API docs — request a large per_page to fetch many items
    final uri = Uri.parse('$baseUrl/api/products?per_page=1000');
    final res = await ApiClient.get(uri, timeoutSeconds: 20);
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body) as Map<String, dynamic>;
    final List<dynamic> data = (body['products'] ?? body['data'] ?? []) as List<dynamic>;
    return data.cast<Map<String, dynamic>>();
  }

  static Future<Map<String, dynamic>?> fetchProduct(String baseUrl, String productKey) async {
    try {
      final uri = Uri.parse('$baseUrl/api/products/$productKey');
      // Log request URI
      print('[ProductService] GET $uri');
      final res = await ApiClient.get(uri, timeoutSeconds: 15);
      // Log status and body for debugging
      print('[ProductService] Response (${res.statusCode}): ${res.body}');
      if (res.statusCode != 200) return null;
      final body = json.decode(res.body) as Map<String, dynamic>;
      // The API may return the product under 'product' or directly in 'data'
      final product = (body['product'] ?? body['data'] ?? body) as Map<String, dynamic>;
      return Map<String, dynamic>.from(product);
    } catch (e) {
      print('[ProductService] Error fetching product: $e');
      return null;
    }
  }
}
