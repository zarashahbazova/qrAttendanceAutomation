const express = require("express");

const authenticateToken = require("../middleware/authMiddleware");

const attendanceController = require("../controllers/attendanceController");

const router = express.Router();

const multer = require("multer");
const path = require("path");
const fs = require("fs");
const uploadDir = path.join(__dirname, "../uploads");

if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, {
        recursive: true
    });
}

const upload = multer({
    dest: uploadDir
});
router.get(
    "/screenshot-event",
    attendanceController.getScreenshotEvent
);
router.post(
    "/screenshot",
    upload.single("screenshot"),
    attendanceController.receiveScreenshot
);
// yoklama başlat
router.post(
    "/session",
    authenticateToken,
    attendanceController.createAttendanceSession
);

// aynı yoklamanın QR'ını yenile
router.post(
    "/session/:sessionId/refresh",
    authenticateToken,
    attendanceController.refreshAttendanceQR
);

// yoklamayı sonlandır
router.post(
    "/session/:sessionId/end",
    authenticateToken,
    attendanceController.endAttendanceSession
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

router.get(
    "/history",
    authenticateToken,
    attendanceController.getAttendanceHistory
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

// öğretmenin eski yoklamaları
router.get(
    "/history",
    authenticateToken,
    attendanceController.getAttendanceHistory
);



module.exports = router;