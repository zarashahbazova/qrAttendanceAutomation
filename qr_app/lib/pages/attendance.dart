import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../services/api_client.dart';

class AttendancePage extends StatefulWidget {
  const AttendancePage({super.key});

  @override
  State<AttendancePage> createState() => _AttendancePageState();
}

class _AttendancePageState extends State<AttendancePage> {
  final ApiClient apiClient = ApiClient();

  List<dynamic> attendance = [];

  bool isLoading = true;

  @override
  void initState() {
    super.initState();

    loadAttendance();
  }

  //yoklamaları getir
  Future<void> loadAttendance() async {
    try {
      final prefs = await SharedPreferences.getInstance();

      final token = prefs.getString('token');

      if (token == null) {
        if (!mounted) return;

        setState(() {
          isLoading = false;
        });

        return;
      }

      final result = await apiClient.getMyAttendance(token);

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
          backgroundColor: const Color(0xFF111827),

          behavior: SnackBarBehavior.floating,

          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),

          content: Text(
            e.toString().replaceFirst('Exception: ', ''),

            style: const TextStyle(color: Colors.white, fontSize: 13),
          ),
        ),
      );
    }
  }

  // tarih
  String _formatDate(String? rawDate) {
    if (rawDate == null || rawDate.isEmpty) {
      return '-';
    }

    try {
      final dt = DateTime.parse(rawDate).toLocal();

      final day = dt.day.toString().padLeft(2, '0');

      final month = dt.month.toString().padLeft(2, '0');

      final year = dt.year.toString();

      final hour = dt.hour.toString().padLeft(2, '0');

      final minute = dt.minute.toString().padLeft(2, '0');

      return '$day.$month.$year • '
          '$hour:$minute';
    } catch (_) {
      return rawDate;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFAFAFA),

      body: SafeArea(
        child: RefreshIndicator(
          color: const Color(0xFF111827),

          onRefresh: loadAttendance,

          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),

            padding: const EdgeInsets.all(20),

            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,

              children: [
                // baslik
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,

                  children: [
                    const Text(
                      'Yoklama Geçmişi',

                      style: TextStyle(
                        fontSize: 20,

                        fontWeight: FontWeight.w800,

                        letterSpacing: -0.5,

                        color: Color(0xFF111827),
                      ),
                    ),

                    IconButton(
                      onPressed: loadAttendance,

                      style: IconButton.styleFrom(
                        backgroundColor: Colors.white,

                        side: const BorderSide(color: Color(0xFFE5E7EB)),
                      ),

                      icon: const Icon(
                        Icons.refresh_rounded,

                        size: 20,

                        color: Color(0xFF111827),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 20),

                // liste
                isLoading
                    ? const Padding(
                        padding: EdgeInsets.symmetric(vertical: 40),

                        child: Center(
                          child: CircularProgressIndicator(
                            strokeWidth: 2,

                            color: Color(0xFF111827),
                          ),
                        ),
                      )
                    : Container(
                        decoration: BoxDecoration(
                          color: Colors.white,

                          borderRadius: BorderRadius.circular(16),

                          border: Border.all(color: const Color(0xFFE5E7EB)),
                        ),

                        child: attendance.isEmpty
                            ? Padding(
                                padding: const EdgeInsets.symmetric(
                                  vertical: 48,
                                ),

                                child: Center(
                                  child: Column(
                                    children: const [
                                      Icon(
                                        Icons.assignment_late_outlined,

                                        size: 32,

                                        color: Color(0xFF9CA3AF),
                                      ),

                                      SizedBox(height: 10),

                                      Text(
                                        'Henüz katıldığınız yoklama yok.',

                                        style: TextStyle(
                                          fontSize: 13,

                                          fontWeight: FontWeight.w500,

                                          color: Color(0xFF6B7280),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              )
                            : ListView.separated(
                                shrinkWrap: true,

                                physics: const NeverScrollableScrollPhysics(),

                                itemCount: attendance.length,

                                separatorBuilder: (context, index) =>
                                    const Divider(
                                      height: 1,

                                      color: Color(0xFFF3F4F6),

                                      indent: 56,
                                    ),

                                itemBuilder: (context, index) {
                                  final item = attendance[index];

                                  return _buildAttendanceRow(
                                    teacherName:
                                        item['teacher_name'] ?? 'Öğretmen',

                                    courseName: item['course_name'] ?? 'Ders',

                                    attendanceName:
                                        item['attendance_name'] ?? 'Yoklama',

                                    dateText: _formatDate(item['attended_at']),
                                  );
                                },
                              ),
                      ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  //yoklama sistemi
  Widget _buildAttendanceRow({
    required String teacherName,

    required String courseName,

    required String attendanceName,

    required String dateText,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),

      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),

            decoration: BoxDecoration(
              color: const Color(0xFFF9FAFB),

              borderRadius: BorderRadius.circular(8),

              border: Border.all(color: const Color(0xFFF3F4F6)),
            ),

            child: const Icon(
              Icons.school_outlined,

              size: 18,

              color: Color(0xFF4B5563),
            ),
          ),

          const SizedBox(width: 14),

          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,

              children: [
                // Ders adı
                Text(
                  courseName,

                  style: const TextStyle(
                    fontSize: 14,

                    fontWeight: FontWeight.w700,

                    color: Color(0xFF111827),
                  ),
                ),

                const SizedBox(height: 3),

                // Yoklama adı
                Text(
                  attendanceName,

                  style: const TextStyle(
                    fontSize: 12,

                    fontWeight: FontWeight.w600,

                    color: Color(0xFF374151),
                  ),
                ),

                const SizedBox(height: 3),

                // Öğretmen
                Text(
                  teacherName,

                  style: const TextStyle(
                    fontSize: 13,

                    fontWeight: FontWeight.w500,

                    color: Color(0xFF111827),
                  ),
                ),

                const SizedBox(height: 3),

                // Tarih / saat
                Text(
                  dateText,

                  style: const TextStyle(
                    fontSize: 12,

                    color: Color(0xFF6B7280),

                    fontWeight: FontWeight.w400,
                  ),
                ),
              ],
            ),
          ),

          // katıldı
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),

            decoration: BoxDecoration(
              color: const Color(0xFFECFDF5),

              borderRadius: BorderRadius.circular(6),

              border: Border.all(color: const Color(0xFFA7F3D0)),
            ),

            child: const Text(
              'Katıldı',

              style: TextStyle(
                fontSize: 11,

                fontWeight: FontWeight.w600,

                color: Color(0xFF047857),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
