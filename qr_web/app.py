from flask import Flask, render_template, request, redirect, send_file, url_for, session
import requests
import qrcode
import io
import base64
import time
from datetime import datetime

# flask uygulaması oluşturuluyor
app = Flask(__name__)

app.secret_key = "teacher-panel-secret-key"

# node.js backend
BACKEND_URL = "http://localhost:5001"

# ögretmen hesabı
TEACHER_USERNAME = "0000"
TEACHER_PASSWORD = "1234"

# flaskın kendi raminde tuttugu aktif yoklama bilgileri
current_session_id = None
current_qr_token = None
current_qr_expires_at = 0
attendance_window_expires_at = 0
current_attendance_name = None


# login
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:

            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={"student_number": username, "password": password},
                timeout=5,
            )

        except requests.RequestException as error:

            print("LOGIN BACKEND HATASI:", error)

            return render_template("login.html", error="Backend'e bağlanılamadı.")

        # başarılı login
        if response.status_code == 200:

            data = response.json()

            user = data.get("user", {})

            token = data.get("token")

            # Öğretmen hesabı mı kontrolü
            if user.get("role") != "teacher":

                return render_template(
                    "login.html", error="Bu hesap öğretmen hesabı değil."
                )

            # Token geldi mi?
            if not token:

                return render_template("login.html", error="Backend token göndermedi.")

            # sessiona kaydet
            session.clear()

            session["role"] = "teacher"

            session["username"] = user.get("student_number")

            session["name"] = user.get("full_name")

            session["teacher_token"] = token

            print("Öğretmen login başarılı.")

            print("Teacher token kaydedildi.")

            return redirect(url_for("teacher"))

        # login hatasi
        try:

            error_message = response.json().get(
                "message", "Kullanıcı numarası veya şifre yanlış."
            )

        except Exception:

            error_message = "Kullanıcı numarası veya şifre yanlış."

        return render_template("login.html", error=error_message)

    return render_template("login.html")


# öğretmen paneli
@app.route("/teacher")
def teacher():

    if session.get("role") != "teacher":

        return redirect(url_for("login"))

    global current_session_id
    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at
    global current_attendance_name

    qr_image = None
    remaining_seconds = 0
    total_remaining_seconds = 0

    # aktif yoklama var mı
    if current_session_id is not None:

        # toplam yoklama süresi
        total_remaining_seconds = max(
            0, int(attendance_window_expires_at - time.time())
        )

        # toplam süre dolduysa
        if total_remaining_seconds <= 0:

            current_session_id = None
            current_qr_token = None
            current_qr_expires_at = 0
            attendance_window_expires_at = 0
            current_attendance_name = None

        elif current_qr_token is not None:

            remaining_seconds = max(0, int(current_qr_expires_at - time.time()))

            # QR hâlâ geçerliyse göster
            if remaining_seconds > 0:

                qr = qrcode.make(current_qr_token)

                buffer = io.BytesIO()

                qr.save(buffer, format="PNG")

                qr_image = base64.b64encode(buffer.getvalue()).decode()

            else:

                current_qr_token = None

                current_qr_expires_at = 0

    return render_template(
        "teacher.html",
        qr_image=qr_image,
        remaining_seconds=remaining_seconds,
        total_remaining_seconds=total_remaining_seconds,
        attendance_name=current_attendance_name,
        attendance=[],
    )


