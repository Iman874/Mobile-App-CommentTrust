import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'screens/config_screen.dart';
import 'screens/search_screen.dart';
import 'screens/scan_qr_screen.dart';
import 'screens/reviews_screen.dart';
import 'screens/history_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Comment Trust',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(primarySwatch: Colors.green, fontFamily: 'Roboto'),
      initialRoute: '/config',
      routes: {
        '/': (context) => HomeScreen(),
        '/config': (context) => const ConfigScreen(),
        '/search': (context) => SearchScreen(),
        '/scan': (context) => ScanQRScreen(),
        '/reviews': (context) => ReviewsScreen(),
        '/history': (context) => HistoryScreen(),
      },
    );
  }
}
