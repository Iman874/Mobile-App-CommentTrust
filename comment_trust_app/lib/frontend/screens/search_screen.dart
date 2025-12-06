import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import 'product_detail_screen.dart';
import '../services/api_config.dart';
import '../services/dummy_data_loader.dart';
import '../services/product_service.dart';

class SearchScreen extends StatefulWidget {
  @override
  _SearchScreenState createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  int _currentIndex = 1; // Set to search tab
  final TextEditingController _searchController = TextEditingController();
  List<Map<String,dynamic>> _allProducts = [];
  List<Map<String,dynamic>> _visibleProducts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _initLoad();
    _searchController.addListener(() => _filter(_searchController.text));
  }

  Future<void> _initLoad() async {
    await ApiConfig.I.load();
    if (ApiConfig.I.demoMode) {
      final list = await DummyDataLoader.loadProducts();
      _allProducts = list.map((p) => {
        'product_key': p['name'], // placeholder key
        'name': p['name'],
        'avg_rating': p['rating'],
        'image': p['image'],
      }).toList();
    } else {
      final base = ApiConfig.I.baseUrl;
      final remote = await ProductService.fetchAll(base);
      _allProducts = remote.map((p) => {
        'product_key': p['product_key'],
        'name': p['name'] ?? 'Produk Tanpa Nama',
        'avg_rating': (p['avg_rating'] ?? 0).toDouble(),
        'image': 'assets/images/img1.jpg',
      }).toList();
    }
    _visibleProducts = _allProducts.take(5).toList();
    if (!mounted) return;
    setState(() { _loading = false; });
  }

  void _filter(String q) {
    if (q.trim().isEmpty) {
      setState(() { _visibleProducts = _allProducts.take(5).toList(); });
      return;
    }
    final query = q.toLowerCase();
    final scored = _allProducts.map((p) {
      final name = (p['name'] ?? '').toString().toLowerCase();
      double score;
      if (name.contains(query)) {
        score = 1.0;
      } else {
        score = _similarity(name, query);
      }
      return {'data': p, 'score': score};
    }).where((e) => (e['score'] as double?) != null && (e['score'] as double) >= 0.4).toList();
    scored.sort((a,b) => (b['score'] as double).compareTo(a['score'] as double));
    setState(() { _visibleProducts = scored.map((e)=> e['data'] as Map<String,dynamic>).take(5).toList(); });
  }

  double _similarity(String a, String b) {
    final dist = _levenshtein(a, b);
    final maxLen = a.length > b.length ? a.length : b.length;
    if (maxLen == 0) return 0.0;
    return 1.0 - dist / maxLen;
  }

  int _levenshtein(String s, String t) {
    if (s == t) return 0;
    if (s.isEmpty) return t.length;
    if (t.isEmpty) return s.length;
    final rows = s.length + 1;
    final cols = t.length + 1;
    final matrix = List.generate(rows, (_) => List<int>.filled(cols, 0));
    for (var i=0;i<rows;i++) { matrix[i][0] = i; }
    for (var j=0;j<cols;j++) { matrix[0][j] = j; }
    for (var i=1;i<rows;i++) {
      for (var j=1;j<cols;j++) {
        final cost = s[i-1] == t[j-1] ? 0 : 1;
        matrix[i][j] = [
          matrix[i-1][j] + 1,
          matrix[i][j-1] + 1,
          matrix[i-1][j-1] + cost,
        ].reduce((a,b)=> a < b ? a : b);
      }
    }
    return matrix[rows-1][cols-1];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        backgroundColor: Color(0xFF1B4D3E),
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
              child: Icon(Icons.check, color: Color(0xFF1B4D3E), size: 16),
            ),
            SizedBox(width: 8),
            Text(
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
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Title
              Text(
                'Halaman Pencarian Produk',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 20),

              // Search Section
              Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Masukkan Link Produk',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                        color: Colors.black87,
                      ),
                    ),
                    SizedBox(height: 12),
                    Container(
                      decoration: BoxDecoration(
                        color: Colors.grey[50],
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: TextField(
                        controller: _searchController,
                        decoration: InputDecoration(
                          hintText: 'Tempel disini',
                          hintStyle: TextStyle(color: Colors.grey[500]),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                          suffixIcon: Icon(
                            Icons.search,
                            color: Colors.grey[600],
                          ),
                        ),
                      ),
                    ),
                    SizedBox(height: 16),

                    // Filter Buttons
                    Row(
                      children: [
                        _buildFilterButton('Kata Kunci', true),
                        SizedBox(width: 8),
                        _buildFilterButton('Handphone', false),
                        SizedBox(width: 8),
                        _buildFilterButton('Laptop', false),
                      ],
                    ),
                  ],
                ),
              ),

              SizedBox(height: 24),

              // Results Section
              Text(
                'Hasil Pencarian',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 12),

              if (_loading)
                Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
              else ..._visibleProducts.map((p) => Container(
                margin: EdgeInsets.only(bottom: 12),
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(8),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 10,
                      offset: Offset(0, 2),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.asset(
                        p['image'] ?? 'assets/images/img1.jpg',
                        width: 60,
                        height: 60,
                        fit: BoxFit.cover,
                      ),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            p['name'] ?? 'Produk',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                              color: Colors.black87,
                            ),
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                          ),
                          SizedBox(height: 8),
                          Row(
                            children: [
                              Row(
                                children: List.generate(5, (index) {
                                  return Icon(
                                    Icons.star,
                                    size: 16,
                                    color: Colors.orange,
                                  );
                                }),
                              ),
                              SizedBox(width: 8),
                              Text(
                                '${(p['avg_rating'] ?? 0).toStringAsFixed(1)}/5.0',
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
                    InkWell(
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ProductDetailScreen(
                              productKey: p['product_key']?.toString() ?? '',
                              productName: p['name']?.toString() ?? 'Produk',
                            ),
                          ),
                        );
                      },
                      borderRadius: BorderRadius.circular(20),
                      child: Container(
                        padding: EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 8,
                        ),
                        decoration: BoxDecoration(
                          color: Color(0xFF1B4D3E),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          'Detail',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ))
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

  Widget _buildFilterButton(String text, bool isActive) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: isActive ? Color(0xFF1B4D3E) : Colors.grey[200],
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: isActive ? Colors.white : Colors.grey[700],
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  void _navigateToScreen(BuildContext context, int index) {
    switch (index) {
      case 0:
        Navigator.pushReplacementNamed(context, '/');
        break;
      case 1:
        // Already on search screen
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

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}
