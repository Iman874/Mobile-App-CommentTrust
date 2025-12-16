import 'package:flutter/material.dart';

class AppLogo extends StatelessWidget {
  final double size;
  const AppLogo({super.key, this.size = 32});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: Colors.transparent, // let PNG transparency show through
        borderRadius: BorderRadius.circular(4),
      ),
      child: Padding(
        padding: const EdgeInsets.all(2.0), // reduce padding so image fills more
        child: Image.asset(
          'assets/logo/logo_commenttrust.png',
          fit: BoxFit.contain,
          errorBuilder: (context, error, stackTrace) {
            // Fallback to the previous check icon if the asset isn't present yet
            return Icon(Icons.check, color: const Color(0xFF1B4D3E), size: size - 8);
          },
        ),
      ),
    );
  }
}
