import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../widgets/custom_bottom_nav_bar.dart';
import '../route/api_config.dart';
import '../services/analysis_service.dart';

class ProductAnalyticsScreen extends StatefulWidget {
  final String productKey;
  final String productName;
  const ProductAnalyticsScreen({super.key, required this.productKey, required this.productName});

  @override
  State<ProductAnalyticsScreen> createState() => _ProductAnalyticsScreenState();
}

class _ProductAnalyticsScreenState extends State<ProductAnalyticsScreen> {
  int _currentIndex = 3;
  bool _loading = true;
  List<PieSeg> _segments = [];
  List<Map<String,dynamic>> _topTags = []; // {tag, count} list for display

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    await ApiConfig.I.load();
    if (ApiConfig.I.demoMode || widget.productKey.isEmpty) {
      _segments = [
        PieSeg(0.7, const Color(0xFFA5E6D0), '70%'),
        PieSeg(0.2, const Color(0xFFF4C18B), '20%'),
        PieSeg(0.1, const Color(0xFFFF8C82), '10%'),
      ];
      setState(() { _loading = false; });
      return;
    }
    final data = await AnalysisService.fetchAnalysis(ApiConfig.I.baseUrl, widget.productKey);
    final metrics = data?['metrics'] as Map<String,dynamic>?;
    if (metrics != null) {
      final sent = (metrics['sentiment_counts'] as Map<String,dynamic>? ?? {});
      final total = (metrics['count_reviews'] ?? 0).toDouble();
      final pos = (sent['positive'] ?? 0).toDouble();
      final neg = (sent['negative'] ?? 0).toDouble();
      final other = math.max(0.0, total - pos - neg);
      final safeTotal = total == 0 ? 1.0 : total;
      _segments = [
        PieSeg(pos / safeTotal, const Color(0xFFA5E6D0), '${safeTotal==0?0:(pos / safeTotal * 100).round()}%'),
        PieSeg(neg / safeTotal, const Color(0xFFF4C18B), '${safeTotal==0?0:(neg / safeTotal * 100).round()}%'),
        PieSeg(other / safeTotal, const Color(0xFFFF8C82), '${safeTotal==0?0:(other / safeTotal * 100).round()}%'),
      ];

      // Extract top tags from metrics most_common_tags (if available)
      final tagsMap = (metrics['most_common_tags'] as Map<String,dynamic>?) ?? {};
      _topTags = tagsMap.entries.map((e) => {'tag': e.key, 'count': e.value}).toList();
    }
    if (mounted) {
      setState(() { _loading = false; });
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
                Icons.comment,
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
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            children: [
              const SizedBox(height: 16),
              _buildSectionHeader('Grafik Kepercayaan produk'),
              _buildChartCard(),
              _buildSectionHeaderWithFilter('Komentar Penting'),
              _buildImportantComment(),
              _buildMediaAndTagCard(),
              const SizedBox(height: 80),
            ],
          ),
        ),
      ),
      bottomNavigationBar: CustomBottomNavBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() { _currentIndex = index; });
          _navigateToScreen(context, index);
        },
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1B4D3E),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        title,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _buildSectionHeaderWithFilter(String title) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF1B4D3E),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.w500,
            ),
          ),
          const Icon(Icons.filter_list, color: Colors.white, size: 20),
        ],
      ),
    );
  }

  Widget _buildChartCard() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        boxShadow: [
          BoxShadow(
            color: Color.fromRGBO(0,0,0,0.08),
            blurRadius: 6,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: _loading ? const Center(child: SizedBox(height: 60,width:60,child: CircularProgressIndicator())) : Column(
        children: [
          SizedBox(
            width: 180,
            height: 180,
            child: CustomPaint(painter: PieChartWithLabelPainter(_segments)),
          ),
          const SizedBox(height: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildLegendItem('Komentar Baik', const Color(0xFFA5E6D0)),
              const SizedBox(height: 6),
              _buildLegendItem('Komentar Buruk', const Color(0xFFF4C18B)),
              const SizedBox(height: 6),
              _buildLegendItem('Komentar Tidak Berguna', const Color(0xFFFF8C82)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLegendItem(String text, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 12,
          height: 12,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 6),
        Text(text, style: const TextStyle(fontSize: 12, color: Colors.black)),
      ],
    );
  }

  Widget _buildImportantComment() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16),
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
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CircleAvatar(
            radius: 20,
            backgroundColor: Color(0xFFE0E0E0),
            child: Icon(Icons.person, color: Colors.grey),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text('Andi Saputra', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                SizedBox(height: 6),
                Text('Produknya bagus banget, sesuai deskripsi. Packing juga rapi, jadi aman sampai rumah.', style: TextStyle(fontSize: 12, height: 1.4)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMediaAndTagCard() {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
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
          const Text('Foto dan video terkait produk', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Colors.black87)),
          const SizedBox(height: 12),
          Row(children: [
            _buildMediaIcon(Icons.image, Colors.grey[400]!),
            const SizedBox(width: 12),
            _buildMediaIcon(Icons.image, Colors.grey[400]!),
            const SizedBox(width: 12),
            _buildMediaIcon(Icons.videocam, Colors.grey[400]!),
          ]),
          const SizedBox(height: 20),
          const Text('Tag pada komentar ini', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Colors.black87)),
          const SizedBox(height: 12),
          _topTags.isEmpty
              ? const Text('Belum ada tag.', style: TextStyle(fontSize: 12, color: Colors.grey))
              : Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: _topTags.map((t) {
                    final tag = (t['tag'] as String?) ?? '-';
                    return _buildTag(tag, const Color(0xFF1B4D3E));
                  }).toList(),
                ),
        ],
      ),
    );
  }

  Widget _buildMediaIcon(IconData icon, Color color) {
    return Container(
      width: 45,
      height: 45,
      decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(8)),
      child: Icon(icon, color: Colors.white, size: 22),
    );
  }

  Widget _buildTag(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(15)),
      child: Text(text, style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w500)),
    );
  }

  void _navigateToScreen(BuildContext context, int index) {
    switch (index) {
      case 0: Navigator.pushReplacementNamed(context, '/'); break;
      case 1: Navigator.pushReplacementNamed(context, '/search'); break;
      case 2: Navigator.pushReplacementNamed(context, '/scan'); break;
      case 3: break;
      case 4: Navigator.pushReplacementNamed(context, '/history'); break;
    }
  }
}