# yoklama baslat
@app.route("/start-attendance", methods=["POST"])
def start_attendance():

    if session.get("role") != "teacher":

        return redirect(url_for("login"))

    global current_session_id
    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at
    global current_attendance_name

    # -----------------------------------------------------
    # YOKLAMA ADINI AL
    # -----------------------------------------------------

    attendance_name = request.form.get("attendance_name", "").strip()

    if not attendance_name:

        return """
        <h1>Yoklama adı gerekli.</h1>
        <p>Lütfen yoklama adı girin.</p>
        <a href="/teacher">Geri dön</a>
        """

    # -----------------------------------------------------
    # SESSION'DAN JWT AL
    # -----------------------------------------------------

    token = session.get("teacher_token")

    print("\n==============================")
    print("YOKLAMA BAŞLATILIYOR")
    print("Teacher token var mı:", bool(token))
    print("Backend:", BACKEND_URL)
    print("Yoklama adı:", attendance_name)

    if not token:

        print("Teacher token bulunamadı.")

        session.clear()

        return redirect(url_for("login"))

    # -----------------------------------------------------
    # NODE.JS'E YOKLAMA BAŞLATMA İSTEĞİ
    # -----------------------------------------------------

    try:

        response = requests.post(
            f"{BACKEND_URL}/attendance/session",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"attendanceName": attendance_name},
            timeout=5,
        )

    except requests.RequestException as error:

        print("NODE.JS BAĞLANTI HATASI:", error)

        return """
        <h1>Backend bağlantı hatası</h1>
        <p>Node.js backend'e ulaşılamadı.</p>
        <a href="/teacher">Geri dön</a>
        """

    print("Node.js status:", response.status_code)

    print("Node.js response:", response.text)

    # -----------------------------------------------------
    # BAŞARILI
    # -----------------------------------------------------

    if response.status_code in [200, 201]:

        data = response.json()

        attendance_session = data.get("session", {})

        # SESSION ID
        current_session_id = attendance_session.get("id")

        # YOKLAMA ADI
        current_attendance_name = attendance_session.get(
            "attendance_name", attendance_name
        )

        # TOPLAM SÜRE
        total_expires_at = attendance_session.get("total_expires_at")

        if total_expires_at:

            try:

                total_expires_at = total_expires_at.replace("Z", "+00:00")

                attendance_window_expires_at = datetime.fromisoformat(
                    total_expires_at
                ).timestamp()

            except Exception as error:

                print("Toplam tarih dönüştürme hatası:", error)

                attendance_window_expires_at = time.time() + 120

        else:

            attendance_window_expires_at = time.time() + 120

        # QR TOKEN
        current_qr_token = attendance_session.get("qr_token")

        # QR SÜRESİ
        expires_at = attendance_session.get("expires_at")

        if expires_at:

            try:

                expires_at = expires_at.replace("Z", "+00:00")

                current_qr_expires_at = datetime.fromisoformat(expires_at).timestamp()

            except Exception as error:

                print("QR tarih dönüştürme hatası:", error)

                current_qr_expires_at = time.time() + 30

        else:

            current_qr_expires_at = time.time() + 30

        print("SESSION ID:", current_session_id)

        print("QR TOKEN:", current_qr_token)

        print("QR EXPIRES:", current_qr_expires_at)

        print("TOTAL EXPIRES:", attendance_window_expires_at)

        print("==============================\n")

        return redirect(url_for("teacher"))

    # -----------------------------------------------------
    # NODE.JS HATASI
    # -----------------------------------------------------

    try:

        error = response.json().get("message", "Yoklama başlatılamadı.")

    except Exception:

        error = "Yoklama başlatılamadı."

    print("YOKLAMA HATASI:", error)

    return f"""
    <h1>Yoklama başlatılamadı.</h1>
    <p>{error}</p>
    <a href="/teacher">Geri dön</a>
    """


@app.route("/obs-qr-image")
def obs_qr_image():

    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at

    if current_qr_token is None:
        return "", 204

    if time.time() >= attendance_window_expires_at:
        return "", 204

    if time.time() >= current_qr_expires_at:
        return "", 204

    qr = qrcode.make(current_qr_token)

    buffer = io.BytesIO()

    qr.save(buffer, format="PNG")

    buffer.seek(0)

    return send_file(buffer, mimetype="image/png")


