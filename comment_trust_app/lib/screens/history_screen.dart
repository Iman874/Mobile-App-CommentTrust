import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import 'product_comments_screen.dart';
import 'product_analytics_screen.dart';
import '../services/history_service.dart';
import '../data-dummy/dummy_data_loader.dart';
import '../route/api_config.dart';
import '../services/auth_service.dart';
import '../services/product_service.dart';
import '../services/analysis_service.dart';
import '../services/tag_service.dart';
import 'tag_comments_screen.dart';

class HistoryScreen extends StatefulWidget {
  final bool embedded;
  const HistoryScreen({super.key, this.embedded = false});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  int _currentIndex = 4;
  String? _lastProductKey;
  String? _lastProductName;
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _analysis;
  Map<String, dynamic>? _product;
  List<Map<String, dynamic>> _tagCounts = [];

  @override
  void initState() {
    super.initState();
    _loadLastViewed();
  }

  Future<void> _loadLastViewed() async {
    await ApiConfig.I.load();
    final last = await HistoryService.getLastViewed();

    // If we have a saved last viewed product, use it as the initial state
    if (last != null) {
      _lastProductKey = last['productKey'];
      _lastProductName = last['productName'];
    }

    // Try to fetch the most recently scraped product from backend and prefer it
    try {
      final token = await AuthService.token;
      // Ensure we have at least a guest token so backend can return products
      if ((token == null || token.isEmpty) && !ApiConfig.I.demoMode) {
        await AuthService.guestLogin(ApiConfig.I.baseUrl);
      }

      if (!ApiConfig.I.demoMode) {
        final base = ApiConfig.I.baseUrl;
        final remote = await ProductService.fetchLatest(base, limit: 1);
        if (remote.isNotEmpty) {
        final r = remote.first;
        final remoteKey = (r['product_key'] ?? r['id'] ?? r['product_id'])?.toString() ?? '';
        final remoteName = (r['name'] ?? r['title'])?.toString() ?? remoteKey;

        // If there is no saved last or the remote product is newer/different, use remote product
        if (remoteKey.isNotEmpty) {
          try {
            // Fetch full product and analysis like ProductDetailScreen
            final product = await ProductService.fetchProduct(base, remoteKey);
            final data = await AnalysisService.fetchAnalysis(base, remoteKey);
            final tags = await TagService.fetchTagCounts(base, remoteKey);

            // persist latest product as last viewed
            await HistoryService.setLastViewed(productKey: remoteKey, productName: remoteName);

            if (!mounted) return;
            setState(() {
              _lastProductKey = remoteKey;
              _lastProductName = remoteName;
              _product = product != null ? Map<String,dynamic>.from(product as Map) : null;
              _analysis = data ?? _analysis;
              _tagCounts = tags;
              _loading = false;
              _error = null;
            });
            return;
          } catch (e) {
            print('[HistoryScreen] Error fetching remote product details: $e');
            // fallback to saved or demo behavior below
          }
        }
      }
      }
    } catch (e) {
      print('[HistoryScreen] Error fetching latest product: $e');
      // ignore and fallback to saved/dummy state
    }

    // If we're here, use saved last (if any) or demo fallback
    if (last == null) {
      final token = await AuthService.token;
      if (ApiConfig.I.demoMode && (token == null || token.isEmpty)) {
        try {
          final list = await DummyDataLoader.loadProducts();
          if (list.isNotEmpty) {
            final first = list.first;
            if (!mounted) return;
            setState(() {
              _lastProductKey = first['product_key']?.toString() ?? '';
              _lastProductName = first['name']?.toString() ?? 'Produk contoh';
              _loading = false;
            });
            return;
          }
        } catch (_) {}
      }

      if (!mounted) return;
      setState(() {
        _lastProductKey = null;
        _lastProductName = null;
        _loading = false;
      });
      return;
    }

    // There is a saved last viewed product - populate state
    if (!mounted) return;
    setState(() {
      _lastProductKey = last['productKey'];
      _lastProductName = last['productName'];
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final content = _loading
        ? const Center(child: CircularProgressIndicator())
        : SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

              const Text(
                'Halaman Histori Produk',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 20),

              // Error banner
              if (_error != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(color: Colors.red[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: Colors.red[100]!)),
                  child: Row(children: [
                    Expanded(child: Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 13))),
                    TextButton(onPressed: _loadLastViewed, child: const Text('Retry'))
                  ]),
                ),
              ],

