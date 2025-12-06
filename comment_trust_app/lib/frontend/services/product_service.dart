import 'dart:convert';
import 'package:http/http.dart' as http;

class ProductService {
  static Future<List<Map<String, dynamic>>> fetchLatest(String baseUrl, {int limit = 10}) async {
    final uri = Uri.parse('$baseUrl/api/products/latest?limit=$limit');
    final res = await http.get(uri).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> data = body['data'] ?? [];
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> fetchSimplified(String baseUrl, {int limit = 10}) async {
    final uri = Uri.parse('$baseUrl/api/products?limit=$limit');
    final res = await http.get(uri).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> data = body['data'] ?? [];
    return data.cast<Map<String, dynamic>>();
  }

  static Future<List<Map<String, dynamic>>> fetchAll(String baseUrl) async {
    final uri = Uri.parse('$baseUrl/api/products/all');
    final res = await http.get(uri).timeout(const Duration(seconds: 20));
    if (res.statusCode != 200) return [];
    final body = json.decode(res.body);
    final List<dynamic> data = body['data'] ?? [];
    return data.cast<Map<String, dynamic>>();
  }
}
