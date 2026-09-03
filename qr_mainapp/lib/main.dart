import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:mobile_scanner/mobile_scanner.dart';

void main() {
  runApp(const QrStudentApp());
}

class QrStudentApp extends StatelessWidget {
  const QrStudentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'QR Yoklama',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const ScannerPage(),
    );
  }
}

class ScannerPage extends StatefulWidget {
  const ScannerPage({super.key});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> {
  bool sending = false;
  String message = 'QR kodu okutun';
  String? lastQrData;
  final String backendUrl = 'http://192.168.60.30:5001';

  Future<void> sendQrToBackend(String qrData) async {
    if (sending) return;

    setState(() {
      sending = true;
      message = 'QR backend\'e gönderiliyor...';
    });

    try {
      final response = await http.post(
        Uri.parse('$backendUrl/qr/scan'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'qrData': qrData}),
      );

      if (response.statusCode >= 200 && response.statusCode < 300) {
        setState(() {
          message = 'QR başarıyla backend\'e gönderildi.';
        });
      } else {
        setState(() {
          message = 'Backend hata verdi: ${response.statusCode}';
        });
      }
    } catch (e) {
      setState(() {
        message = 'Backend bağlantısı kurulamadı.';
      });
    } finally {
      setState(() {
        sending = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('QR Yoklama'), centerTitle: true),
      body: Stack(
        children: [
          MobileScanner(
            onDetect: (capture) {
              if (sending) return;

              if (capture.barcodes.isEmpty) return;

              final barcode = capture.barcodes.first;
              final String? value = barcode.rawValue;

              if (value == null || value.isEmpty) return;

              // Aynı QR daha önce gönderildiyse tekrar gönderme.
              if (value == lastQrData) return;

              // Bu QR'ı son okutulan QR olarak kaydet.
              lastQrData = value;

              sendQrToBackend(value);
            },
          ),

          Positioned(
            left: 20,
            right: 20,
            bottom: 30,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withValues(alpha: 0.75),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                message,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
          ),

          if (sending) const Center(child: CircularProgressIndicator()),
        ],
      ),
    );
  }
}
