import 'dart:typed_data';
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
  final MobileScannerController scannerController =
      MobileScannerController(
    returnImage: true,
    detectionSpeed: DetectionSpeed.noDuplicates,
  );

  bool sending = false;

  String message = 'QR kodunu kamera alanının ortasına getirin';

  final String backendUrl = 'http://192.168.60.32:5001';

  Future<void> sendQrImage(Uint8List imageBytes) async {
    if (sending) return;

    setState(() {
      sending = true;
      message = 'QR görüntüsü gönderiliyor...';
    });

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$backendUrl/qr/scan-image'),
      );

      request.files.add(
        http.MultipartFile.fromBytes(
          'qrImage',
          imageBytes,
          filename: 'qr_capture.jpg',
          contentType: http.MediaType('image', 'jpeg'),

        ),
      );

      final response = await request.send();

      if (!mounted) return;

      if (response.statusCode >= 200 &&
          response.statusCode < 300) {
        setState(() {
          message = 'QR görüntüsü gönderildi.';
        });
      } else {
        setState(() {
          message =
              'Backend hata verdi: ${response.statusCode}';
        });
      }
    } catch (e) {
      if (!mounted) return;

      setState(() {
        message = 'Backend bağlantısı kurulamadı.';
      });
    } finally {
      if (mounted) {
        setState(() {
          sending = false;
        });
      }
    }
  }

  @override
  void dispose() {
    scannerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('QR Yoklama'),
        centerTitle: true,
      ),
      body: Stack(
        children: [
          MobileScanner(
            controller: scannerController,
            fit: BoxFit.cover,
            onDetect: (capture) {
              if (sending) return;

              final Uint8List? image = capture.image;

              if (image == null || image.isEmpty) {
                setState(() {
                  message = 'QR görüntüsü alınamadı.';
                });
                return;
              }

              // QR'ın rawValue'sunu KULLANMIYORUZ.
              // Sadece kameranın aldığı gerçek görüntüyü gönderiyoruz.
              sendQrImage(image);
            },
          ),

          Center(
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                border: Border.all(
                  color: Colors.white,
                  width: 3,
                ),
                borderRadius: BorderRadius.circular(16),
              ),
            ),
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
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                ),
              ),
            ),
          ),

          if (sending)
            const Center(
              child: CircularProgressIndicator(),
            ),
        ],
      ),
    );
  }
}