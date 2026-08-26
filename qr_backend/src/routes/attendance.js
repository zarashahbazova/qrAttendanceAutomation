const express = require("express");

const authenticateToken = require("../middleware/authMiddleware");

const attendanceController = require("../controllers/attendanceController");

const router = express.Router();
router.get(
    "/screenshot-event",
    attendanceController.getScreenshotEvent
);

// yoklama başlat
router.post(
    "/session",
    authenticateToken,
    attendanceController.createAttendanceSession
);

router.post(
    "/screenshot-trigger",
    authenticateToken,
    attendanceController.triggerScreenshot
);

// yoklamaya katıl
router.post(
    "/join",
    authenticateToken,
    attendanceController.joinAttendance
);


// ögrencinin katıldığı yoklamalar
router.get(
    "/my",
    authenticateToken,
    attendanceController.getMyAttendance
);


// ögretmen icin mevcut yoklamadaki öğrenciler
router.get(
    "/current",
    authenticateToken,
    attendanceController.getCurrentAttendance
);


module.exports = router;