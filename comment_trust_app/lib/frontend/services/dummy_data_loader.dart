import 'dart:convert';
import 'package:flutter/services.dart' show rootBundle;

class DummyDataLoader {
  static Future<List<Map<String, dynamic>>> loadProducts() async {
    final raw = await rootBundle.loadString('assets/dummy_data/products.json');
    final list = json.decode(raw) as List<dynamic>;
    return list.cast<Map<String, dynamic>>();
  }
}
