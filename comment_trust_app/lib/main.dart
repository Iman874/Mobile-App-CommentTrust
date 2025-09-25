import 'package:flutter/material.dart';
import 'frontend/screens/home_screen.dart';
import 'frontend/screens/search_screen.dart';
import 'frontend/screens/scan_qr_screen.dart';
import 'frontend/screens/reviews_screen.dart';
import 'frontend/screens/history_screen.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Comment Trust App',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(primarySwatch: Colors.green, fontFamily: 'Roboto'),
      initialRoute: '/',
      routes: {
        '/': (context) => HomeScreen(),
        '/search': (context) => SearchScreen(),
        '/scan': (context) => ScanQRScreen(),
        '/reviews': (context) => ReviewsScreen(),
        '/history': (context) => HistoryScreen(),
      },
    );
  }
}