              // 🔹 Produk dalam histori
              if (_lastProductName == null)
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: Color.fromRGBO(0,0,0,0.05),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Center(
                    child: Text(
                      'Belum ada histori',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Colors.grey[700],
                      ),
                    ),
                  ),
                )
              else
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: Color.fromRGBO(0,0,0,0.05),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const Text(
                        'Produk dalam Histori',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: Colors.black87,
                        ),
                      ),
                      const SizedBox(height: 14),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.asset(
                          'assets/logo/logo_commenttrust.png',
                          width: 110,
                          height: 80,
                          fit: BoxFit.contain,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _lastProductName ?? 'Belum ada produk yang dilihat',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: Colors.black87,
                        ),
                        textAlign: TextAlign.center,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      const SizedBox(height: 12),

                      InkWell(
                        onTap: () {
                          if (_lastProductKey != null && _lastProductName != null && _lastProductKey!.isNotEmpty) {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) => ProductAnalyticsScreen(
                                  productKey: _lastProductKey!,
                                  productName: _lastProductName!,
                                ),
                              ),
                            );
                          } else {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Belum ada produk yang dilihat. Silakan pilih produk terlebih dahulu.')),
                            );
                          }
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            border: Border.all(color: Colors.grey[400]!),
                            borderRadius: BorderRadius.circular(6),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.show_chart, size: 16),
                              const SizedBox(width: 4),
                              Text(
                                (_lastProductKey != null && _lastProductKey!.isNotEmpty) ? 'Lihat Grafik' : 'Belum ada histori',
                                style: const TextStyle(fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

              if (_lastProductName != null) ...[
                const SizedBox(height: 20),

                // 🔹 Hasil Review (versi final)
                _buildReviewCard(),

                const SizedBox(height: 20),

                // 🔹 Detail Review (dynamic tags)
                _buildDetailReviewSection(context),
              ],
            ],
          ),
        ),
      );

    if (widget.embedded) return content;

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        backgroundColor: const Color(0xFF1B4D3E),
        elevation: 0,
        title: Row(
          children: [
            Container(
              width: 24,
              height: 24,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Icon(
                Icons.history,
                color: Color(0xFF1B4D3E),
                size: 16,
              ),
            ),
            const SizedBox(width: 8),
            const Text(
              'Comment Trust - History',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
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

  // ========================== Hasil Review ==========================
  Widget _buildReviewCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Color.fromRGBO(0,0,0,0.05),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        children: [
          const Text(
            'Hasil Review',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w700,
              color: Colors.black,
            ),
          ),
          const SizedBox(height: 16),

          _buildReviewItem(
            icon: Icons.verified,
            text: _trustText(),
            color: const Color(0xFF1B4D3E),
          ),
          const SizedBox(height: 10),
          _buildReviewItem(
            icon: Icons.thumb_up_alt,
            text: _positiveText(),
            color: const Color(0xFF157F1F),
          ),
          const SizedBox(height: 10),
          _buildReviewItem(
            icon: Icons.thumb_down_alt,
            text: _negativeText(),
            color: const Color(0xFF7D0A0A),
          ),
          const SizedBox(height: 10),
          _buildReviewItem(
            icon: Icons.circle_outlined,
            text: _otherText(),
            color: const Color(0xFF9E9E9E),
          ),
          // Only show 'Komentar Mencurigakan' when computed percentage > 0
          if (int.tryParse(_fakeText().replaceAll(RegExp('[^0-9]'), '')) != null && int.tryParse(_fakeText().replaceAll(RegExp('[^0-9]'), ''))! > 0) ...[
            const SizedBox(height: 10),
            _buildReviewItem(
              icon: Icons.report_problem,
              text: _fakeText(),
              color: const Color(0xFFFF9800),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildReviewItem({
    required IconData icon,
    required String text,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(25),
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.white, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _trustText() {
    double trust = 0.0;
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    if (m != null) {
      final raw = m['avg_trust_percent_norm'] ?? m['avg_trust_percent'] ?? m['avg_trust_score'] ?? m['avg_trust'] ?? 0;
      if (raw is num) trust = raw.toDouble();
      else trust = double.tryParse(raw?.toString() ?? '0') ?? 0.0;
    }

    if ((trust == 0 || trust.isNaN) && _product != null) {
      final p = _product!;
      final candidate = p['avg_trust_score'] ?? p['meta']?['metrics']?['avg_trust_score'] ?? p['meta']?['metrics']?['avg_trust_percent'];
      if (candidate is num) trust = candidate.toDouble();
      else trust = double.tryParse(candidate?.toString() ?? '0') ?? trust;
    }

    if (trust > 0 && trust <= 1) trust = trust * 100.0;
    final pct = trust.isFinite ? trust.round() : 0;
    return '$pct% Tingkat Kepercayaan Produk';
  }

  String _positiveText() {
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    final sent = (m?['sentiment_counts'] as Map<String, dynamic>? ?? {});
    final total = (m?['count_reviews'] ?? _product?['count_reviews'] ?? 0).toDouble();
    final pos = (sent['positive'] ?? 0).toDouble();
    final pct = total > 0 ? (pos / total * 100).round() : 0;
    return '$pct% Komentar Positif';
  }

  String _negativeText() {
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    final sent = (m?['sentiment_counts'] as Map<String, dynamic>? ?? {});
    final total = (m?['count_reviews'] ?? _product?['count_reviews'] ?? 0).toDouble();
    final neg = (sent['negative'] ?? 0).toDouble();
    final pct = total > 0 ? (neg / total * 100).round() : 0;
    return '$pct% Komentar Negatif';
  }

  String _otherText() {
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    final sent = (m?['sentiment_counts'] as Map<String, dynamic>? ?? {});
    final total = (m?['count_reviews'] ?? _product?['count_reviews'] ?? 0).toDouble();
    final neu = (sent['neutral'] ?? sent['neu'] ?? 0).toDouble();
    final pct = total > 0 ? (neu / total * 100).round() : 0;
    return '$pct% Komentar Netral';
  }

  String _fakeText() {
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    final total = (m?['count_reviews'] ?? _product?['count_reviews'] ?? _product?['meta']?['metrics']?['count_reviews'] ?? 0).toDouble();

    dynamic raw = m?['fake_review_count'] ?? m?['fake_rate'];
    if (raw == null || raw == 0) {
      raw = _product?['fake_rate'] ?? _product?['meta']?['metrics']?['fake_rate'];
    }

    double pct = 0.0;
    if (raw is num) {
      final val = raw.toDouble();
      if (val > 0 && val <= 1 && total > 0) {
        pct = val * 100.0;
      } else if (val > 1 && total > 0) {
        pct = (val / total) * 100.0;
      }
    } else {
      final parsed = double.tryParse(raw?.toString() ?? '0') ?? 0.0;
      if (parsed > 0 && parsed <= 1 && total > 0) pct = parsed * 100.0;
      else if (parsed > 1 && total > 0) pct = (parsed / total) * 100.0;
    }
    final rounded = pct.isFinite ? pct.round() : 0;
    return '$rounded% Komentar Mencurigakan';
  }

  // ========================== Detail Review ==========================
  Widget _buildDetailReviewSection(BuildContext context) {
    final topTags = List<Map<String, dynamic>>.from(_tagCounts)
      ..sort((a, b) => ((b['count'] ?? 0) as num).compareTo((a['count'] ?? 0) as num));
    final visible = topTags.take(4).toList();

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Color.fromRGBO(0,0,0,0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Detail Review',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 16),
          if (visible.isEmpty)
            const Text('Belum ada tag.', style: TextStyle(fontSize: 12, color: Colors.grey))
          else ...[
            for (final t in visible) ...[
              GestureDetector(
                onTap: () {
                  final tagName = (t['tag'] ?? t['name'])?.toString() ?? '';
                  if (tagName.isNotEmpty) {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => TagCommentsScreen(productKey: _lastProductKey ?? '', tag: tagName),
                      ),
                    );
                  }
                },
                child: _buildReviewDetailItem(
                  ((t['tag'] ?? t['name']) as String?) ?? '-',
                  '(${(t['count'] ?? 0)})',
                ),
              ),
              const SizedBox(height: 8),
            ],
          ],
          const SizedBox(height: 12),
          InkWell(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ProductCommentsScreen(),
                  settings: RouteSettings(arguments: {'productKey': _lastProductKey ?? ''}),
                ),
              );
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey[400]!),
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.expand_more, size: 16),
                  SizedBox(width: 4),
                  Text(
                    'Lihat lebih banyak tag',
                    style: TextStyle(fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReviewDetailItem(String title, String count) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        children: [
          Expanded(
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: Colors.black87,
              ),
            ),
          ),
          Text(count, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
        ],
      ),
    );
  }

  // ========================== Navigasi ==========================
  void _navigateToScreen(BuildContext context, int index) {
    switch (index) {
      case 0:
        Navigator.pushReplacementNamed(context, '/');
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
        break;
    }
  }
}
