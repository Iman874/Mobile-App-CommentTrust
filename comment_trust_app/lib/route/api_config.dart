import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  ApiConfig._internal();
  static final ApiConfig _instance = ApiConfig._internal();
  static ApiConfig get I => _instance;

  String _scheme = 'http';
  String _host = '';
  String? _port;
  bool _demoMode = false;

  String get scheme => _scheme;
  String get host => _host;
  String? get port => _port;
  bool get demoMode => _demoMode;

  String get baseUrl {
    final p = (_port == null || _port!.trim().isEmpty) ? '' : ':${_port!.trim()}';
    return "$scheme://$host$p";
  }

  Future<void> load() async {
    final sp = await SharedPreferences.getInstance();
    _scheme = sp.getString('api.scheme') ?? 'http';
    _host = sp.getString('api.host') ?? '';
    _port = sp.getString('api.port');
    _demoMode = sp.getBool('api.demoMode') ?? false;
  }

  Future<void> save({
    required String scheme,
    required String host,
    String? port,
    required bool demoMode,
  }) async {
    _scheme = scheme;
    _host = host;
    _port = (port != null && port.trim().isEmpty) ? null : port;
    _demoMode = demoMode;
    final sp = await SharedPreferences.getInstance();
    await sp.setString('api.scheme', _scheme);
    await sp.setString('api.host', _host);
    if (_port == null) {
      await sp.remove('api.port');
    } else {
      await sp.setString('api.port', _port!);
    }
    await sp.setBool('api.demoMode', _demoMode);
  }
}