@app.route("/obs-qr")
def obs_qr():

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">

        <style>

            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                background: white;
                overflow: hidden;
            }

            body {
                display: flex;
                align-items: center;
                justify-content: center;
            }

            #qr {
                width: 80vmin;
                height: 80vmin;
                object-fit: contain;
            }

        </style>

    </head>

    <body>

        <img id="qr" alt="QR">

        <script>

            async function updateQR() {

                const qr = document.getElementById("qr");

                qr.src =
                    "/obs-qr-image?t=" +
                    Date.now();

            }

            updateQR();

            setInterval(
                updateQR,
                500
            );

        </script>

    </body>
    </html>
    """


@app.route("/api/teacher-state")
def teacher_state():

    if session.get("role") != "teacher":

        return {"error": "Yetkisiz"}, 401

    global current_session_id
    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at
    global current_attendance_name

    qr_image = None
    remaining_seconds = 0
    total_remaining_seconds = 0
    session_finished = False

    token = session.get("teacher_token")

    # =====================================================
    # AKTİF YOKLAMA YOKSA
    # =====================================================

    if current_session_id is None:

        attendance = []

        return {
            "qr_image": None,
            "remaining_seconds": 0,
            "total_remaining_seconds": 0,
            "attendance_name": None,
            "session_id": None,
            "session_finished": False,
            "attendance": attendance,
        }

    # =====================================================
    # TOPLAM 120 SANİYE KONTROLÜ
    # =====================================================

    total_remaining_seconds = max(0, int(attendance_window_expires_at - time.time()))

    if total_remaining_seconds <= 0:

        print("120 saniye doldu. Yoklama sonlandırılıyor.")

        # Backend'de session'ı kapat
        if token:

            try:

                response = requests.post(
                    f"{BACKEND_URL}/attendance/session/" f"{current_session_id}/end",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    timeout=5,
                )

                print("Otomatik sonlandırma:", response.status_code, response.text)

            except requests.RequestException as error:

                print("Otomatik sonlandırma hatası:", error)

        current_session_id = None
        current_qr_token = None
        current_qr_expires_at = 0
        attendance_window_expires_at = 0

        session_finished = True

        attendance = []

        return {
            "qr_image": None,
            "remaining_seconds": 0,
            "total_remaining_seconds": 0,
            "attendance_name": current_attendance_name,
            "session_id": None,
            "session_finished": session_finished,
            "attendance": attendance,
        }

    # =====================================================
    # QR YOKSA - AYNI SESSION İÇİN QR YENİLE
    # =====================================================

    if current_qr_token is None and token:

        try:

            response = requests.post(
                f"{BACKEND_URL}/attendance/session/" f"{current_session_id}/refresh",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=5,
            )

            if response.status_code == 200:

                data = response.json()

                attendance_session = data.get("session", {})

                current_qr_token = attendance_session.get("qr_token")

                current_attendance_name = attendance_session.get(
                    "attendance_name", current_attendance_name
                )

                expires_at = attendance_session.get("expires_at")

                if expires_at:

                    try:

                        expires_at = expires_at.replace("Z", "+00:00")

                        current_qr_expires_at = datetime.fromisoformat(
                            expires_at
                        ).timestamp()

                    except Exception:

                        current_qr_expires_at = time.time() + 30

                else:

                    current_qr_expires_at = time.time() + 30

                print("Aynı yoklama için yeni QR:", current_qr_token)

            else:

                print("QR yenilenemedi:", response.text)

        except requests.RequestException as error:

            print("QR yenileme bağlantı hatası:", error)

    # =====================================================
    # MEVCUT QR
    # =====================================================

    if current_qr_token is not None:

        qr_remaining = max(0, int(current_qr_expires_at - time.time()))

        if qr_remaining <= 0:

            current_qr_token = None
            current_qr_expires_at = 0

        else:

            remaining_seconds = qr_remaining

            qr = qrcode.make(current_qr_token)

            buffer = io.BytesIO()

            qr.save(buffer, format="PNG")

            qr_image = base64.b64encode(buffer.getvalue()).decode()

    # =====================================================
    # YOKLAMA LİSTESİ
    # =====================================================

    attendance = []

    if token and current_session_id is not None:

        try:

            response = requests.get(
                f"{BACKEND_URL}/attendance/current",
                params={"sessionId": current_session_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )

            if response.status_code == 200:

                data = response.json()

                attendance = data.get("attendance", [])

            else:

                print("Yoklama listesi status:", response.status_code)

                print("Yoklama listesi response:", response.text)

        except requests.RequestException as error:

            print("Yoklama listesi bağlantı hatası:", error)

    return {
        "qr_image": qr_image,
        "remaining_seconds": remaining_seconds,
        "total_remaining_seconds": total_remaining_seconds,
        "attendance_name": current_attendance_name,
        "session_id": current_session_id,
        "session_finished": False,
        "attendance": attendance,
    }


@app.route("/refresh-qr", methods=["POST"])
def refresh_qr():

    if session.get("role") != "teacher":
        return {"error": "Yetkisiz"}, 401

    global current_session_id
    global current_qr_token
    global current_qr_expires_at

    token = session.get("teacher_token")

    if not token:
        return {"error": "Token bulunamadı"}, 401

    if current_session_id is None:
        return {"error": "Aktif yoklama yok"}, 400

    try:

        response = requests.post(
            f"{BACKEND_URL}/attendance/session/" f"{current_session_id}/refresh",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )

        if response.status_code != 200:

            print("QR yenileme hatası:", response.status_code, response.text)

            return {"error": "QR yenilenemedi."}, response.status_code

        data = response.json()

        attendance_session = data.get("session", {})

        current_qr_token = attendance_session.get("qr_token")

        expires_at = attendance_session.get("expires_at")

        if expires_at:

            try:

                expires_at = expires_at.replace("Z", "+00:00")

                current_qr_expires_at = datetime.fromisoformat(expires_at).timestamp()

            except Exception:

                current_qr_expires_at = time.time() + 30

        else:

            current_qr_expires_at = time.time() + 30

        print("Manuel QR yenilendi:", current_qr_token)

        return {"success": True}

    except requests.RequestException as error:

        print("QR yenileme bağlantı hatası:", error)

        return {"error": "Backend'e bağlanılamadı."}, 500


@app.route("/api/attendance-history")
def attendance_history():

    if session.get("role") != "teacher":

        return {"error": "Yetkisiz"}, 401

    token = session.get("teacher_token")

    if not token:

        return {"error": "Token bulunamadı"}, 401

    try:

        response = requests.get(
            f"{BACKEND_URL}/attendance/history",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5,
        )

        return (response.json(), response.status_code)

    except requests.RequestException as error:

        print("Eski yoklamalar bağlantı hatası:", error)

        return {"error": "Backend'e bağlanılamadı."}, 500


# =========================================================
# YOKLAMAYI MANUEL SONLANDIR
# =========================================================


@app.route("/end-attendance", methods=["POST"])
def end_attendance():

    if session.get("role") != "teacher":

        return redirect(url_for("login"))

    global current_session_id
    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at
    global current_attendance_name

    token = session.get("teacher_token")

    if current_session_id is None:

        return redirect(url_for("teacher"))

    try:

        response = requests.post(
            f"{BACKEND_URL}/attendance/session/" f"{current_session_id}/end",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=5,
        )

        print("Yoklama sonlandırma:", response.status_code, response.text)

    except requests.RequestException as error:

        print("Yoklama sonlandırma bağlantı hatası:", error)

    current_session_id = None
    current_qr_token = None
    current_qr_expires_at = 0
    attendance_window_expires_at = 0
    current_attendance_name = None

    return redirect(url_for("teacher"))


# =========================================================
# YOKLAMA LİSTESİ
# =========================================================


@app.route("/attendance-list")
def attendance_list():

    if session.get("role") != "teacher":

        return redirect(url_for("login"))

    token = session.get("teacher_token")

    attendance = []

    if token and current_session_id is not None:

        try:

            response = requests.get(
                f"{BACKEND_URL}/attendance/current",
                params={"sessionId": current_session_id},
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )

            if response.status_code == 200:

                data = response.json()

                attendance = data.get("attendance", [])

            else:

                print("Yoklama listesi status:", response.status_code)

                print("Yoklama listesi response:", response.text)

        except requests.RequestException as error:

            print("Yoklama listesi bağlantı hatası:", error)

    return render_template("attendance_list.html", attendance=attendance)


# =========================================================
# ANA SAYFA
# =========================================================


@app.route("/home")
def home():

    if session.get("role") != "teacher":

        return redirect(url_for("login"))

    return redirect(url_for("teacher"))


# =========================================================
# LOGOUT
# =========================================================


@app.route("/logout")
def logout():

    global current_session_id
    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at
    global current_attendance_name

    current_session_id = None
    current_qr_token = None
    current_qr_expires_at = 0
    attendance_window_expires_at = 0
    current_attendance_name = None

    session.clear()

    return redirect(url_for("login"))


# =========================================================
# UYGULAMAYI BAŞLAT
# =========================================================

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5002, debug=True)
