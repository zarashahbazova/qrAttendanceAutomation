const express = require("express");

const authenticateToken = require("../middleware/authMiddleware");

const attendanceController = require("../controllers/attendanceController");

const router = express.Router();


// Öğretmen - yoklama başlat
router.post(
    "/session",
    authenticateToken,
    attendanceController.createAttendanceSession
);


// Öğrenci - yoklamaya katıl
router.post(
    "/join",
    authenticateToken,
    attendanceController.joinAttendance
);


// Öğrenci - katıldığı yoklamalar
router.get(
    "/my",
    authenticateToken,
    attendanceController.getMyAttendance
);


// Öğretmen - mevcut yoklamadaki öğrenciler
router.get(
    "/current",
    authenticateToken,
    attendanceController.getCurrentAttendance
);


module.exports = router;