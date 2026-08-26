const crypto = require("crypto");
const pool = require("../config/database");

let screenshotEvent = null;

//öğretmen yoklama baslatıyo
async function createAttendanceSession(req, res) {
    try {

        if (req.user.role !== "teacher") {
            return res.status(403).json({
                message: "Sadece öğretmen yoklama başlatabilir."
            });
        }

        const qrToken = crypto //qrtoken
            .randomBytes(32)
            .toString("hex");

        const createdAt = new Date();

        const expiresAt = new Date(
            createdAt.getTime() + 30 * 1000
        );

        const result = await pool.query(
            `
            INSERT INTO attendance_sessions
            (
                teacher_id,
                qr_token,
                created_at,
                expires_at
            )
            VALUES ($1, $2, $3, $4)
            RETURNING id, qr_token, created_at, expires_at
            `,
            [
                req.user.userId,
                qrToken,
                createdAt,
                expiresAt
            ]
        );

        res.status(201).json({
            message: "Yoklama başlatıldı.",
            session: result.rows[0]
        }); //webe json gönderiliyor

    } catch (error) {

        console.error(
            "Yoklama oluşturma hatası:",
            error
        );

        res.status(500).json({
            message: "Yoklama başlatılamadı."
        });
    }
}


// =========================================================
// ÖĞRENCİ - YOKLAMAYA KATIL
// =========================================================

async function joinAttendance(req, res) {
    try {

        if (req.user.role !== "student") {
            return res.status(403).json({
                message: "Sadece öğrenciler yoklamaya katılabilir."
            });
        }

        const { qrToken } = req.body; //flutterdan qrtoken aliniyor

        if (!qrToken) {
            return res.status(400).json({
                message: "QR kodu bulunamadı."
            });
        }

        const sessionResult = await pool.query( //databaseden token aliniyor
            `
            SELECT *
            FROM attendance_sessions
            WHERE qr_token = $1
            `,
            [qrToken]
        );

        if (sessionResult.rows.length === 0) {
            return res.status(404).json({
                message: "Geçersiz QR kodu."
            });
        }

        const session = sessionResult.rows[0];

        if (
            new Date() >
            new Date(session.expires_at)
        ) {
            return res.status(400).json({
                message: "QR kodunun süresi dolmuş."
            });
        }

        const result = await pool.query( //token geçerliyse
            `
            INSERT INTO attendance_records
            (
                session_id,
                student_id
            )
            VALUES ($1, $2)
            ON CONFLICT (session_id, student_id)
            DO NOTHING
            RETURNING id, attended_at
            `,
            [
                session.id,
                req.user.userId
            ]
        );

        if (result.rows.length === 0) {
            return res.json({
                message: "Bu yoklamaya zaten katıldınız."
            });
        }

        screenshotEvent = {
            id: Date.now(),
            studentId: req.user.userId,
            sessionId: session.id
        };

        console.log("📸 SCREENSHOT EVENT OLUŞTU:");
        console.log(screenshotEvent);

        res.json({
            message: "Yoklama başarıyla alındı.",
            attendance: result.rows[0]
        });

    } catch (error) {

        console.error(
            "Yoklamaya katılma hatası:",
            error
        );

        res.status(500).json({
            message: "Yoklamaya katılırken hata oluştu."
        });
    }
}


// =========================================================
// ÖĞRENCİ - KATILDIĞI YOKLAMALAR
// =========================================================

async function getMyAttendance(req, res) {
    try {

        if (req.user.role !== "student") {
            return res.status(403).json({
                message: "Bu alan sadece öğrenciler içindir."
            });
        }

        const result = await pool.query(
            `
            SELECT
                ar.id,
                ar.attended_at,
                u.full_name AS teacher_name,
                s.created_at AS session_date
            FROM attendance_records ar
            INNER JOIN attendance_sessions s
                ON ar.session_id = s.id
            INNER JOIN users u
                ON s.teacher_id = u.id
            WHERE ar.student_id = $1
            ORDER BY ar.attended_at DESC
            `,
            [req.user.userId]
        );

        res.json({
            attendance: result.rows
        });

    } catch (error) {

        console.error(
            "Yoklamaları getirme hatası:",
            error
        );

        res.status(500).json({
            message: "Yoklamalar getirilemedi."
        });
    }
}


// =========================================================
// ÖĞRETMEN - AKTİF YOKLAMADAKİ ÖĞRENCİLER
// =========================================================

async function getCurrentAttendance(req, res) {
    try {

        if (req.user.role !== "teacher") {
            return res.status(403).json({
                message: "Bu alan sadece öğretmenler içindir."
            });
        }

        const result = await pool.query(
            `
            SELECT
                ar.id,
                u.full_name AS name,
                u.student_number,
                TO_CHAR(
                    ar.attended_at,
                    'HH24:MI:SS'
                ) AS time
            FROM attendance_records ar

            INNER JOIN attendance_sessions s
                ON ar.session_id = s.id

            INNER JOIN users u
                ON ar.student_id = u.id

            WHERE s.teacher_id = $1

            ORDER BY ar.attended_at ASC
            `,
            [req.user.userId]
        );

        res.json({
            attendance: result.rows
        });

    } catch (error) {

        console.error(
            "Güncel yoklama listesi hatası:",
            error
        );

        res.status(500).json({
            message: "Yoklama listesi getirilemedi."
        });
    }
}
// =========================================================
// APPIUM - SCREENSHOT EVENTİNİ KONTROL ET
// =========================================================

async function getScreenshotEvent(req, res) {

    if (!screenshotEvent) {
        return res.json({
            event: null
        });
    }

    const event = screenshotEvent;

    // Event bir kez okunduktan sonra tekrar tetiklenmesin
    screenshotEvent = null;

    res.json({
        event: event
    });
}
// =========================================================
// FLUTTER - QR ALGILANDIĞINDA SCREENSHOT TETİKLE
// =========================================================

async function triggerScreenshot(req, res) {
    try {

        if (req.user.role !== "student") {
            return res.status(403).json({
                message: "Sadece öğrenciler screenshot tetikleyebilir."
            });
        }

        screenshotEvent = {
            id: Date.now(),
            studentId: req.user.userId
        };

        console.log("📸 QR ALGILANDI - SCREENSHOT TETİKLENDİ:");
        console.log(screenshotEvent);

        res.json({
            message: "Screenshot tetiklendi."
        });

    } catch (error) {

        console.error(
            "Screenshot trigger hatası:",
            error
        );

        res.status(500).json({
            message: "Screenshot tetiklenemedi."
        });
    }
}
// =========================================================
// EXPORT
// =========================================================

module.exports = {
    createAttendanceSession,
    joinAttendance,
    getMyAttendance,
    getCurrentAttendance,
    getScreenshotEvent,
    triggerScreenshot

};