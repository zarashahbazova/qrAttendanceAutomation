from flask import Flask, render_template, request, redirect, url_for, session
import requests
import qrcode
import io
import base64
import time
from datetime import datetime


# =========================================================
# FLASK
# =========================================================

app = Flask(__name__)

app.secret_key = "teacher-panel-secret-key"


# =========================================================
# NODE.JS BACKEND
# =========================================================

BACKEND_URL = "http://localhost:5001"


# =========================================================
# ÖĞRETMEN HESABI
# =========================================================

TEACHER_USERNAME = "0000"
TEACHER_PASSWORD = "1234"


# =========================================================
# AKTİF QR BİLGİLERİ
# =========================================================

current_qr_token = None
current_qr_expires_at = 0
attendance_window_expires_at = 0

# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        try:

            response = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "student_number": username,
                    "password": password
                },
                timeout=5
            )

        except requests.RequestException as error:

            print(
                "LOGIN BACKEND HATASI:",
                error
            )

            return render_template(
                "login.html",
                error="Backend'e bağlanılamadı."
            )

        # -------------------------------------------------
        # BAŞARILI LOGIN
        # -------------------------------------------------

        if response.status_code == 200:

            data = response.json()

            user = data.get(
                "user",
                {}
            )

            token = data.get(
                "token"
            )

            # Öğretmen hesabı mı?
            if user.get("role") != "teacher":

                return render_template(
                    "login.html",
                    error="Bu hesap öğretmen hesabı değil."
                )

            # Token geldi mi?
            if not token:

                return render_template(
                    "login.html",
                    error="Backend token göndermedi."
                )

            # -------------------------------------------------
            # SESSION'A KAYDET
            # -------------------------------------------------

            session.clear()

            session["role"] = "teacher"

            session["username"] = user.get(
                "student_number"
            )

            session["name"] = user.get(
                "full_name"
            )

            # EN ÖNEMLİ SATIR
            session["teacher_token"] = token

            print(
                "Öğretmen login başarılı."
            )

            print(
                "Teacher token kaydedildi."
            )

            return redirect(
                url_for("teacher")
            )

        # -------------------------------------------------
        # LOGIN HATASI
        # -------------------------------------------------

        try:

            error_message = response.json().get(
                "message",
                "Kullanıcı numarası veya şifre yanlış."
            )

        except Exception:

            error_message = (
                "Kullanıcı numarası veya şifre yanlış."
            )

        return render_template(
            "login.html",
            error=error_message
        )

    return render_template(
        "login.html"
    )


# =========================================================
# ÖĞRETMEN PANELİ
# =========================================================

@app.route("/teacher")
def teacher():

    if session.get("role") != "teacher":

        return redirect(
            url_for("login")
        )

    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at
    qr_image = None
    remaining_seconds = 0

    # -----------------------------------------------------
    # AKTİF QR VAR MI?
    # -----------------------------------------------------

    if current_qr_token is not None:

        remaining_seconds = max(
            0,
            int(
                current_qr_expires_at
                - time.time()
            )
        )

        # -------------------------------------------------
        # QR HÂLÂ GEÇERLİ
        # -------------------------------------------------

        if remaining_seconds > 0:

            qr = qrcode.make(
                current_qr_token
            )

            buffer = io.BytesIO()

            qr.save(
                buffer,
                format="PNG"
            )

            qr_image = base64.b64encode(
                buffer.getvalue()
            ).decode()

        # -------------------------------------------------
        # QR SÜRESİ DOLDU
        # -------------------------------------------------

        else:

            current_qr_token = None
            current_qr_expires_at = 0

    return render_template(
        "teacher.html",
        qr_image=qr_image,
        remaining_seconds=remaining_seconds,
        attendance=[]
    )


# =========================================================
# YOKLAMAYI BAŞLAT
# =========================================================

