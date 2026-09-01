import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiClient {
  static const String baseUrl = 'http://192.168.60.24:5001';

  // Mac üzerinde emulator kullanıyorsan:
  // static const String baseUrl =
  //     'http://127.0.0.1:5001';

  // login
  Future<Map<String, dynamic>> login(
    String studentNumber,
    String password,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),

      headers: {'Content-Type': 'application/json'},

      body: jsonEncode({'student_number': studentNumber, 'password': password}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      return data;
    }

    throw Exception(data['message'] ?? 'Giriş yapılamadı.');
  }

  // yoklamaya katıl
  Future<String> joinAttendance(String token, String qrToken) async {
    final response = await http.post(
      Uri.parse('$baseUrl/attendance/join'),

      headers: {
        'Content-Type': 'application/json',

        'Authorization': 'Bearer $token',
      },

      body: jsonEncode({'qrToken': qrToken}),
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      return data['message'] ?? 'Yoklama alındı.';
    }

    throw Exception(data['message'] ?? 'Yoklama alınamadı.');
  }

  // öğrencinin yoklama gecmisi
  Future<List<dynamic>> getMyAttendance(String token) async {
    final response = await http.get(
      Uri.parse('$baseUrl/attendance/my'),

      headers: {'Authorization': 'Bearer $token'},
    );

    final data = jsonDecode(response.body);

    if (response.statusCode == 200) {
      return data['attendance'] ?? [];
    }

    throw Exception(data['message'] ?? 'Yoklamalar alınamadı.');
  }
}
