import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import '../services/api_config.dart';
import '../services/tag_service.dart';

class ProductCommentsScreen extends StatefulWidget {
  @override
  _ProductCommentsScreenState createState() => _ProductCommentsScreenState();
}

class _ProductCommentsScreenState extends State<ProductCommentsScreen> {
  int _currentIndex = 3;
  bool _loading = true;
  List<Map<String,dynamic>> _comments = [];
  Map<int, bool> expandedStatus = {};
  String? _productKey; // passed via ModalRoute or inherited context later

  @override
  void initState() {
    super.initState();
    Future.microtask(_init); // defer to ensure context available
  }

  void _init() async {
    // Expect arguments: {productKey:..., tag: optional}
    final args = ModalRoute.of(context)?.settings.arguments;
    if (args is Map && args['productKey'] is String) {
      _productKey = args['productKey'] as String;
    }
    await ApiConfig.I.load();
    if (_productKey != null && _productKey!.isNotEmpty && !ApiConfig.I.demoMode) {
      _comments = await TagService.fetchCommentsByTag(ApiConfig.I.baseUrl, _productKey!, args is Map && args['tag'] is String ? args['tag'] as String : '');
    }
    if (mounted) setState(()=> _loading = false);
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

      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Komentar Penting dari Pembeli',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
              const SizedBox(height: 20),

              // 🔹 Header Section (Komentar + Filter Icon)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1B4D3E),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: const [
                    Text(
                      'Komentar Penting',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    Icon(Icons.filter_list, color: Colors.white, size: 20),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // 🔹 Comments List
              if (_loading) const Center(child: CircularProgressIndicator()) else ...[
                for (int i=0; i<_comments.length; i++) ...[
                  _buildCommentCard(
                    index: i,
                    name: (_comments[i]['username'] ?? 'Anon').toString(),
                    comment: (_comments[i]['comment'] ?? '').toString(),
                    showExpand: true,
                    tags: (_comments[i]['tags'] as List?)?.cast<dynamic>() ?? const [],
                  ),
                  const SizedBox(height:12),
                ]
              ],
              const SizedBox(height: 20),

              // 🔹 Bagian media dan tag dalam satu card
              Container(
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

                    // Media Icons
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

                    // Tags
                    Row(
                      children: [
                        _buildTag('Bagus', const Color(0xFF1B4D3E)),
                        const SizedBox(width: 8),
                        _buildTag('Pengiriman Lambat', const Color(0xFF7D0A0A)),
                      ],
                    ),
                  ],
                ),
              ),
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

  // 🔹 Widget untuk komentar dengan media di-expand dalam card
  Widget _buildCommentCard({
    required int index,
    required String name,
    required String comment,
    bool showExpand = false,
    List<dynamic> tags = const [],
  }) {
    bool isExpanded = expandedStatus[index] ?? false;

    return Container(
      padding: const EdgeInsets.all(14),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: nama + avatar
          Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: Colors.grey[300],
                child: const Icon(Icons.person, color: Colors.grey, size: 20),
              ),
              const SizedBox(width: 12),
              Text(
                name,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Isi komentar
          Text(comment, style: const TextStyle(fontSize:12,color:Colors.black87,height:1.4)),
          if(tags.isNotEmpty) ...[
            const SizedBox(height:8),
            Wrap(spacing:6,runSpacing:6,children:[
              for(final t in tags) _buildTag(t.toString(), const Color(0xFF1B4D3E)),
            ]),
          ],

          if (showExpand) ...[
            const SizedBox(height: 10),
            GestureDetector(
              onTap: () {
                setState(() {
                  expandedStatus[index] = !isExpanded;
                });
              },
              child: Row(
                children: [
                  Icon(
                    isExpanded ? Icons.expand_less : Icons.expand_more,
                    size: 16,
                    color: Colors.grey,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    isExpanded ? 'Sembunyikan Detail' : 'Lihat Lebih Detail',
                    style: const TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ],

          if (isExpanded) ...[
            const SizedBox(height: 10),
            Row(
              children: [
                _buildMediaIcon(Icons.image, Colors.grey[400]!),
                const SizedBox(width: 10),
                _buildMediaIcon(Icons.videocam, Colors.grey[400]!),
              ],
            ),
          ],
        ],
      ),
    );
  }

  // 🔹 Widget untuk ikon media
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

  // 🔹 Widget untuk tag
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

  // 🔹 Navigasi bawah
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
