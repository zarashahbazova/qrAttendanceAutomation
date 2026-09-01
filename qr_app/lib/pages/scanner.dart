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
  bool torchOn = false;

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

      // Screenshot'ın alınabilmesi için kamerayı
      // kısa süre açık tut.
      await Future.delayed(const Duration(seconds: 2));

      if (!mounted) return;

      await controller.stop();

      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (_) {
          return AlertDialog(
            backgroundColor: Colors.white,
            surfaceTintColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
            ),
            title: const Row(
              children: [
                Icon(
                  Icons.check_circle_outline_rounded,
                  color: Color(0xFF10B981),
                  size: 24,
                ),
                SizedBox(width: 8),
                Text(
                  'Yoklama Başarılı',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF111827),
                  ),
                ),
              ],
            ),
            content: Text(
              message,
              style: const TextStyle(fontSize: 14, color: Color(0xFF4B5563)),
            ),
            actions: [
              SizedBox(
                width: double.infinity,
                height: 44,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF000000),
                    foregroundColor: Colors.white,
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  onPressed: () async {
                    Navigator.pop(context);

                    if (!controller.value.isRunning) {
                      await controller.start();
                    }

                    processing = false;

                    if (mounted) {
                      setState(() {});
                    }
                  },
                  child: const Text(
                    'Tamam',
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                ),
              ),
            ],
          );
        },
      );
    } catch (e) {
      processing = false;
      if (!mounted) return;

      String message = e.toString().replaceFirst('Exception: ', '');

      if (message.contains('QR kodunun süresi dolmuş')) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            backgroundColor: Color(0xFF111827),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.all(Radius.circular(8)),
            ),
            content: Text(
              'QR kodunun süresi dolmuş. Güncel QR kodu okutun.',
              style: TextStyle(color: Colors.white, fontSize: 13),
            ),
            duration: Duration(seconds: 2),
          ),
        );
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: const Color(0xFFDC2626),
          behavior: SnackBarBehavior.floating,
          shape: const RoundedRectangleBorder(
            borderRadius: BorderRadius.all(Radius.circular(8)),
          ),
          content: Text(
            message,
            style: const TextStyle(color: Colors.white, fontSize: 13),
          ),
        ),
      );
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
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          MobileScanner(
            controller: controller,
            onDetect: (capture) {
              final barcodes = capture.barcodes;
              if (barcodes.isEmpty) return;

              final value = barcodes.first.rawValue;
              if (value == null || value.isEmpty) return;

              processQr(value);
            },
          ),
          SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.only(
                    left: 20,
                    top: 12,
                    right: 20,
                    bottom: 12,
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'QR Tara',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      IconButton(
                        style: IconButton.styleFrom(
                          backgroundColor: Colors.black.withOpacity(0.5),
                        ),
                        icon: Icon(
                          torchOn
                              ? Icons.flash_on_rounded
                              : Icons.flash_off_rounded,
                          color: Colors.white,
                          size: 20,
                        ),
                        onPressed: () {
                          controller.toggleTorch();
                          setState(() => torchOn = !torchOn);
                        },
                      ),
                    ],
                  ),
                ),
                const Spacer(),
                Container(
                  width: 250,
                  height: 250,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.9),
                      width: 2,
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 16,
                    vertical: 8,
                  ),
                  decoration: BoxDecoration(
                    color: Colors.black.withOpacity(0.65),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Text(
                    'Öğretmenin ekranındaki QR kodu hizalayın',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                const Spacer(),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
