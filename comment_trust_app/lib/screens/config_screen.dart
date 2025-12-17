import 'dart:convert';
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

    try {
      final uri = Uri.parse('$baseUrl/api/ping');
      final resp = await ApiClient.get(uri, timeoutSeconds: 5);
      print('[ConfigScreen] PING $uri => ${resp.statusCode} ${resp.body}');
      if (resp.statusCode == 200) {
        final body = (resp.body.isNotEmpty) ? resp.body : '{}';
        // basic success check
        try {
          final parsed = body.isNotEmpty ? (json.decode(body) as Map<String,dynamic>) : {};
          final ok = (parsed['status']?.toString().toLowerCase() == 'ok') || parsed['ok'] == true;
          if (!ok) {
            setState(() { _error = 'Backend ping responded but reported not-ok: ${parsed.toString()}'; _testing = false; });
            return;
          }
        } catch (e) {
          print('[ConfigScreen] Warning: failed parsing ping body: $e');
        }

        await ApiConfig.I.save(
          scheme: _scheme,
          host: host,
          port: port.isEmpty ? null : port,
          demoMode: false,
        );

        // Attempt guest login so the backend creates a guest user/token
        final gotGuest = await AuthService.guestLogin(baseUrl);
        print('[ConfigScreen] guestLogin => $gotGuest');
        if (!mounted) return;
        if (!gotGuest) {
          setState(() {
            _error = 'Gagal membuat akun guest pada backend. Coba lagi atau periksa konfigurasi.';
            _testing = false;
          });
          return;
        }

        Navigator.pushReplacementNamed(context, '/');
        setState(() { _testing = false; });
        return;
      } else {
        setState(() {
          _error = 'Tidak dapat terhubung ke backend di $baseUrl (HTTP ${resp.statusCode})';
        });
      }
    } catch (e) {
      setState(() { _error = 'Gagal memanggil $baseUrl/api/ping : ${e.toString()}'; });
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

  Future<void> _runDiagnostics() async {
    setState(() { _testing = true; _error = null; });
    await ApiConfig.I.load();
    final base = ApiConfig.I.baseUrl;
    try {
      final pingUri = Uri.parse('$base/api/ping');
      final pingRes = await ApiClient.get(pingUri, timeoutSeconds: 5);
      print('[ConfigScreen][DIAG] PING $pingUri => ${pingRes.statusCode} ${pingRes.body}');

      final prodUri = Uri.parse('$base/api/products?limit=1');
      final prodRes = await ApiClient.get(prodUri, timeoutSeconds: 8);
      print('[ConfigScreen][DIAG] PRODUCTS $prodUri => ${prodRes.statusCode} ${prodRes.body}');

      String detail = 'PING: ${pingRes.statusCode}\n${pingRes.body}\n\nPRODUCTS: ${prodRes.statusCode}\n${prodRes.body}';
      if (!mounted) return;
      await showDialog(context: context, builder: (ctx) => AlertDialog(title: const Text('Diagnostic API'), content: SingleChildScrollView(child: SelectableText(detail)), actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK'))]));
    } catch (e) {
      setState(() { _error = 'Diagnosa gagal: ${e.toString()}'; });
    } finally {
      setState(() { _testing = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        automaticallyImplyLeading: false,
        title: Row(children: [
          Image.asset('assets/logo/logo_commenttrust.png', width: 28, height: 28, errorBuilder: (ctx,err,st){ return const Icon(Icons.broken_image, size: 28); }),
          const SizedBox(width: 8),
          const Text('Konfigurasi Koneksi'),
        ]),
      ),
      body: GestureDetector(
        onTap: () => FocusScope.of(context).unfocus(),
        child: SingleChildScrollView(
          padding: EdgeInsets.only(left: 16.0, right: 16.0, top: 16.0, bottom: MediaQuery.of(context).viewInsets.bottom + 16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Small info row showing current saved base URL and app name
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(12),
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8), boxShadow: [BoxShadow(color: const Color.fromRGBO(0,0,0,0.03), blurRadius: 6, offset: Offset(0,2))]),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text('App name: CommentTrust', style: const TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    Text('Current base URL: ${ApiConfig.I.baseUrl}', style: const TextStyle(color: Colors.black87)),
                  ]),
                ),
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
                const SizedBox(height: 12),
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
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: _testing ? null : _runDiagnostics,
                        child: const Text('Diagnosa API & Print JSON'),
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
      ),
    );
  }
}
