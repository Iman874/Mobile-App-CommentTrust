import 'dart:convert';

import 'package:flutter/material.dart';
import '../widgets/custom_app_bar.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import '../data-dummy/dummy_data_loader.dart';
import '../route/api_config.dart';
import '../route/api_client.dart';
import '../services/auth_service.dart';
import '../services/product_service.dart';
import 'product_detail_screen.dart';

class HomeScreen extends StatefulWidget {
  final bool embedded;
  const HomeScreen({super.key, this.embedded = false});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  bool _showAll = false;
  List<Map<String, dynamic>> _products = [];

  // Link input & process states
  final _urlCtrl = TextEditingController();
  bool _isProcessing = false;
  String? _statusMessage;
  bool _statusIsError = false;
  double? _progressPercent;

  bool _handledScannedUrl = false;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (!_handledScannedUrl) {
      final args = ModalRoute.of(context)?.settings.arguments;
      if (args is Map && args['scannedUrl'] is String) {
        final url = args['scannedUrl'] as String;
        _handledScannedUrl = true;
        // Fill input and submit
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _urlCtrl.text = url;
          _submitUrl();
        });
      }
    }
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    await ApiConfig.I.load();
    if (ApiConfig.I.demoMode) {
      final list = await DummyDataLoader.loadProducts();
      if (!mounted) return;
      setState(() { _products = list; });
      return;
    }
    final baseUrl = ApiConfig.I.baseUrl;
    // Ensure we have a token (guest) so /api/products returns user-specific items
    final tok = await AuthService.token;
    if ((tok == null || tok.isEmpty)) {
      await AuthService.guestLogin(baseUrl);
    }
    // Fetch 3 latest products from the database (most recently scraped)
    final remote = await ProductService.fetchLatest(baseUrl, limit: 3);
    // Map remote rows to UI structure (preserve existing keys expected by UI).
    final mapped = remote.map<Map<String,dynamic>>((p){
      return {
        // Don't assume image exists in DB; show placeholder text in detail page
        'image': 'assets/logo/logo_commenttrust.png',
        'name': p['name'] ?? p['title'] ?? 'Produk Tanpa Nama',
        'rating': (p['avg_rating'] ?? p['avg_rating_normalized'] ?? 0).toDouble(),
        'product_key': p['product_key'] ?? p['id'] ?? p['product_id'],
      }; }).toList();
    if (!mounted) return;
    setState(() { _products = mapped; });
  }

  @override
  Widget build(BuildContext context) {
    final displayedProducts = _showAll ? _products : _products.take(3).toList();

    final content = SingleChildScrollView(
      child: Column(
        children: [
            // 🔹 Bagian Input Link Produk
            Container(
              color: Colors.white,
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Masukkan Link Produk',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      color: Colors.black87,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    decoration: BoxDecoration(
                      color: Colors.grey[50],
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.grey[300]!),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _urlCtrl,
                            enabled: !_isProcessing,
                            decoration: const InputDecoration(
                              hintText: 'Tempel link Shopee di sini',
                              hintStyle: TextStyle(color: Colors.grey),
                              border: InputBorder.none,
                              contentPadding: EdgeInsets.symmetric(
                                horizontal: 8,
                                vertical: 12,
                              ),
                            ),
                            onSubmitted: (_) => _submitUrl(),
                          ),
                        ),
                        const SizedBox(width: 6),
                        _isProcessing
                            ? SizedBox(
                                width: 36,
                                height: 36,
                                child: Center(
                                  child: SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  ),
                                ),
                              )
                            : IconButton(
                                onPressed: _submitUrl,
                                icon: const Icon(Icons.send, color: Colors.green),
                              ),
                      ],
                    ),
                  ),
                  if (_statusMessage != null) ...[
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            _statusMessage!,
                            style: TextStyle(
                              color: _statusIsError ? Colors.red : Colors.black87,
                            ),
                          ),
                        ),
                        if (_progressPercent != null)
                          Text('${_progressPercent!.toStringAsFixed(0)}%')
                      ],
                    ),
                    if (_isProcessing) ...[
                      const SizedBox(height: 8),
                      LinearProgressIndicator(
                        value: _progressPercent == null ? null : (_progressPercent! / 100),
                        minHeight: 6,
                        backgroundColor: Colors.grey[200],
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.green),
                      ),
                    ],
                  ],
                ],
              ),
            ),

            const SizedBox(height: 8),

            // 🔹 Bagian Review Terbaru
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12.0),
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF1B4D3E),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text(
                        'Review Terbaru',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),

                    // 🔸 Daftar Produk
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      child: Column(
                        children: [
                          ...displayedProducts.map((product) {
                            return Container(
                              margin: const EdgeInsets.only(bottom: 12),
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: Colors.white,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.center,
                                children: [
                                  // 🔹 Gambar produk (lebih kecil & proporsional)
                                  SizedBox(
                                    width: 65,
                                    height: 65,
                                    child: ClipRRect(
                                      borderRadius: BorderRadius.circular(8),
                                      child: Image.asset(
                                        product['image'],
                                        fit: BoxFit.cover,
                                      ),
                                    ),
                                  ),
                                  const SizedBox(width: 10),

                                  // 🔹 Info produk
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text(
                                          product['name'],
                                          style: const TextStyle(
                                            fontSize: 12,
                                            fontWeight: FontWeight.w500,
                                            color: Colors.black87,
                                          ),
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                        ),
                                        const SizedBox(height: 8),
                                        Row(
                                          children: [
                                            Row(
                                              children: List.generate(5, (
                                                index,
                                              ) {
                                                return const Icon(
                                                  Icons.star,
                                                  size: 14,
                                                  color: Colors.orange,
                                                );
                                              }),
                                            ),
                                            const SizedBox(width: 6),
                                            Text(
                                              '${product['rating'].toStringAsFixed(1)}/5.0',
                                              style: TextStyle(
                                                fontSize: 12,
                                                color: Colors.grey[600],
                                              ),
                                            ),
                                          ],
                                        ),
                                      ],
                                    ),
                                  ),

                                  const SizedBox(width: 8),

                                  // 🔹 Tombol Detail
                                  GestureDetector(
                                    onTap: () {
                                      Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                          builder: (context) => ProductDetailScreen(
                                            productKey: product['product_key']?.toString() ?? '',
                                            productName: product['name']?.toString() ?? 'Produk',
                                          ),
                                        ),
                                      );
                                    },
                                    child: Container(
                                      padding: const EdgeInsets.symmetric(
                                        vertical: 6,
                                        horizontal: 12,
                                      ),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF1B4D3E),
                                        borderRadius: BorderRadius.circular(20),
                                      ),
                                      child: const Text(
                                        'Detail',
                                        style: TextStyle(
                                          color: Colors.white,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w500,
                                        ),
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            );
                          }),

                          // 🔹 Tombol Show More / Less
                          GestureDetector(
                            onTap: () {
                              setState(() {
                                _showAll = !_showAll;
                              });
                            },
                            child: Padding(
                              padding: const EdgeInsets.only(
                                top: 8,
                                bottom: 20,
                              ),
                              child: Center(
                                child: Text(
                                  _showAll ? 'Show less...' : 'Show more...',
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      );

    if (widget.embedded) return content;

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: CustomAppBar(),
      body: content,
      bottomNavigationBar: CustomBottomNavBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
          _navigateToScreen(context, index);
        },
      ),
    );
  }

  void _navigateToScreen(BuildContext context, int index) {
    switch (index) {
      case 0:
        break;
      case 1:
        Navigator.pushReplacementNamed(context, '/search');
        break;
      case 2:
        Navigator.pushReplacementNamed(context, '/scan');
        break;
      case 3:
        Navigator.pushReplacementNamed(context, '/reviews');
        break;
      case 4:
        Navigator.pushReplacementNamed(context, '/history');
        break;
    }
  }

  bool _isShopeeLink(String url) {
    final u = url.toLowerCase();
    return u.contains('shopee.') || u.contains('shp.ee');
  }

  Future<Map<String, dynamic>> _pollJob(String jobId, {int timeoutMs = 12 * 60 * 1000}) async {
    final baseUrl = ApiConfig.I.baseUrl;
    final start = DateTime.now();
    while (DateTime.now().difference(start).inMilliseconds < timeoutMs) {
      try {
        final uri = Uri.parse('$baseUrl/api/analysis/job/${Uri.encodeComponent(jobId)}');
        final resp = await ApiClient.get(uri).timeout(const Duration(seconds: 15));
        if (resp.statusCode == 200) {
          print('[HomeScreen] pollJob body: ${resp.body}');
          final body = json.decode(resp.body) as Map<String, dynamic>;

          // Extract the actual job payload consistently (FlaskService may nest under job.data or data)
          Map<String, dynamic> jobData;
          if (body['job'] is Map) {
            final jobWrapper = body['job'] as Map<String, dynamic>;
            if (jobWrapper['data'] is Map) {
              jobData = Map<String, dynamic>.from(jobWrapper['data']);
            } else {
              jobData = Map<String, dynamic>.from(jobWrapper);
            }
          } else if (body['data'] is Map) {
            jobData = Map<String, dynamic>.from(body['data']);
          } else {
            jobData = Map<String, dynamic>.from(body);
          }

          // Support alternate field names and nested shapes
          final phase = (jobData['phase'] ?? jobData['status'] ?? '') as String;
          final scrTotal = (jobData['scraper_total'] ?? jobData['scraperTotal'] ?? 0) as num;
          final scrProg = (jobData['scraper_progress'] ?? jobData['scraperProgress'] ?? jobData['progress'] ?? 0) as num;

          if (scrTotal > 0) {
            setState(() {
              _progressPercent = (scrProg / scrTotal) * 100;
              _statusMessage = 'Scraping: ${scrProg.toString()}/${scrTotal.toString()}';
            });
          }

          if (phase == 'error' || jobData['error'] != null) {
            return {
              'ok': false,
              'error': jobData['error'] ?? 'scrape error',
              'productId': jobData['product_id'] ?? jobData['productId']
            };
          }

          final scrapeDone = phase == 'done' || phase == 'completed' || (scrTotal > 0 && scrProg >= scrTotal);
          if (scrapeDone) {
            return {
              'ok': true,
              'productId': jobData['product_id'] ?? jobData['productId'] ?? jobData['product_id_str']
            };
          }
        }
      } catch (_) {
        // ignore transient errors and keep polling
      }

      await Future.delayed(const Duration(seconds: 3));
    }

    return {'ok': false, 'error': 'timeout waiting for scraping'};
  }

  Future<Map<String, dynamic>> _pollAnalysis(String productId, {int timeoutMs = 12 * 60 * 1000}) async {
    final baseUrl = ApiConfig.I.baseUrl;
    final start = DateTime.now();
    while (DateTime.now().difference(start).inMilliseconds < timeoutMs) {
      try {
        final uri = Uri.parse('$baseUrl/api/analysis/product/${Uri.encodeComponent(productId)}');
        final resp = await ApiClient.get(uri).timeout(const Duration(seconds: 15));
        if (resp.statusCode == 200) {
          print('[HomeScreen] pollAnalysis body: ${resp.body}');
          final body = json.decode(resp.body) as Map<String, dynamic>;
          // Consider analysis ready when backend returns ok:true and 'analysis' or 'product' is present
          if ((body['ok'] == true && (body['analysis'] != null || body['product'] != null)) || body['analysis'] != null) {
            final productKey = body['product'] != null ? (body['product']['product_key'] ?? productId) : (body['product_id'] ?? productId);
            final productName = body['product'] != null ? (body['product']['name'] ?? '') : (body['analysis']?['name'] ?? '');
            return {'ok': true, 'product_key': productKey, 'product_name': productName, 'data': body};
          }
        }
      } catch (_) {
        // ignore and retry
      }
      // Update waiting indicator
      setState(() {
        _statusMessage = 'Menunggu analisis selesai...';
      });
      await Future.delayed(const Duration(seconds: 3));
    }
    return {'ok': false, 'error': 'timeout waiting for analysis'};
  }

  Future<void> _submitUrl() async {
    if (_isProcessing) return;
    final raw = _urlCtrl.text.trim();
    if (raw.isEmpty) {
      setState(() {
        _statusMessage = 'URL kosong';
        _statusIsError = true;
      });
      return;
    }
    if (!_isShopeeLink(raw)) {
      setState(() {
        _statusMessage = 'Mohon masukkan link Shopee yang valid';
        _statusIsError = true;
      });
      return;
    }

    setState(() {
      _isProcessing = true;
      _statusMessage = 'Mengirim permintaan ke scraper...';
      _statusIsError = false;
      _progressPercent = null;
    });

    if (ApiConfig.I.demoMode) {
      // Simulate progress for demo
      for (var i = 1; i <= 5; i++) {
        await Future.delayed(const Duration(milliseconds: 300));
        setState(() => _progressPercent = i * 20);
      }
      setState(() {
        _statusMessage = 'Demo: Scraping & analisis selesai (simulasi)';
        _isProcessing = false;
      });
      return;
    }

    final baseUrl = ApiConfig.I.baseUrl;
    try {
      // Ensure we have a guest token so Laravel will associate products with this user
      final token = await AuthService.token;
      if (token == null) {
        setState(() { _statusMessage = 'Membuat akun guest...' ;});
        final okGuest = await AuthService.guestLogin(baseUrl);
        if (!okGuest) {
          setState(() {
            _statusMessage = 'Gagal membuat akun guest. Silakan login manual dari konfigurasi.';
            _statusIsError = true;
            _isProcessing = false;
          });
          return;
        }
      }

      final scrapeUri = Uri.parse('$baseUrl/api/analysis/scrape');
      final body = {'product_url': raw, 'source': 'shopee'};
      final res = await ApiClient.post(scrapeUri, body: body, timeoutSeconds: 30);
      print('[HomeScreen] POST ${scrapeUri.toString()} => ${res.statusCode}: ${res.body}');
      if (res.statusCode != 200 && res.statusCode != 201) {
        setState(() {
          _statusMessage = 'Gagal mengirim permintaan ke backend (${res.statusCode})';
          _statusIsError = true;
          _isProcessing = false;
        });
        return;
      }
      final data = json.decode(res.body) as Map<String, dynamic>;
      print('[HomeScreen] scrape response decoded: $data');
      final jobId = data['job_id'] ?? data['job']?['id'];
      String? productId = (data['product_id'] ?? data['id'] ?? (data['product']?['id']))?.toString();

      if (jobId != null) {
        setState(() {
          _statusMessage = 'Menunggu scraping selesai...';
        });
        final jobRes = await _pollJob(jobId.toString());
        if (!jobRes['ok']) {
          setState(() {
            _statusMessage = 'Scraping gagal: ${jobRes['error'] ?? 'unknown'}';
            _statusIsError = true;
            _isProcessing = false;
          });
          return;
        }
        if (jobRes['productId'] != null) productId = jobRes['productId']?.toString();
      }

      if (productId != null) {
        setState(() {
          _statusMessage = 'Memulai analisis...';
          _progressPercent = null;
        });
        final analyzeUri = Uri.parse('$baseUrl/api/analysis/analyze/$productId');
        final ares = await ApiClient.post(analyzeUri, body: {});
        if (ares.statusCode != 200 && ares.statusCode != 201) {
          // analysis may be queued; show success message anyway but continue to poll
          setState(() {
            _statusMessage = 'Permintaan analisis dikirim (status ${ares.statusCode}). Menunggu hasil...';
          });
        } else {
          setState(() {
            _statusMessage = 'Permintaan analisis dikirim. Menunggu hasil analisis...';
          });
        }

        // Poll for analysis completion and retrieve product info
        final analysisRes = await _pollAnalysis(productId.toString());
        if (!analysisRes['ok']) {
          setState(() {
            _statusMessage = 'Analisis gagal atau timeout: ${analysisRes['error'] ?? 'unknown'}';
            _statusIsError = true;
            _isProcessing = false;
          });
          return;
        }

        final productKey = analysisRes['product_key']?.toString() ?? productId.toString();
        if (!mounted) return;
        // Navigate to Product Detail screen and let it fetch & display the analysis
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(
            builder: (context) => ProductDetailScreen(
              productKey: productKey,
              productName: analysisRes['product_name']?.toString() ?? 'Produk',
            ),
          ),
        );
        return;
      } else {
        setState(() {
          _statusMessage = 'Permintaan terkirim. Backend belum menyediakan product id.';
          _isProcessing = false;
        });
      }
    } catch (e) {
      setState(() {
        _statusMessage = 'Kesalahan: ${e.toString()}';
        _statusIsError = true;
        _isProcessing = false;
      });
    }
  }
}