@app.route(
    "/start-attendance",
    methods=["POST"]
)
def start_attendance():

    if session.get("role") != "teacher":

        return redirect(
            url_for("login")
        )

    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at 
    # -----------------------------------------------------
    # SESSION'DAN JWT AL
    # -----------------------------------------------------

    token = session.get(
        "teacher_token"
    )

    print("\n==============================")
    print(
        "YOKLAMA BAŞLATILIYOR"
    )
    print(
        "Teacher token var mı:",
        bool(token)
    )
    print(
        "Backend:",
        BACKEND_URL
    )

    if not token:

        print(
            "Teacher token bulunamadı."
        )

        session.clear()

        return redirect(
            url_for("login")
        )

    # -----------------------------------------------------
    # NODE.JS'E YOKLAMA BAŞLATMA İSTEĞİ
    # -----------------------------------------------------

    try:

        response = requests.post(
            f"{BACKEND_URL}/attendance/session",
            headers={
                "Authorization":
                    f"Bearer {token}",
                "Content-Type":
                    "application/json"
            },
            json={},
            timeout=5
        )

    except requests.RequestException as error:

        print(
            "NODE.JS BAĞLANTI HATASI:",
            error
        )

        return """
        <h1>Backend bağlantı hatası</h1>
        <p>Node.js backend'e ulaşılamadı.</p>
        <a href="/teacher">Geri dön</a>
        """

    print(
        "Node.js status:",
        response.status_code
    )

    print(
        "Node.js response:",
        response.text
    )

    # -----------------------------------------------------
    # BAŞARILI
    # -----------------------------------------------------

    if response.status_code in [200, 201]:
        attendance_window_expires_at = time.time() + 120

        data = response.json()

        attendance_session = data.get(
            "session",
            {}
        )

        # QR TOKEN
        current_qr_token = (
            attendance_session.get(
                "qr_token"
            )
        )

        # SÜRE
        expires_at = (
            attendance_session.get(
                "expires_at"
            )
        )

        if expires_at:

            try:

                expires_at = expires_at.replace(
                    "Z",
                    "+00:00"
                )

                current_qr_expires_at = (
                    datetime.fromisoformat(
                        expires_at
                    ).timestamp()
                )

            except Exception as error:

                print(
                    "Tarih dönüştürme hatası:",
                    error
                )

                current_qr_expires_at = (
                    time.time() + 120
                )

        else:

            current_qr_expires_at = (
                time.time() + 120
            )

        print(
            "QR TOKEN:",
            current_qr_token
        )

        print(
            "QR EXPIRES:",
            current_qr_expires_at
        )

        print(
            "==============================\n"
        )

        return redirect(
            url_for("teacher")
        )

    # -----------------------------------------------------
    # NODE.JS HATASI
    # -----------------------------------------------------

    try:

        error = response.json().get(
            "message",
            "Yoklama başlatılamadı."
        )

    except Exception:

        error = (
            "Yoklama başlatılamadı."
        )

    print(
        "YOKLAMA HATASI:",
        error
    )

    return f"""
    <h1>Yoklama başlatılamadı.</h1>
    <p>{error}</p>
    <a href="/teacher">Geri dön</a>
    """


