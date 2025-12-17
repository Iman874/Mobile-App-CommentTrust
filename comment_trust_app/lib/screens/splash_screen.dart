import 'package:flutter/material.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  double _opacity = 1.0;

  @override
  void initState() {
    super.initState();
    // Start the fade animation immediately after the first frame so
    // AnimatedOpacity will animate the transition.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      setState(() => _opacity = 0.0);
      // After 1.5 seconds (the fade duration), navigate to the config screen.
      Future.delayed(const Duration(milliseconds: 1500), () {
        if (!mounted) return;
        Navigator.pushReplacementNamed(context, '/config');
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color.fromARGB(255, 255, 255, 255),
      body: Center(
        child: AnimatedOpacity(
          opacity: _opacity,
          duration: const Duration(milliseconds: 1500),
          curve: Curves.easeInOut,
          child: Image.asset(
            'assets/logo/logo_commenttrust.png',
            width: 200,
            height: 200,
            fit: BoxFit.contain,            errorBuilder: (ctx,err,stack) => Column(
              mainAxisSize: MainAxisSize.min,
              children: const [
                Icon(Icons.broken_image, size: 72, color: Colors.grey),
                SizedBox(height: 8),
                Text('Logo tidak ditemukan', style: TextStyle(color: Colors.grey))
              ],
            ),          ),
        ),
      ),
    );
  }
}
