import 'package:flutter/material.dart';
import '../route/api_config.dart';
import '../route/api_client.dart';
import '../services/auth_service.dart';

class ConfigScreen extends StatefulWidget {
  const ConfigScreen({super.key});

  @override
  State<ConfigScreen> createState() => _ConfigScreenState();
}

class _ConfigScreenState extends State<ConfigScreen> {
  final _formKey = GlobalKey<FormState>();
  String _scheme = 'http';
  final _hostCtrl = TextEditingController();
  final _portCtrl = TextEditingController();
  bool _testing = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    ApiConfig.I.load().then((_) {
      setState(() {
        _scheme = ApiConfig.I.scheme;
        _hostCtrl.text = ApiConfig.I.host;
        _portCtrl.text = ApiConfig.I.port ?? '';
      });
    });
  }

  Future<void> _testAndContinue() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _testing = true;
      _error = null;
    });
    final host = _hostCtrl.text.trim();
    final port = _portCtrl.text.trim();
    final baseUrl = port.isEmpty ? '$_scheme://$host' : '$_scheme://$host:$port';
    final ok = await ApiClient.ping(baseUrl);
    if (!mounted) return;
    if (ok) {
      await ApiConfig.I.save(
        scheme: _scheme,
        host: host,
        port: port.isEmpty ? null : port,
        demoMode: false,
      );
      if (!mounted) return;

      // Attempt guest login so the backend creates a guest user/token
      final gotGuest = await AuthService.guestLogin(baseUrl);
      if (!mounted) return;
      if (!gotGuest) {
        setState(() {
          _error = 'Gagal membuat akun guest pada backend. Coba lagi atau periksa konfigurasi.';
        });
        return;
      }

      Navigator.pushReplacementNamed(context, '/');
    } else {
      setState(() {
        _error = 'Tidak dapat terhubung ke backend di $baseUrl';
      });
    }
    setState(() {
      _testing = false;
    });
  }

  Future<void> _launchDemo() async {
    await ApiConfig.I.save(
      scheme: 'http',
      host: '',
      port: null,
      demoMode: true,
    );
    if (!mounted) return;
    Navigator.pushReplacementNamed(context, '/');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Konfigurasi Koneksi')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Protocol'),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                initialValue: _scheme,
                items: const [
                  DropdownMenuItem(value: 'http', child: Text('http')),
                  DropdownMenuItem(value: 'https', child: Text('https')),
                ],
                onChanged: (v) => setState(() => _scheme = v ?? 'http'),
              ),
              const SizedBox(height: 16),
              const Text('Base URL / Host'),
              const SizedBox(height: 8),
              TextFormField(
                controller: _hostCtrl,
                decoration: const InputDecoration(
                  hintText: 'contoh: 192.168.1.10 atau domain.com',
                  border: OutlineInputBorder(),
                ),
                validator: (v) => (v == null || v.trim().isEmpty)
                    ? 'Host tidak boleh kosong'
                    : null,
              ),
              const SizedBox(height: 16),
              const Text('Port (opsional) — kosongkan bila tidak pakai'),
              const SizedBox(height: 8),
              TextFormField(
                controller: _portCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  hintText: 'contoh: 8000',
                  border: OutlineInputBorder(),
                ),
              ),
              if (_error != null) ...[
                const SizedBox(height: 12),
                Text(_error!, style: const TextStyle(color: Colors.red)),
              ],
              const Spacer(),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _testing ? null : _testAndContinue,
                      child: _testing
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Test & Continue'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Center(
                child: TextButton(
                  onPressed: _launchDemo,
                  child: const Text('Launch Demo Version (Offline)'),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }
}
