import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import 'product_comments_screen.dart';
import 'product_analytics_screen.dart';
import '../route/api_config.dart';
import '../services/analysis_service.dart';
import '../services/history_service.dart';
import '../services/tag_service.dart';

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
  Map<String, dynamic>? _analysis;
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
    await ApiConfig.I.load();
    if (ApiConfig.I.demoMode || widget.productKey.isEmpty) {
      // Demo mode: fabricate minimal analysis placeholders
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
        _loading = false;
      });
      return;
    }
    final base = ApiConfig.I.baseUrl;
    final data = await AnalysisService.fetchAnalysis(base, widget.productKey);
    final tags = await TagService.fetchTagCounts(base, widget.productKey);
    if (!mounted) return;
    setState(() {
      _analysis = data;
      _tagCounts = tags;
      _loading = false;
    });
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
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.asset(
                        'assets/images/img1.jpg',
                        width: 110,
                        height: 80,
                        fit: BoxFit.cover,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      widget.productName,
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
            icon: Icons.cancel,
            text: _otherText(),
            color: const Color(0xFF9E9E9E),
          ),
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
              _buildReviewDetailItem(
                (t['tag'] as String?) ?? '-',
                '(${(t['count'] ?? 0)})',
              ),
              const SizedBox(height: 8),
            ],
          ],
          const SizedBox(height: 12),
          InkWell(
            onTap: () {
              // Arahkan ke layar komentar dengan filter tag jika diperlukan
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ProductCommentsScreen(),
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
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    if (m == null) return '0% Tingkat Kepercayaan Produk';
    final trustNorm = (m['avg_trust_percent_norm'] ?? 0).toDouble();
    final pct = trustNorm.round();
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
    final m = _analysis?['metrics'] as Map<String, dynamic>?;
    if (m == null) return '0% Komentar Tidak Relevan';
    final sent = (m['sentiment_counts'] as Map<String, dynamic>? ?? {});
    final total = (m['count_reviews'] ?? 0).toDouble();
    final pos = (sent['positive'] ?? 0).toDouble();
    final neg = (sent['negative'] ?? 0).toDouble();
    final otherCount = total - pos - neg;
    final pct = total > 0 ? (otherCount / total * 100).round() : 0;
    return '$pct% Komentar Tidak Relevan';
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
