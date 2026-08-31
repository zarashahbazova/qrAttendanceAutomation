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

        const { attendanceName } = req.body;

        if (!attendanceName || !attendanceName.trim()) {
            return res.status(400).json({
                message: "Yoklama adı zorunludur."
            });
        }

        // Öğretmenin hâlihazırda aktif bir yoklaması var mı?
        const activeSession = await pool.query(
            `
            SELECT id
            FROM attendance_sessions
            WHERE teacher_id = $1
              AND is_saved = false
              AND total_expires_at > NOW()
            LIMIT 1
            `,
            [req.user.userId]
        );

        if (activeSession.rows.length > 0) {
            return res.status(400).json({
                message: "Zaten aktif bir yoklamanız var."
            });
        }

        const qrToken = crypto
            .randomBytes(32)
            .toString("hex");

        const createdAt = new Date();

        // Bu QR'ın geçerlilik süresi: 30 saniye
        const expiresAt = new Date(
            createdAt.getTime() + 30 * 1000
        );

        // Bütün yoklamanın toplam süresi: 120 saniye
        const totalExpiresAt = new Date(
            createdAt.getTime() + 120 * 1000
        );

        const result = await pool.query(
            `
            INSERT INTO attendance_sessions
            (
                teacher_id,
                qr_token,
                created_at,
                expires_at,
                total_expires_at,
                attendance_name,
                is_saved
            )
            VALUES ($1, $2, $3, $4, $5, $6, false)
            RETURNING
                id,
                teacher_id,
                qr_token,
                created_at,
                expires_at,
                total_expires_at,
                attendance_name,
                is_saved
            `,
            [
                req.user.userId,
                qrToken,
                createdAt,
                expiresAt,
                totalExpiresAt,
                attendanceName.trim()
            ]
        );

        res.status(201).json({
            message: "Yoklama başlatıldı.",
            session: result.rows[0]
        });

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
//öğretmen- ayni yoklamanın qrını yenile
async function refreshAttendanceQR(req, res) {
    try {

        if (req.user.role !== "teacher") {
            return res.status(403).json({
                message: "Sadece öğretmen QR yenileyebilir."
            });
        }

        const { sessionId } = req.params;

        const sessionResult = await pool.query(
            `
            SELECT *
            FROM attendance_sessions
            WHERE id = $1
              AND teacher_id = $2
            `,
            [
                sessionId,
                req.user.userId
            ]
        );

        if (sessionResult.rows.length === 0) {
            return res.status(404).json({
                message: "Yoklama bulunamadı."
            });
        }

        const session = sessionResult.rows[0];

        // Yoklama zaten sonlandırılmışsa
        if (session.is_saved) {
            return res.status(400).json({
                message: "Bu yoklama zaten sonlandırılmış."
            });
        }

        // Toplam 120 saniye dolmuşsa
        if (new Date() > new Date(session.total_expires_at)) {

            await pool.query(
                `
                UPDATE attendance_sessions
                SET is_saved = true
                WHERE id = $1
                `,
                [sessionId]
            );

            return res.status(400).json({
                message: "Yoklamanın toplam süresi dolmuş."
            });
        }

        const qrToken = crypto
            .randomBytes(32)
            .toString("hex");

        const now = new Date();

        let newExpiresAt = new Date(
            now.getTime() + 30 * 1000
        );

        // QR'ın süresi toplam 120 saniyeyi geçmesin
        const totalExpiresAt = new Date(
            session.total_expires_at
        );

        if (newExpiresAt > totalExpiresAt) {
            newExpiresAt = totalExpiresAt;
        }

        const result = await pool.query(
            `
            UPDATE attendance_sessions
            SET
                qr_token = $1,
                expires_at = $2
            WHERE id = $3
            RETURNING
                id,
                qr_token,
                created_at,
                expires_at,
                total_expires_at,
                attendance_name,
                is_saved
            `,
            [
                qrToken,
                newExpiresAt,
                sessionId
            ]
        );

        res.json({
            message: "QR yenilendi.",
            session: result.rows[0]
        });

    } catch (error) {

        console.error(
            "QR yenileme hatası:",
            error
        );

        res.status(500).json({
            message: "QR yenilenemedi."
        });
    }
}