# =========================================================
# ÖĞRETMEN EKRANI API
# =========================================================
@app.route("/api/teacher-state")
def teacher_state():

    if session.get("role") != "teacher":
        return {
            "error": "Yetkisiz"
        }, 401

    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at

    qr_image = None
    remaining_seconds = 0

    token = session.get("teacher_token")

    # =====================================================
    # TOPLAM 120 SANİYE KONTROLÜ
    # =====================================================

    if (
        attendance_window_expires_at > 0
        and time.time() >= attendance_window_expires_at
    ):
        current_qr_token = None
        current_qr_expires_at = 0
        attendance_window_expires_at = 0

    # =====================================================
    # QR YOKSA
    # =====================================================

    if (
        current_qr_token is None
        and attendance_window_expires_at > 0
        and token
    ):

        try:

            response = requests.post(
                f"{BACKEND_URL}/attendance/session",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={},
                timeout=5
            )

            if response.status_code in [200, 201]:

                data = response.json()

                attendance_session = data.get(
                    "session",
                    {}
                )

                current_qr_token = (
                    attendance_session.get(
                        "qr_token"
                    )
                )

                expires_at = (
                    attendance_session.get(
                        "expires_at"
                    )
                )

                if expires_at:

                    try:

                        expires_at = expires_at.replace(
                            "Z",
                            "+00:00"
                        )

                        current_qr_expires_at = (
                            datetime.fromisoformat(
                                expires_at
                            ).timestamp()
                        )

                    except Exception:

                        current_qr_expires_at = (
                            time.time() + 30
                        )

                else:

                    current_qr_expires_at = (
                        time.time() + 30
                    )

                print(
                    "Yeni QR oluşturuldu:",
                    current_qr_token
                )

            else:

                print(
                    "Yeni QR oluşturulamadı:",
                    response.text
                )

        except requests.RequestException as error:

            print(
                "Yeni QR bağlantı hatası:",
                error
            )

    # =====================================================
    # MEVCUT QR
    # =====================================================

    if current_qr_token is not None:

        qr_remaining = max(
            0,
            int(
                current_qr_expires_at
                - time.time()
            )
        )

        # -------------------------------------------------
        # QR SÜRESİ DOLDU
        # -------------------------------------------------

        if qr_remaining <= 0:

            current_qr_token = None
            current_qr_expires_at = 0

        else:

            remaining_seconds = qr_remaining

            qr = qrcode.make(
                current_qr_token
            )

            buffer = io.BytesIO()

            qr.save(
                buffer,
                format="PNG"
            )

            qr_image = base64.b64encode(
                buffer.getvalue()
            ).decode()

    # =====================================================
    # YOKLAMA LİSTESİ
    # =====================================================

    attendance = []

    if token:

        try:

            response = requests.get(
                f"{BACKEND_URL}/attendance/current",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=5
            )

            if response.status_code == 200:

                data = response.json()

                attendance = data.get(
                    "attendance",
                    []
                )

        except requests.RequestException as error:

            print(
                "Yoklama listesi bağlantı hatası:",
                error
            )

    return {
        "qr_image": qr_image,
        "remaining_seconds": remaining_seconds,
        "attendance": attendance
    }
# =========================================================
# YOKLAMA LİSTESİ
# =========================================================

@app.route("/attendance-list")
def attendance_list():

    if session.get("role") != "teacher":

        return redirect(
            url_for("login")
        )

    token = session.get(
        "teacher_token"
    )

    attendance = []

    if token:

        try:

            response = requests.get(
                f"{BACKEND_URL}/attendance/current",
                headers={
                    "Authorization":
                        f"Bearer {token}"
                },
                timeout=5
            )

            if response.status_code == 200:

                data = response.json()

                attendance = data.get(
                    "attendance",
                    []
                )

            else:

                print(
                    "Yoklama listesi status:",
                    response.status_code
                )

                print(
                    "Yoklama listesi response:",
                    response.text
                )

        except requests.RequestException as error:

            print(
                "Yoklama listesi bağlantı hatası:",
                error
            )

    return render_template(
        "attendance_list.html",
        attendance=attendance
    )


# =========================================================
# ANA SAYFA
# =========================================================

@app.route("/home")
def home():

    if session.get("role") != "teacher":

        return redirect(
            url_for("login")
        )

    return redirect(
        url_for("teacher")
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    global current_qr_token
    global current_qr_expires_at
    global attendance_window_expires_at
    current_qr_token = None
    current_qr_expires_at = 0


    attendance_window_expires_at = 0
    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# UYGULAMAYI BAŞLAT
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5002,
        debug=True
    )