import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../widgets/custom_bottom_nav_bar.dart';

class ProductAnalyticsScreen extends StatefulWidget {
  @override
  _ProductAnalyticsScreenState createState() => _ProductAnalyticsScreenState();
}

class _ProductAnalyticsScreenState extends State<ProductAnalyticsScreen> {
  int _currentIndex = 3;

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

              // ================= Header: Grafik Kepercayaan =================
              _buildSectionHeader('Grafik Kepercayaan produk'),

              // ================= Pie Chart =================
              _buildChartCard(),

              // ================= Header: Komentar Penting =================
              _buildSectionHeaderWithFilter('Komentar Penting'),

              // ================= Komentar Penting =================
              _buildImportantComment(),

              // ================= Media dan Tag =================
              _buildMediaAndTagCard(),

              const SizedBox(height: 80),
            ],
          ),
        ),
      ),

      // ================= Bottom Navigation =================
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

  // ================= Header Section =================
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

  // ================= Header dengan Icon Filter =================
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

  // ================= Grafik Card =================
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
            color: Colors.black.withOpacity(0.08),
            blurRadius: 6,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        children: [
          SizedBox(
            width: 180,
            height: 180,
            child: CustomPaint(painter: PieChartWithLabelPainter()),
          ),
          const SizedBox(height: 16),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildLegendItem('Komentar Baik', const Color(0xFFA5E6D0)),
              const SizedBox(height: 6),
              _buildLegendItem('Komentar Buruk', const Color(0xFFF4C18B)),
              const SizedBox(height: 6),
              _buildLegendItem(
                'Komentar Tidak Berguna',
                const Color(0xFFFF8C82),
              ),
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

  // ================= Komentar Penting =================
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
            color: Colors.black.withOpacity(0.05),
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
                Text(
                  'Andi Saputra',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                ),
                SizedBox(height: 6),
                Text(
                  'Produknya bagus banget, sesuai deskripsi. Packing juga rapi, jadi aman sampai rumah.',
                  style: TextStyle(fontSize: 12, height: 1.4),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ================= Gabungan Media & Tag Card =================
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
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Foto dan video terkait produk',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12),

          Row(
            children: [
              _buildMediaIcon(Icons.image, Colors.grey[400]!),
              const SizedBox(width: 12),
              _buildMediaIcon(Icons.image, Colors.grey[400]!),
              const SizedBox(width: 12),
              _buildMediaIcon(Icons.videocam, Colors.grey[400]!),
            ],
          ),

          const SizedBox(height: 20),

          const Text(
            'Tag pada komentar ini',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w500,
              color: Colors.black87,
            ),
          ),
          const SizedBox(height: 12),

          Row(
            children: [
              _buildTag('Bagus', const Color(0xFF1B4D3E)),
              const SizedBox(width: 8),
              _buildTag('Pengiriman Lambat', const Color(0xFF7D0A0A)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMediaIcon(IconData icon, Color color) {
    return Container(
      width: 45,
      height: 45,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Icon(icon, color: Colors.white, size: 22),
    );
  }

  Widget _buildTag(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(15),
      ),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  // ================= Navigasi =================
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
        break;
      case 4:
        Navigator.pushReplacementNamed(context, '/history');
        break;
    }
  }
}

// ================= Pie Chart Dengan Label Persen =================
class PieChartWithLabelPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..style = PaintingStyle.fill;
    final textPainter = TextPainter(
      textAlign: TextAlign.center,
      textDirection: TextDirection.ltr,
    );

    final data = [
      {'value': 70.0, 'color': const Color(0xFFA5E6D0), 'label': '70%'},
      {'value': 20.0, 'color': const Color(0xFFF4C18B), 'label': '20%'},
      {'value': 10.0, 'color': const Color(0xFFFF8C82), 'label': '10%'},
    ];

    double total = data.fold(0, (sum, item) => sum + (item['value'] as double));
    double startAngle = -math.pi / 2;
    final radius = size.width / 2;

    for (var item in data) {
      final sweepAngle = (item['value'] as double) / total * 2 * math.pi;
      paint.color = item['color'] as Color;

      // Gambar segmen pie
      canvas.drawArc(
        Rect.fromCircle(center: Offset(radius, radius), radius: radius),
        startAngle,
        sweepAngle,
        true,
        paint,
      );

      // Posisi teks persentase
      final midAngle = startAngle + sweepAngle / 2;
      final labelX = radius + (radius / 1.6) * math.cos(midAngle);
      final labelY = radius + (radius / 1.6) * math.sin(midAngle);

      textPainter.text = TextSpan(
        text: item['label'] as String,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: Colors.white,
        ),
      );
      textPainter.layout();
      textPainter.paint(
        canvas,
        Offset(labelX - textPainter.width / 2, labelY - textPainter.height / 2),
      );

      startAngle += sweepAngle;
    }
  }

  @override
  bool shouldRepaint(CustomPainter oldDelegate) => false;
}
