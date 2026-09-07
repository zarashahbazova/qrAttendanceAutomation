import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(const QrStudentApp());
}

// ============================================================
// KULLANICI MODELİ
// ============================================================

class PumaUser {
  final String username;
  final String password;
  bool selected;

  PumaUser({
    required this.username,
    required this.password,
    this.selected = false,
  });

  Map<String, dynamic> toJson() {
    return {'username': username, 'password': password, 'selected': selected};
  }

  factory PumaUser.fromJson(Map<String, dynamic> json) {
    return PumaUser(
      username: json['username'] ?? '',
      password: json['password'] ?? '',
      selected: json['selected'] ?? false,
    );
  }
}

// ============================================================
// ANA UYGULAMA
// ============================================================

class QrStudentApp extends StatelessWidget {
  const QrStudentApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'QR Yoklama',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: const ColorScheme.light(
          primary: Colors.black,
          secondary: Colors.black,
        ),
        scaffoldBackgroundColor: Colors.white,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black,
          elevation: 0,
        ),
      ),
      home: const HomePage(),
    );
  }
}

// ============================================================
// ANA SAYFA + ALT NAVIGATION
// ============================================================

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int selectedIndex = 0;

  final List<PumaUser> users = [];

  @override
  void initState() {
    super.initState();
    loadUsers();
  }

  // ----------------------------------------------------------
  // KAYITLI KULLANICILARI YÜKLE
  // ----------------------------------------------------------

  Future<void> loadUsers() async {
    final prefs = await SharedPreferences.getInstance();

    final savedUsers = prefs.getString('puma_users');

    if (savedUsers == null) return;

    try {
      final List<dynamic> decoded = jsonDecode(savedUsers);

      setState(() {
        users.clear();

        for (final item in decoded) {
          users.add(PumaUser.fromJson(Map<String, dynamic>.from(item)));
        }
      });
    } catch (e) {
      // Kayıt bozuksa uygulamanın açılmasını engelleme.
    }
  }

  // ----------------------------------------------------------
  // KULLANICILARI KAYDET
  // ----------------------------------------------------------

  Future<void> saveUsers() async {
    final prefs = await SharedPreferences.getInstance();

    final data = users.map((user) => user.toJson()).toList();

    await prefs.setString('puma_users', jsonEncode(data));
  }

  // ----------------------------------------------------------
  // EKRAN
  // ----------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final pages = [
      ScannerPage(users: users),
      UsersPage(
        users: users,
        onUsersChanged: () {
          saveUsers();

          setState(() {});
        },
      ),
    ];

    return Scaffold(
      body: IndexedStack(index: selectedIndex, children: pages),

      bottomNavigationBar: NavigationBar(
        backgroundColor: Colors.white,
        indicatorColor: Colors.grey.shade200,
        selectedIndex: selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.qr_code_scanner),
            label: 'Scanner',
          ),
          NavigationDestination(
            icon: Icon(Icons.people_outline),
            label: 'Kullanıcılar',
          ),
        ],
      ),
    );
  }
}

// ============================================================
// SCANNER SAYFASI
// ============================================================

class ScannerPage extends StatefulWidget {
  final List<PumaUser> users;

  const ScannerPage({super.key, required this.users});

  @override
  State<ScannerPage> createState() => _ScannerPageState();
}

class _ScannerPageState extends State<ScannerPage> {
  final MobileScannerController scannerController = MobileScannerController(
    returnImage: true,
    detectionSpeed: DetectionSpeed.noDuplicates,
  );

  bool sending = false;

  String message = 'QR kodunu kamera alanının ortasına getirin';

  final String backendUrl = 'http://192.168.60.28:5001';

  // ----------------------------------------------------------
  // QR GÖNDER
  // ----------------------------------------------------------

  Future<void> sendQrImage(Uint8List imageBytes) async {
    if (sending) return;

    // SADECE SEÇİLİ KULLANICILARI AL
    final selectedUsers = widget.users.where((user) => user.selected).toList();

    if (selectedUsers.isEmpty) {
      setState(() {
        message = 'Önce en az bir kullanıcı seçin.';
      });
      return;
    }

    setState(() {
      sending = true;
      message = 'QR görüntüsü ve seçili kullanıcılar gönderiliyor...';
    });

    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$backendUrl/qr/scan-image'),
      );

      // QR görüntüsü
      request.files.add(
        http.MultipartFile.fromBytes(
          'qrImage',
          imageBytes,
          filename: 'qr_capture.jpg',
          contentType: http.MediaType('image', 'jpeg'),
        ),
      );

      // SADECE SEÇİLİ HESAPLARI GÖNDER
      for (int i = 0; i < selectedUsers.length; i++) {
        request.fields['users[$i][username]'] = selectedUsers[i].username;

        request.fields['users[$i][password]'] = selectedUsers[i].password;
      }

      final response = await request.send();

      final responseBody = await response.stream.bytesToString();

      if (!mounted) return;