class PieSeg { final double fraction; final Color color; final String label; PieSeg(this.fraction,this.color,this.label); }

class PieChartWithLabelPainter extends CustomPainter {
  final List<PieSeg> segments;
  PieChartWithLabelPainter(this.segments);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    final textPainter = TextPainter(textAlign: TextAlign.center, textDirection: TextDirection.ltr);
    final radius = size.width / 2;
    double startAngle = -math.pi / 2;
    for (var seg in segments) {
      final sweepAngle = seg.fraction * 2 * math.pi;
      paint.color = seg.color;
      canvas.drawArc(Rect.fromCircle(center: Offset(radius, radius), radius: radius), startAngle, sweepAngle, true, paint);
      final midAngle = startAngle + sweepAngle / 2;
      final labelX = radius + (radius / 1.6) * math.cos(midAngle);
      final labelY = radius + (radius / 1.6) * math.sin(midAngle);
      textPainter.text = TextSpan(text: seg.label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white));
      textPainter.layout();
      textPainter.paint(canvas, Offset(labelX - textPainter.width / 2, labelY - textPainter.height / 2));
      startAngle += sweepAngle;
    }
  }
  @override
  bool shouldRepaint(covariant PieChartWithLabelPainter oldDelegate) => oldDelegate.segments != segments;
}