//yoklaamyı sonlandir
async function endAttendanceSession(req, res) {
    try {

        if (req.user.role !== "teacher") {
            return res.status(403).json({
                message: "Sadece öğretmen yoklamayı sonlandırabilir."
            });
        }

        const { sessionId } = req.params;

        const result = await pool.query(
            `
            UPDATE attendance_sessions
            SET
                is_saved = true,
                expires_at = NOW()
            WHERE id = $1
              AND teacher_id = $2
              AND is_saved = false
            RETURNING
                id,
                attendance_name,
                created_at,
                total_expires_at,
                is_saved
            `,
            [
                sessionId,
                req.user.userId
            ]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({
                message: "Aktif yoklama bulunamadı."
            });
        }

        res.json({
            message: "Yoklama sonlandırıldı.",
            session: result.rows[0]
        });

    } catch (error) {

        console.error(
            "Yoklama sonlandırma hatası:",
            error
        );

        res.status(500).json({
            message: "Yoklama sonlandırılamadı."
        });
    }
}

//yoklamaya katıl
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

        // Öğretmen yoklamayı manuel olarak sonlandırmışsa
        if (session.is_saved) {
            return res.status(400).json({
                message: "Bu yoklama artık aktif değil."
            });
        }

        // QR'ın 30 saniyesi dolmuşsa
        if (
            new Date() >
            new Date(session.expires_at)
        ) {
            return res.status(400).json({
                message: "QR kodunun süresi dolmuş."
            });
        }

        // Yoklamanın toplam 120 saniyesi dolmuşsa
        if (
            new Date() >
            new Date(session.total_expires_at)
        ) {

            await pool.query(
                `
        UPDATE attendance_sessions
        SET is_saved = true
        WHERE id = $1
        `,
                [session.id]
            );

            return res.status(400).json({
                message: "Yoklamanın süresi dolmuş."
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


// katıldıgı yoklamalar
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


// aktif yoklamadaki öğrenciler
async function getCurrentAttendance(req, res) {
    try {

        if (req.user.role !== "teacher") {
            return res.status(403).json({
                message: "Bu alan sadece öğretmenler içindir."
            });
        }

        const { sessionId } = req.query;

        // Aktif yoklama yoksa boş liste
        if (!sessionId) {
            return res.json({
                attendance: []
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
              AND s.id = $2

            ORDER BY ar.attended_at ASC
            `,
            [
                req.user.userId,
                sessionId
            ]
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

// eski yoklamalar
async function getAttendanceHistory(req, res) {
    try {

        if (req.user.role !== "teacher") {
            return res.status(403).json({
                message: "Bu alan sadece öğretmenler içindir."
            });
        }

        const result = await pool.query(
            `
            SELECT
                s.id,
                s.attendance_name,
                s.created_at,
                s.total_expires_at,
                s.is_saved,
                COUNT(ar.id)::int AS student_count
            FROM attendance_sessions s

            LEFT JOIN attendance_records ar
                ON ar.session_id = s.id

            WHERE s.teacher_id = $1
              AND s.is_saved = true

            GROUP BY
                s.id,
                s.attendance_name,
                s.created_at,
                s.total_expires_at,
                s.is_saved

            ORDER BY s.created_at DESC
            `,
            [req.user.userId]
        );

        res.json({
            attendance: result.rows
        });

    } catch (error) {

        console.error(
            "Eski yoklamaları getirme hatası:",
            error
        );

        res.status(500).json({
            message: "Eski yoklamalar getirilemedi."
        });
    }
}

// ss eventini kontrol et (appium)
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

//qr algilandiginda ss tetikle (flutter)
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

//export
module.exports = {
    createAttendanceSession,
    refreshAttendanceQR,
    endAttendanceSession,
    joinAttendance,
    getMyAttendance,
    getCurrentAttendance,
    getScreenshotEvent,
    getAttendanceHistory,
    triggerScreenshot
};