      if (response.statusCode >= 200 && response.statusCode < 300) {
        setState(() {
          message =
              'QR gönderildi. '
              '${selectedUsers.length} seçili hesap işlenecek.';
        });
      } else {
        setState(() {
          message =
              'Backend hata verdi: '
              '${response.statusCode}\n'
              '$responseBody';
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

  // ----------------------------------------------------------
  // DISPOSE
  // ----------------------------------------------------------

  @override
  void dispose() {
    scannerController.dispose();
    super.dispose();
  }

  // ----------------------------------------------------------
  // SAYFA
  // ----------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'QR Yoklama',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),

      body: Stack(
        children: [
          // KAMERA
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

              sendQrImage(image);
            },
          ),

          // QR KUTUSU
          Center(
            child: Container(
              width: 260,
              height: 260,
              decoration: BoxDecoration(
                border: Border.all(color: Colors.white, width: 3),
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),

          // MESAJ
          Positioned(
            left: 20,
            right: 20,
            bottom: 30,
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black.withAlpha(5),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                message,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.white, fontSize: 16),
              ),
            ),
          ),

          // YÜKLENİYOR
          if (sending)
            const Center(child: CircularProgressIndicator(color: Colors.white)),
        ],
      ),
    );
  }
}

// ============================================================
// KULLANICILAR SAYFASI
// ============================================================

class UsersPage extends StatelessWidget {
  final List<PumaUser> users;
  final VoidCallback onUsersChanged;

  const UsersPage({
    super.key,
    required this.users,
    required this.onUsersChanged,
  });

  // ----------------------------------------------------------
  // KULLANICI EKLE
  // ----------------------------------------------------------

  void showAddUserDialog(BuildContext context) {
    final usernameController = TextEditingController();
    final passwordController = TextEditingController();

    showDialog(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          backgroundColor: Colors.white,

          title: const Text(
            'Kullanıcı Ekle',
            style: TextStyle(color: Colors.black, fontWeight: FontWeight.bold),
          ),

          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: usernameController,
                decoration: const InputDecoration(
                  labelText: 'Puma kullanıcı adı',
                  border: OutlineInputBorder(),
                ),
              ),

              const SizedBox(height: 16),

              TextField(
                controller: passwordController,
                obscureText: true,
                decoration: const InputDecoration(
                  labelText: 'Puma şifresi',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),

          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(dialogContext);
              },
              child: const Text('İptal', style: TextStyle(color: Colors.black)),
            ),

            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.black,
                foregroundColor: Colors.white,
              ),

              onPressed: () {
                final username = usernameController.text.trim();

                final password = passwordController.text;

                if (username.isEmpty || password.isEmpty) {
                  return;
                }

                users.add(PumaUser(username: username, password: password));

                onUsersChanged();

                Navigator.pop(dialogContext);
              },

              child: const Text('Ekle'),
            ),
          ],
        );
      },
    );
  }

  // ----------------------------------------------------------
  // KULLANICI SİL
  // ----------------------------------------------------------

  void deleteUser(BuildContext context, int index) {
    users.removeAt(index);

    onUsersChanged();
  }

  // ----------------------------------------------------------
  // KULLANICI SEÇ / SEÇME
  // ----------------------------------------------------------

  void toggleUser(int index) {
    final user = users[index];

    // Zaten seçiliyse kaldır
    if (user.selected) {
      user.selected = false;
      onUsersChanged();
      return;
    }

    // Kaç kişi seçili?
    final selectedCount = users.where((user) => user.selected).length;

    // Maksimum 3
    if (selectedCount >= 3) {
      return;
    }

    user.selected = true;

    onUsersChanged();
  }

  // ----------------------------------------------------------
  // SAYFA
  // ----------------------------------------------------------

  @override
  Widget build(BuildContext context) {
    final selectedCount = users.where((user) => user.selected).length;

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Kullanıcılar',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        centerTitle: true,
      ),

      body: Padding(
        padding: const EdgeInsets.all(16),

        child: Column(
          children: [
            // SEÇİM BİLGİSİ
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(14),
              ),
              child: Text(
                'Seçili hesap: $selectedCount / 3',
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.bold,
                ),
                textAlign: TextAlign.center,
              ),
            ),

            const SizedBox(height: 16),

            // KULLANICI EKLE
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  side: const BorderSide(color: Colors.black),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),

                onPressed: () {
                  showAddUserDialog(context);
                },

                icon: const Icon(Icons.person_add_outlined),

                label: const Text(
                  'Kullanıcı Ekle',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            ),

            const SizedBox(height: 20),

            // KULLANICI YOKSA
            if (users.isEmpty)
              const Expanded(
                child: Center(
                  child: Text(
                    'Henüz kullanıcı eklenmedi.',
                    style: TextStyle(fontSize: 16),
                  ),
                ),
              )
            // KULLANICILAR
            else
              Expanded(
                child: ListView.builder(
                  itemCount: users.length,

                  itemBuilder: (context, index) {
                    final user = users[index];

                    return Card(
                      color: Colors.white,
                      elevation: 0,
                      margin: const EdgeInsets.only(bottom: 10),
                      shape: RoundedRectangleBorder(
                        side: const BorderSide(color: Colors.black12),
                        borderRadius: BorderRadius.circular(14),
                      ),

                      child: ListTile(
                        onTap: () {
                          toggleUser(index);
                        },

                        leading: Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            color: user.selected ? Colors.black : Colors.white,
                            border: Border.all(color: Colors.black),
                            borderRadius: BorderRadius.circular(10),
                          ),

                          child: Icon(
                            user.selected ? Icons.check : Icons.person_outline,
                            color: user.selected ? Colors.white : Colors.black,
                          ),
                        ),

                        title: Text(
                          user.username,
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),

                        subtitle: const Text('Puma hesabı'),

                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Checkbox(
                              value: user.selected,

                              activeColor: Colors.black,

                              onChanged: (_) {
                                toggleUser(index);
                              },
                            ),

                            IconButton(
                              icon: const Icon(Icons.delete_outline),

                              onPressed: () {
                                deleteUser(context, index);
                              },
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}
