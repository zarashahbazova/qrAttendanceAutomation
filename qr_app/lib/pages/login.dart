import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_client.dart';
import 'home.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final numberController = TextEditingController();
  final passwordController = TextEditingController();

  final ApiClient apiClient = ApiClient();

  bool isLoading = false;
  bool obscurePassword = true;

  Future<void> login() async {
    final number = numberController.text.trim();
    final password = passwordController.text;

    if (number.isEmpty || password.isEmpty) {
      showMessage('Numara ve şifre giriniz.');
      return;
    }

    setState(() {
      isLoading = true;
    });

    try {
      final data = await apiClient.login(
        number,
        password,
      );

      final prefs =
          await SharedPreferences.getInstance();

      final user = data['user'];

      await prefs.setString(
        'token',
        data['token'],
      );

      await prefs.setString(
        'user_id',
        user['id'].toString(),
      );

      await prefs.setString(
        'student_number',
        user['student_number'],
      );

      await prefs.setString(
        'full_name',
        user['full_name'],
      );

      await prefs.setString(
        'role',
        user['role'],
      );

      if (!mounted) return;

      Navigator.pushAndRemoveUntil(
        context,
        MaterialPageRoute(
          builder: (_) => const HomePage(),
        ),
        (route) => false,
      );

    } catch (e) {
      showMessage(
        e.toString().replaceFirst(
          'Exception: ',
          '',
        ),
      );
    } finally {
      if (mounted) {
        setState(() {
          isLoading = false;
        });
      }
    }
  }

  void showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
      ),
    );
  }

  @override
  void dispose() {
    numberController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Giriş Yap'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [

              const Icon(
                Icons.qr_code_2,
                size: 90,
              ),

              const SizedBox(height: 30),

              TextField(
                controller: numberController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(
                  labelText: 'Öğrenci Numarası',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.person),
                ),
              ),

              const SizedBox(height: 16),

              TextField(
                controller: passwordController,
                obscureText: obscurePassword,
                decoration: InputDecoration(
                  labelText: 'Şifre',
                  border: const OutlineInputBorder(),
                  prefixIcon: const Icon(Icons.lock),
                  suffixIcon: IconButton(
                    icon: Icon(
                      obscurePassword
                          ? Icons.visibility
                          : Icons.visibility_off,
                    ),
                    onPressed: () {
                      setState(() {
                        obscurePassword =
                            !obscurePassword;
                      });
                    },
                  ),
                ),
              ),

              const SizedBox(height: 24),

              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed:
                      isLoading ? null : login,
                  child: isLoading
                      ? const CircularProgressIndicator()
                      : const Text('Giriş Yap'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}