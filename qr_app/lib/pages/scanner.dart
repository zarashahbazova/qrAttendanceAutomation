import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_client.dart';

class ScannerPage extends StatefulWidget {
  const ScannerPage({super.key});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> {
  final MobileScannerController controller = MobileScannerController();

  final ApiClient apiClient = ApiClient();

  bool processing = false;

  Future<void> processQr(String qrToken) async {
    if (processing) return;

    processing = true;

    try {
      final prefs = await SharedPreferences.getInstance();

      final token = prefs.getString('token');

      if (token == null) {
        throw Exception('Oturum bulunamadı.');
      }

      final message = await apiClient.joinAttendance(token, qrToken);

      if (!mounted) return;

      await controller.stop();

      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) {
          return AlertDialog(
            title: const Text('Yoklama'),
            content: Text(message),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context);

                  controller.start();

                  processing = false;

                  if (mounted) {
                    setState(() {});
                  }
                },
                child: const Text('Tamam'),
              ),
            ],
          );
        },
      );
    } catch (e) {
      processing = false;

      if (!mounted) return;

      String message = e.toString().replaceFirst('Exception: ', '');

      // ==========================================
      // SÜRESİ GEÇMİŞ QR
      // ==========================================

      if (message.contains('QR kodunun süresi dolmuş')) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'QR kodunun süresi dolmuş. '
              'Güncel QR kodu okutun.',
            ),
            duration: Duration(seconds: 2),
          ),
        );

        // Kamera açık kalıyor.
        // Öğrenci yeni QR'ı direkt okutabilir.

        return;
      }

      // ==========================================
      // DİĞER HATALAR
      // ==========================================

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('QR Tara'), centerTitle: true),

      body: MobileScanner(
        controller: controller,

        onDetect: (capture) {
          final barcodes = capture.barcodes;

          if (barcodes.isEmpty) return;

          final value = barcodes.first.rawValue;

          if (value == null || value.isEmpty) {
            return;
          }

          processQr(value);
        },
      ),
    );
  }
}
