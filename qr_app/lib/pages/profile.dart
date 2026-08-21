import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'login.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() =>
      _ProfilePageState();
}

class _ProfilePageState
    extends State<ProfilePage> {

  String name = '';
  String number = '';
  String role = '';

  @override
  void initState() {
    super.initState();
    loadUser();
  }

  Future<void> loadUser() async {
    final prefs =
        await SharedPreferences.getInstance();

    if (!mounted) return;

    setState(() {
      name = prefs.getString('full_name') ?? '';
      number =
          prefs.getString('student_number') ?? '';
      role = prefs.getString('role') ?? '';
    });
  }

  Future<void> logout() async {
    final prefs =
        await SharedPreferences.getInstance();

    await prefs.clear();

    if (!mounted) return;

    Navigator.pushAndRemoveUntil(
      context,
      MaterialPageRoute(
        builder: (_) => const LoginPage(),
      ),
      (route) => false,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profil'),
        centerTitle: true,
      ),

      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [

            const CircleAvatar(
              radius: 50,
              child: Icon(
                Icons.person,
                size: 50,
              ),
            ),

            const SizedBox(height: 20),

            Text(
              name,
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 8),

            Text('Numara: $number'),

            const SizedBox(height: 4),

            Text(
              role == 'teacher'
                  ? 'Öğretmen'
                  : 'Öğrenci',
            ),

            const Spacer(),

            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: logout,
                child: const Text('Çıkış Yap'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}