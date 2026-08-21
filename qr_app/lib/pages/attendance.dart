import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_client.dart';

class AttendancePage extends StatefulWidget {
  const AttendancePage({super.key});

  @override
  State<AttendancePage> createState() =>
      _AttendancePageState();
}

class _AttendancePageState
    extends State<AttendancePage> {

  final ApiClient apiClient = ApiClient();

  List<dynamic> attendance = [];

  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    loadAttendance();
  }

  Future<void> loadAttendance() async {
    try {
      final prefs =
          await SharedPreferences.getInstance();

      final token = prefs.getString('token');

      if (token == null) {
        return;
      }

      final result =
          await apiClient.getMyAttendance(token);

      if (!mounted) return;

      setState(() {
        attendance = result;
        isLoading = false;
      });

    } catch (e) {
      if (!mounted) return;

      setState(() {
        isLoading = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            e.toString().replaceFirst(
              'Exception: ',
              '',
            ),
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Yoklamalar'),
        centerTitle: true,
      ),

      body: isLoading
          ? const Center(
              child: CircularProgressIndicator(),
            )
          : RefreshIndicator(
              onRefresh: loadAttendance,
              child: attendance.isEmpty
                  ? ListView(
                      children: const [
                        SizedBox(height: 200),
                        Center(
                          child: Text(
                            'Henüz katıldığınız yoklama yok.',
                          ),
                        ),
                      ],
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.all(16),
                      itemCount: attendance.length,
                      itemBuilder: (context, index) {
                        final item =
                            attendance[index];

                        return Card(
                          child: ListTile(
                            leading: const CircleAvatar(
                              child: Icon(
                                Icons.check,
                              ),
                            ),
                            title: Text(
                              item['teacher_name']
                                  ?? 'Öğretmen',
                            ),
                            subtitle: Text(
                              item['attended_at']
                                  ?? '',
                            ),
                          ),
                        );
                      },
                    ),
            ),
    );
  }
}