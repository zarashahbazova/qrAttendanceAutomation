import 'dart:convert';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const ApkManagerApp());
}

class ApkManagerApp extends StatelessWidget {
  const ApkManagerApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'APK Manager',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  String? selectedApkPath;
  String? selectedApkName;

  String selectedCamera = 'webcam0';

  bool isStarting = false;

  // APK seç
  Future<void> pickApk() async {
    final file = await FilePicker.pickFile(
      type: FileType.custom,
      allowedExtensions: ['apk'],
    );

    if (file == null) {
      return;
    }

    setState(() {
      selectedApkPath = file.path;
      selectedApkName = file.name;
    });
  }

  // APKyı emulator üzerinde başlat
  Future<void> installAndStartApk() async {
    if (selectedApkPath == null) {
      return;
    }

    setState(() {
      isStarting = true;
    });

    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:5050/install'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'apkPath': selectedApkPath!,
          'camera': selectedCamera,
        }),
      );

      if (!mounted) {
        return;
      }

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Emulator ve APK başlatılıyor...')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Python Agent hatası: ${response.body}')),
        );
      }
    } catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Python Agent bağlantı hatası: $error')),
      );
    } finally {
      if (mounted) {
        setState(() {
          isStarting = false;
        });
      }
    }
  }

  // Arayüz
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('APK Manager')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const SizedBox(height: 3),

            const Icon(Icons.phone_android, size: 40),

            const SizedBox(height: 10),

            const Text(
              'APK Manager',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),

            const SizedBox(height: 10),

            const Text(
              'Emulator üzerinde çalıştırmak istediğiniz '
              'APK dosyasını seçin.',
              textAlign: TextAlign.center,
            ),

            const SizedBox(height: 30),

            // APK ekle
            SizedBox(
              width: double.infinity,
              height: 35,
              child: ElevatedButton.icon(
                onPressed: isStarting ? null : pickApk,
                icon: const Icon(Icons.folder_open),
                label: const Text('APK Ekle', style: TextStyle(fontSize: 18)),
              ),
            ),

            const SizedBox(height: 30),

            // Seçilen APK
            if (selectedApkName != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.android),
                          SizedBox(width: 4),
                          Text(
                            'Seçilen APK',
                            style: TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 18,
                            ),
                          ),
                        ],
                      ),

                      const SizedBox(height: 12),

                      Text(
                        selectedApkName!,
                        style: const TextStyle(fontSize: 16),
                      ),

                      const SizedBox(height: 8),

                      Text(
                        selectedApkPath ?? '',
                        style: const TextStyle(fontSize: 12),
                      ),
                    ],
                  ),
                ),
              ),

            const SizedBox(height: 25),

            // Kamera seç
            Align(
              alignment: Alignment.centerLeft,
              child: Text(
                'Kamera',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            ),

            const SizedBox(height: 8),

            DropdownButtonFormField<String>(
              value: selectedCamera,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.camera_alt),
              ),
              items: const [
                DropdownMenuItem(
                  value: 'webcam0',
                  child: Text('FaceTime HD Kamera'),
                ),
                DropdownMenuItem(
                  value: 'webcam1',
                  child: Text('OBS Virtual Camera'),
                ),
              ],
              onChanged: isStarting
                  ? null
                  : (value) {
                      if (value == null) {
                        return;
                      }

                      setState(() {
                        selectedCamera = value;
                      });
                    },
            ),

            const Spacer(),

            // Kur ve başlat
            if (selectedApkPath != null)
              SizedBox(
                width: double.infinity,
                height: 55,
                child: ElevatedButton.icon(
                  onPressed: isStarting ? null : installAndStartApk,
                  icon: isStarting
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.play_arrow),
                  label: Text(
                    isStarting ? 'Başlatılıyor...' : 'Kur ve Başlat',
                    style: const TextStyle(fontSize: 18),
                  ),
                ),
              ),

            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
