import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';

class ProductCommentsScreen extends StatefulWidget {
  @override
  _ProductCommentsScreenState createState() => _ProductCommentsScreenState();
}

class _ProductCommentsScreenState extends State<ProductCommentsScreen> {
  int _currentIndex = 3;

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
                'Halaman',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 20),

              // Comments Dropdown Section
              Container(
                padding: EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Color(0xFF1B4D3E),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      'Komentar Penting',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    Icon(
                      Icons.keyboard_arrow_down,
                      color: Colors.white,
                      size: 20,
                    ),
                  ],
                ),
              ),

              SizedBox(height: 16),

              // Comments List
              _buildCommentCard(
                'Andi Saputra',
                'Produknya cukup bagus, sesuai deskripsi. Packing juga rapi, jadi aman sampai rumah',
              ),
              SizedBox(height: 12),

              _buildCommentCard(
                'Nama pengomentar',
                'Contoh komentar, contoh komentar, contoh komentar, contoh komentar',
                showExpand: true,
              ),
              SizedBox(height: 12),

              _buildCommentCard(
                'Nama pengomentar',
                'Contoh komentar, contoh komentar, contoh komentar, contoh komentar',
                showExpand: true,
              ),
              SizedBox(height: 12),

              _buildCommentCard(
                'Nama pengomentar',
                'Contoh komentar, contoh komentar, contoh komentar, contoh komentar',
              ),

              SizedBox(height: 20),

              // Media Section
              Text(
                'Foto dan video terkait produk',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 12),

              // Media Icons
              Row(
                children: [
                  _buildMediaIcon(Icons.image, Colors.grey[400]!),
                  SizedBox(width: 12),
                  _buildMediaIcon(Icons.image, Colors.grey[400]!),
                  SizedBox(width: 12),
                  _buildMediaIcon(Icons.videocam, Colors.grey[400]!),
                ],
              ),

              SizedBox(height: 20),

              // Tags Section
              Text(
                'Tag pada komentar ini',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 12),

              // Tags
              Row(
                children: [
                  _buildTag('Bagus', Color(0xFF1B4D3E)),
                  SizedBox(width: 8),
                  _buildTag('Pengiriman Lambat', Colors.red),
                ],
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

  Widget _buildCommentCard(
    String name,
    String comment, {
    bool showExpand = false,
  }) {
    return Container(
      padding: EdgeInsets.all(12),
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
          Row(
            children: [
              CircleAvatar(
                radius: 20,
                backgroundColor: Colors.grey[300],
                child: Icon(Icons.person, color: Colors.grey[600], size: 20),
              ),
              SizedBox(width: 12),
              Text(
                name,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: Colors.black87,
                ),
              ),
            ],
          ),
          SizedBox(height: 8),
          Text(
            comment,
            style: TextStyle(fontSize: 12, color: Colors.black87, height: 1.4),
          ),
          if (showExpand) ...[
            SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.expand_more, size: 16, color: Colors.grey[600]),
                SizedBox(width: 4),
                Text(
                  'Lihat Lebih detail',
                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildMediaIcon(IconData icon, Color color) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Icon(icon, color: Colors.white, size: 20),
    );
  }

  Widget _buildTag(String text, Color color) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(15),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: Colors.white,
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
