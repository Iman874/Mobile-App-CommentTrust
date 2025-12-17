import 'package:flutter/material.dart';
import '../widgets/custom_bottom_nav_bar.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
//import '../route/api_config.dart';

class ScanQRScreen extends StatefulWidget {
  final bool embedded;
  const ScanQRScreen({super.key, this.embedded = false});

  @override
  State<ScanQRScreen> createState() => _ScanQRScreenState();
}

class _ScanQRScreenState extends State<ScanQRScreen> {
  int _currentIndex = 2; // Set to scan QR tab
  bool _permissionGranted = false;
  bool _isScanning = false;
  String? _error;

  MobileScannerController? _cameraController;  // will be initialized when permission granted



  @override
  void initState() {
    super.initState();
    _checkPermission();
  }

  Future<void> _checkPermission() async {
    final status = await Permission.camera.status;
    if (status.isGranted) {
      setState(() => _permissionGranted = true);
      // initialize camera controller when permission is granted
      await _initCameraController();
    } else {
      final r = await Permission.camera.request();
      setState(() => _permissionGranted = r.isGranted);
      if (r.isGranted) {
        await _initCameraController();
      }
      if (!r.isGranted) {
        setState(() => _error = 'Izin kamera tidak diberikan. Mohon aktifkan kamera untuk menggunakan fitur pemindaian.');
      }
    }
  }

  bool _isShopeeLink(String url) {
    final u = url.toLowerCase();
    return u.contains('shopee.') || u.contains('shp.ee');
  }

  // Initialize camera controller safely and report errors
  Future<void> _initCameraController() async {
    try {
      _cameraController?.dispose();
      _cameraController = MobileScannerController();
      // optionally start the camera explicitly
      await _cameraController?.start();
      setState(() { _error = null; });
    } catch (e) {
      setState(() { _error = 'Gagal mengakses kamera: ${e.toString()}'; });
    }
  }

  Future<void> _restartCamera() async {
    try {
      await _cameraController?.stop();
      await _cameraController?.start();
      setState(() { _error = null; });
    } catch (e) {
      setState(() { _error = 'Gagal memulai ulang kamera: ${e.toString()}'; });
    }
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
              'Halaman Scan QR',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: Colors.black87,
              ),
            ),
            const SizedBox(height: 20),

            if (!_permissionGranted) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(8), boxShadow: [BoxShadow(color: Color.fromRGBO(0,0,0,0.05), blurRadius: 8, offset: Offset(0,2))]),
                child: Column(children: [
                  Text(_error ?? 'Aplikasi memerlukan izin kamera untuk memindai QR.', style: const TextStyle(color: Colors.black87)),
                  const SizedBox(height: 12),
                  ElevatedButton(onPressed: _checkPermission, child: const Text('Izinkan Kamera'))
                ]),
              ),
            ] else ...[
              Container(
                width: double.infinity,
                height: 400,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey[400]!, width: 2),
                ),
                child: Column(children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: SizedBox(
                      height: 320,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          if (_cameraController != null) MobileScanner(
                            controller: _cameraController!,
                            onDetect: (capture) async {
                              if (_isScanning) return;
                              final barcodes = capture.barcodes;
                              if (barcodes.isEmpty) return;
                              final raw = barcodes.first.rawValue ?? '';
                              if (raw.isEmpty) return;

                              setState(() => _isScanning = true);

                              final url = raw.trim();
                              if (_isShopeeLink(url)) {
                                await _cameraController?.stop();
                                Navigator.pushReplacementNamed(context, '/', arguments: {'scannedUrl': url});
                                return;
                              }

                              await showDialog(context: context, builder: (ctx) => AlertDialog(title: const Text('Hasil Pemindaian'), content: Text(url), actions: [TextButton(onPressed: (){ Navigator.pop(ctx); }, child: const Text('OK'))]));
                              setState(() => _isScanning = false);
                            },
                          ) else Center(child: Text(_error ?? 'Kamera belum tersedia', style: const TextStyle(color: Colors.black54))),
                          // small status overlay
                          Positioned(
                            left: 8,
                            top: 8,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(color: Colors.black45, borderRadius: BorderRadius.circular(6)),
                              child: Text(_cameraController != null ? 'Kamera: Siap' : 'Kamera: Tidak tersedia', style: const TextStyle(color: Colors.white, fontSize: 12)),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Center(
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.link),
                      label: const Text('Tempel / Masukkan URL Produk'),
                      onPressed: _enterUrlManually,
                    ),
                  ),
                ]),
              ),
              const SizedBox(height: 12),
              const Text('Arahkan kamera ke kode QR. Saat URL Shopee terdeteksi, aplikasi akan mengirimkannya ke halaman utama untuk diproses.'),
            ],

            const SizedBox(height: 40),

            // Action Buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1B4D3E),
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: IconButton(
                    onPressed: () async { await _cameraController?.toggleTorch(); },
                    icon: const Icon(Icons.flash_on, color: Colors.white, size: 28),
                  ),
                ),

                // Restart camera button
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1B4D3E),
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: IconButton(
                    onPressed: () async { await _restartCamera(); },
                    icon: const Icon(Icons.refresh, color: Colors.white, size: 28),
                  ),
                ),

                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: const Color(0xFF1B4D3E),
                    borderRadius: BorderRadius.circular(30),
                  ),
                  child: IconButton(
                    onPressed: () {
                      // Gallery QR scan not implemented in this pass
                    },
                    icon: const Icon(
                      Icons.photo_library,
                      color: Colors.white,
                      size: 28,
                    ),
                  ),
                ),
              ],
            ),
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
        title: Row(children: const [SizedBox(width: 8), Text('Comment Trust', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w500))]),
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

  Future<void> _enterUrlManually() async {
    final controller = TextEditingController();
    final val = await showDialog<String?>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Masukkan URL Produk'),
      content: TextField(controller: controller, decoration: const InputDecoration(hintText: 'https://shopee.co.id/...')), 
      actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Batal')), TextButton(onPressed: () => Navigator.pop(ctx, controller.text.trim()), child: const Text('Kirim'))],
    ));

    if (val == null || val.isEmpty) return;
    final url = val.trim();
    if (_isShopeeLink(url)) {
      Navigator.pushReplacementNamed(context, '/', arguments: {'scannedUrl': url});
      return;
    }

    await showDialog(context: context, builder: (ctx) => AlertDialog(title: const Text('URL'), content: Text(url), actions: [TextButton(onPressed: (){ Navigator.pop(ctx); }, child: const Text('OK'))]));
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
        // Already on scan QR screen
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
    _cameraController?.dispose();
    super.dispose();
  }


}
