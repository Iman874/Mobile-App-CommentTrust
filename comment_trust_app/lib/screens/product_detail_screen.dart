import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import 'product_comments_screen.dart';
import 'product_analytics_screen.dart';
import 'tag_comments_screen.dart';
import '../route/api_config.dart';
import '../services/analysis_service.dart';
import '../services/history_service.dart';
import '../services/tag_service.dart';
import '../services/product_service.dart';

class ProductDetailScreen extends StatefulWidget {
  final String productKey;
  final String productName;
  const ProductDetailScreen({super.key, required this.productKey, required this.productName});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  int _currentIndex = 0;
  bool _loading = true;
  String? _error; // human readable error for UI
  Map<String, dynamic>? _analysis;
  Map<String, dynamic>? _product;
  List<Map<String,dynamic>> _tagCounts = [];

  @override
  void initState() {
    super.initState();
    _persistLastViewed();
    _fetch();
  }

  Future<void> _persistLastViewed() async {
    // Store last viewed product locally for History page
    if (widget.productKey.isNotEmpty) {
      await HistoryService.setLastViewed(productKey: widget.productKey, productName: widget.productName);
    }
  }

  Future<void> _fetch() async {
    try {
      await ApiConfig.I.load();
      if (ApiConfig.I.demoMode || widget.productKey.isEmpty) {
        // Demo mode: fabricate minimal analysis placeholders
        if (!mounted) return;
        setState(() {
          _analysis = {
            'metrics': {
              'count_reviews': 0,
              'avg_rating': 0,
              'avg_trust_percent_norm': 0,
              'sentiment_counts': {'positive': 0, 'negative': 0},
              'pros': [],
              'cons': []
            }
          };
          _tagCounts = [];
          _loading = false;
          _error = null;
        });
        return;
      }

      final base = ApiConfig.I.baseUrl;

      // Fetch product details (from Laravel DB) and analysis metrics (may come from Flask or DB)
      final product = await ProductService.fetchProduct(base, widget.productKey);
      final data = await AnalysisService.fetchAnalysis(base, widget.productKey);

      List<Map<String, dynamic>> tags = [];
      try {
        tags = await TagService.fetchTagCounts(base, widget.productKey);
      } catch (e) {
        print('[ProductDetailScreen] Error fetching tags: $e');
        tags = [];
      }

      // Also try to extract any tag information included directly in the product payload
      final prodTags = <Map<String, dynamic>>[];
      try {
        final dynamic p = product;
        if (p is Map) {
          // product.tags or product.meta.tags or product.meta.metrics.tag_stats
          final directTags = p['tags'] ?? p['meta']?['tags'] ?? p['meta']?['metrics']?['tag_stats'];
          if (directTags is List) {
            for (final t in directTags) {
              if (t is Map) {
                final name = (t['name'] ?? t['tag'] ?? t['label'])?.toString() ?? '';
                final count = t['comments_count'] ?? t['count'] ?? 0;
                if (name.isNotEmpty) prodTags.add({'tag': name, 'count': count is num ? count : int.tryParse(count.toString()) ?? 0});
              } else if (t is List && t.length >= 2) {
                prodTags.add({'tag': t[0].toString(), 'count': t[1] is num ? t[1] : int.tryParse(t[1].toString()) ?? 0});
              } else if (t is String) {
                prodTags.add({'tag': t, 'count': 0});
              }
            }
          }
        }
      } catch (e) {
        print('[ProductDetailScreen] Error parsing product tags: $e');
      }

      // Debug: print fetched data so it appears in terminal/console
      print('[ProductDetailScreen] Fetched product: $product');
      print('[ProductDetailScreen] Fetched analysis: $data');
      print('[ProductDetailScreen] Fetched tags (stats): $tags');
      print('[ProductDetailScreen] Fetched tags (product): $prodTags');

      if (!mounted) return;

      // Merge tags from different sources and aggregate counts by tag name
      final Map<String, int> agg = {};
      void addToAgg(Map<String, dynamic> t) {
        final name = (t['tag'] ?? t['name'])?.toString() ?? '';
        if (name.isEmpty) return;
        final cnt = t['count'] is num ? (t['count'] as num).toInt() : int.tryParse(t['count']?.toString() ?? '0') ?? 0;
        agg[name] = (agg[name] ?? 0) + cnt;
      }

      for (final t in tags) addToAgg(t);
      for (final t in prodTags) addToAgg(t);

      final merged = agg.entries.map((e) => {'tag': e.key, 'count': e.value}).toList();

      setState(() {
        // If product provides a better name, use it
        if (product != null && product['name'] != null && product['name'].toString().isNotEmpty) {
          // Update widget title via setState by rebuilding (alternatively you could keep a local productName)
          // We'll keep product name in analysis for convenience
          data?['product_name'] = product['name'];
        }

        _analysis = data ?? _analysis;
        _product = product != null ? Map<String,dynamic>.from(product as Map) : null;
        _tagCounts = merged;
        _loading = false;
        _error = null;
      });
    } catch (e) {
      print('[ProductDetailScreen] Error in _fetch: $e');
      if (!mounted) return;
      setState(() {
        _error = 'Gagal memuat data produk. Coba lagi.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
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
                Icons.check,
                color: Color(0xFF1B4D3E),
                size: 16,
              ),
            ),
            const SizedBox(width: 8),
            const Text(
              'Comment Trust',
              style: TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),

      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Halaman Detail Produk',
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
                    TextButton(onPressed: _fetch, child: const Text('Retry'))
                  ]),
                ),
              ],

              // 🔹 Produk
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
                      'Produk',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: Colors.black87,
                      ),
                    ),
                    const SizedBox(height: 14),
                    const SizedBox(height: 14),
                    // Use logo as product image for now
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
                      (_analysis != null && _analysis!['product_name'] != null && (_analysis!['product_name'] as String).isNotEmpty)
                          ? _analysis!['product_name']
                          : widget.productName,
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
                    SizedBox(
                      width: 160,
                      child: ElevatedButton(
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1B4D3E),
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(6),
                          ),
                        ),
                        onPressed: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => ProductAnalyticsScreen(
                                productKey: widget.productKey,
                                productName: widget.productName,
                              ),
                            ),
                          );
                        },
                        child: const Text(
                          'Lihat Grafik',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              // 🔹 Hasil Review
              _loading ? _buildLoadingCard() : _buildReviewCard(),

              const SizedBox(height: 20),

              // 🔹 Detail Review (menampilkan 4 tag teratas)
              _loading ? _buildLoadingDetail() : _buildDetailReviewSection(context),
              const SizedBox(height: 20),
            ],
          ),
        ),
      ),

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
  Widget _buildLoadingCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Color.fromRGBO(0,0,0,0.1),
            blurRadius: 8,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: const Center(child: SizedBox(height: 40, width: 40, child: CircularProgressIndicator())),
    );
  }

  Widget _buildReviewCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Color.fromRGBO(0,0,0,0.1),
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

  // ========================== Detail Review ==========================
  Widget _buildLoadingDetail() {
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
      child: const SizedBox(height: 40, child: Center(child: CircularProgressIndicator())),
    );
  }

  Widget _buildDetailReviewSection(BuildContext context) {
    // Ambil 4 tag teratas berdasarkan jumlah
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
                        builder: (context) => TagCommentsScreen(productKey: widget.productKey, tag: tagName),
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
              // Arahkan ke layar komentar dengan productKey agar bisa memuat komentar terkait
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ProductCommentsScreen(),
                  settings: RouteSettings(arguments: {'productKey': widget.productKey}),
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


  String _trustText() {
    // Try multiple sources for trust score: metrics -> product payload -> meta.metrics
    double trust = 0.0;
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    if (m != null) {
      final raw = m['avg_trust_percent_norm'] ?? m['avg_trust_percent'] ?? m['avg_trust_score'] ?? m['avg_trust'] ?? 0;
      if (raw is num) trust = raw.toDouble();
      else trust = double.tryParse(raw?.toString() ?? '0') ?? 0.0;
    }

    // fallback to product payload if metrics didn't have a trust value
    if ((trust == 0 || trust.isNaN) && _product != null) {
      final p = _product!;
      final candidate = p['avg_trust_score'] ?? p['meta']?['metrics']?['avg_trust_score'] ?? p['meta']?['metrics']?['avg_trust_percent'];
      if (candidate is num) trust = candidate.toDouble();
      else trust = double.tryParse(candidate?.toString() ?? '0') ?? trust;
    }

    // If trust looks like a 0..1 fraction, convert to percent
    if (trust > 0 && trust <= 1) trust = trust * 100.0;

    final pct = trust.isFinite ? trust.round() : 0;
    return '$pct% Tingkat Kepercayaan Produk';
  }
  String _positiveText() {
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    if (m == null) return '0% Komentar Positif';
    final sent = (m['sentiment_counts'] as Map<String, dynamic>? ?? {});
    final total = (m['count_reviews'] ?? 0).toDouble();
    final pos = (sent['positive'] ?? 0).toDouble();
    final pct = total > 0 ? (pos / total * 100).round() : 0;
    return '$pct% Komentar Positif';
  }
  String _negativeText() {
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    if (m == null) return '0% Komentar Negatif';
    final sent = (m['sentiment_counts'] as Map<String, dynamic>? ?? {});
    final total = (m['count_reviews'] ?? 0).toDouble();
    final neg = (sent['negative'] ?? 0).toDouble();
    final pct = total > 0 ? (neg / total * 100).round() : 0;
    return '$pct% Komentar Negatif';
  }
  String _otherText() {
    // Use 'neutral' sentiment if available rather than 'other' remainder
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    if (m == null) return '0% Komentar Netral';
    final sent = (m['sentiment_counts'] as Map<String, dynamic>? ?? {});
    final total = (m['count_reviews'] ?? 0).toDouble();
    final neu = (sent['neutral'] ?? sent['neu'] ?? 0).toDouble();
    final pct = total > 0 ? (neu / total * 100).round() : 0;
    return '$pct% Komentar Netral';
  }

  String _fakeText() {
    // Prefer metrics values, fallback to product-level fake_rate/count if available
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    final total = (m?['count_reviews'] ?? _product?['count_reviews'] ?? _product?['meta']?['metrics']?['count_reviews'] ?? 0).toDouble();

    dynamic raw = m?['fake_review_count'] ?? m?['fake_rate'];
    if (raw == null || raw == 0) {
      // fallback to product payload
      raw = _product?['fake_rate'] ?? _product?['meta']?['metrics']?['fake_rate'] ?? _product?['meta']?['metrics']?['fake_rate'];
    }

    double pct = 0.0;
    if (raw is num) {
      final val = raw.toDouble();
      if (val > 0 && val <= 1 && total > 0) {
        // treat as rate (e.g., 0.766)
        pct = val * 100.0;
      } else if (val > 1 && total > 0) {
        // treat as count
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
        Navigator.pushReplacementNamed(context, '/history');
        break;
    }
  }
}
