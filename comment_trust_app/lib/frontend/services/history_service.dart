import 'package:shared_preferences/shared_preferences.dart';

class HistoryService {
  static const _kLastProductKey = 'last_product_key';
  static const _kLastProductName = 'last_product_name';

  static Future<void> setLastViewed({required String productKey, required String productName}) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kLastProductKey, productKey);
    await prefs.setString(_kLastProductName, productName);
  }

  static Future<Map<String, String>?> getLastViewed() async {
    final prefs = await SharedPreferences.getInstance();
    final key = prefs.getString(_kLastProductKey);
    final name = prefs.getString(_kLastProductName);
    if (key == null || name == null) return null;
    return {'productKey': key, 'productName': name};
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kLastProductKey);
    await prefs.remove(_kLastProductName);
  }
}
