import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import 'product_detail_screen.dart';
import '../route/api_config.dart';
import '../data-dummy/dummy_data_loader.dart';
import '../services/product_service.dart';

class ReviewsScreen extends StatefulWidget {
  final bool embedded;
  const ReviewsScreen({super.key, this.embedded = false});

  @override
  State<ReviewsScreen> createState() => _ReviewsScreenState();
}

class _ReviewsScreenState extends State<ReviewsScreen> {
  int _currentIndex = 3; // tab aktif: ulasan

  List<Map<String, dynamic>> _latestReviews = [];
  List<Map<String, dynamic>> _previousReviews = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    await ApiConfig.I.load();
    if (ApiConfig.I.demoMode) {
      final all = await DummyDataLoader.loadProducts();
      final latest = all.take(2).toList();
      final prev = all.skip(2).take(2).toList();
      if (!mounted) return;
      setState(() {
        _latestReviews = latest;
        _previousReviews = prev;
      });
      return;
    }
    final baseUrl = ApiConfig.I.baseUrl;
    final data = await ProductService.fetchLatest(baseUrl, limit: 6);
    // Map to UI fields, keep placeholder image assets
    final mapped = data.map<Map<String, dynamic>>((p) => {
      'image': 'assets/logo/logo_commenttrust.png',
      'name': p['name'] ?? 'Unknown Product',
      'rating': (p['avg_rating'] ?? 0).toDouble(),
    }).toList();
    if (!mounted) return;
    setState(() {
      _latestReviews = mapped.take(2).toList();
      _previousReviews = mapped.skip(2).take(2).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    final content = SingleChildScrollView(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Halaman Ulasan Produk',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 20),

            _buildReviewSection('Review Terbaru', _latestReviews),
            const SizedBox(height: 24),
            _buildReviewSection('Review Sebelumnya', _previousReviews),
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

  // 🔸 Bagian tampilan review
  Widget _buildReviewSection(String title, List<Map<String, dynamic>> reviews) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1B4D3E),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 🔹 Judul
          Padding(
            padding: const EdgeInsets.all(16),
            child: Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),

          // 🔹 List review
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Column(
              children: reviews.map((review) {
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
                      // Gambar produk (diperkecil)
                      SizedBox(
                        width: 65,
                        height: 65,
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.asset(
                            review['image'],
                            fit: BoxFit.cover,
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),

                      // Info produk
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              review['name'],
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
                                  children: List.generate(5, (index) {
                                    return const Icon(
                                      Icons.star,
                                      size: 14,
                                      color: Colors.orange,
                                    );
                                  }),
                                ),
                                const SizedBox(width: 6),
                                Text(
                                  '${review['rating'].toStringAsFixed(1)}/5.0',
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

                      // Tombol Detail
                      GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => ProductDetailScreen(
                                productKey: review['product_key']?.toString() ?? '',
                                productName: review['name']?.toString() ?? 'Produk',
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
              }).toList(),
            ),
          ),

          // 🔹 Tombol "Show more..."
          Padding(
            padding: const EdgeInsets.only(bottom: 20, top: 4),
            child: const Center(
              child: Text(
                'Show more...',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  // 🔸 Navigasi ke tab lain
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
