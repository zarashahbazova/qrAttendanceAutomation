import os
import time
import requests
import cv2
import qrcode
import obsws_python as obs

from dotenv import load_dotenv
from appium import webdriver
from appium.options.android import UiAutomator2Options


# ==========================================
# AYARLAR
# ==========================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise Exception(
        "TELEGRAM_BOT_TOKEN bulunamadı!"
    )

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
BACKEND_URL = "http://127.0.0.1:5001"

# ------------------------------------------
# OBS
# ------------------------------------------

OBS_HOST = "127.0.0.1"
OBS_PORT = 4455
OBS_PASSWORD = os.getenv(
    "OBS_WEBSOCKET_PASSWORD"
)

OBS_SOURCE_NAME = "Resim"

# QR 30 saniye geçerli
QR_VALID_SECONDS = 30

# ------------------------------------------
# Telegram
# ------------------------------------------

last_chat_id = 8815799297

# ------------------------------------------
# Klasörler
# ------------------------------------------

os.makedirs(
    "screenshots",
    exist_ok=True
)

os.makedirs(
    "generated_qr",
    exist_ok=True
)

# QR'ın OBS'de ne zamana kadar kalacağını tutar
qr_display_until = None


# ==========================================
# BOŞ QR EKRANI OLUŞTUR
# ==========================================

def create_empty_image():

    empty_path = os.path.abspath(
        "generated_qr/empty.png"
    )

    if not os.path.exists(empty_path):

        image = cv2.cvtColor(
            cv2.UMat(
                480,
                640,
                cv2.CV_8UC3
            ).get(),
            cv2.COLOR_BGR2RGB
        )

        image[:, :] = 255

        cv2.imwrite(
            empty_path,
            cv2.cvtColor(
                image,
                cv2.COLOR_RGB2BGR
            )
        )

        print(
            "✅ empty.png oluşturuldu."
        )

    return empty_path


# ==========================================
# APPIUM'A BAĞLAN
# ==========================================

def connect_appium():

    options = UiAutomator2Options()

    options.platform_name = "Android"
    options.device_name = "emulator-5554"
    options.automation_name = "UiAutomator2"

    print()
    print("======================================")
    print("📱 APPIUM'A BAĞLANILIYOR...")
    print("======================================")

    driver = webdriver.Remote(
        "http://127.0.0.1:4723",
        options=options
    )

    print("✅ APPIUM BAĞLANDI.")
    print("📱 Driver hazır.")
    print()

    return driver


# ==========================================
# BACKEND'DEN SCREENSHOT EVENTİNİ KONTROL ET
# ==========================================

def check_screenshot_event():

    try:

        response = requests.get(
            f"{BACKEND_URL}/attendance/screenshot-event",
            timeout=3
        )

        response.raise_for_status()

        data = response.json()

        return data.get("event")

    except requests.exceptions.RequestException as e:

        print(
            "❌ Backend event kontrol hatası:"
        )

        print(e)

        return None


# ==========================================
# OBS WEBSOCKET'E BAĞLAN
# ==========================================

def connect_obs():

    if not OBS_PASSWORD:

        raise Exception(
            "OBS_WEBSOCKET_PASSWORD bulunamadı!"
        )

    print()
    print("======================================")
    print("🎥 OBS'YE BAĞLANILIYOR...")
    print("======================================")

    client = obs.ReqClient(
        host=OBS_HOST,
        port=OBS_PORT,
        password=OBS_PASSWORD
    )

    print(
        "✅ OBS WebSocket bağlantısı başarılı."
    )

    print()

    return client


# ==========================================
# QR TOKEN → QR GÖRÜNTÜSÜ
# ==========================================

def create_qr_image(qr_data):

    filename = (
        f"generated_qr/qr_"
        f"{int(time.time() * 1000)}.png"
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=(
            qrcode.constants.ERROR_CORRECT_M
        ),
        box_size=12,
        border=4
    )

    qr.add_data(qr_data)

    qr.make(
        fit=True
    )

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    image.save(
        filename
    )

    print()
    print("======================================")
    print(
        "✅ YENİ QR GÖRÜNTÜSÜ OLUŞTURULDU"
    )
    print("======================================")

    print(
        "Dosya:",
        filename
    )

    print()

    return os.path.abspath(
        filename
    )


# ==========================================
# QR GÖRÜNTÜSÜNÜ OBS'YE GÖNDER
# ==========================================

def send_qr_to_obs(
    obs_client,
    qr_image_path
):

    global qr_display_until

    print(
        "📺 QR görüntüsü OBS'ye gönderiliyor..."
    )

    obs_client.set_input_settings(
        OBS_SOURCE_NAME,
        {
            "file": qr_image_path
        },
        True
    )

    # 30 saniyelik süreyi başlat
    qr_display_until = (
        time.time()
        + QR_VALID_SECONDS
    )

    print(
        "✅ QR OBS'ye aktarıldı."
    )

    print(
        f"⏱️ QR {QR_VALID_SECONDS} saniye "
        "gösterilecek."
    )

    print()


# ==========================================
# OBS'DEKİ QR'I TEMİZLE
# ==========================================

def clear_qr_from_obs(
    obs_client
):

    global qr_display_until

    empty_path = create_empty_image()

    print(
        "⏰ QR süresi doldu."
    )

    print(
        "🧹 OBS ekranındaki QR temizleniyor..."
    )

    obs_client.set_input_settings(
        OBS_SOURCE_NAME,
        {
            "file": empty_path
        },
        True
    )

    qr_display_until = None

    print(
        "✅ QR OBS'den temizlendi."
    )

    print()


# ==========================================
# QR SÜRESİNİ KONTROL ET
# ==========================================

def check_qr_expiration(
    obs_client
):

    global qr_display_until

    if qr_display_until is None:

        return

    if time.time() >= qr_display_until:

        clear_qr_from_obs(
            obs_client
        )


# ==========================================
# EN NET SCREENSHOT'I AL
# ==========================================

def take_best_screenshot(
    driver
):

    screenshots = []

    print(
        "📸 3 hızlı screenshot alınıyor..."
    )

    for i in range(3):

        path = (
            f"screenshots/shot_{i}.png"
        )

        print(
            f"📷 Screenshot {i + 1} alınıyor..."
        )

        driver.save_screenshot(
            path
        )

        image = cv2.imread(
            path
        )

        if image is None:

            print(
                f"❌ Screenshot okunamadı: "
                f"{path}"
            )

            continue

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        sharpness = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()

        screenshots.append(
            (
                path,
                sharpness
            )
        )

        print(
            f"   Netlik = {sharpness:.2f}"
        )

        time.sleep(
            0.1
        )

    if not screenshots:

        raise Exception(
            "Hiç screenshot alınamadı!"
        )

    best_path, best_score = max(
        screenshots,
        key=lambda item: item[1]
    )

    print()
    print("======================================")
    print("✅ EN NET SCREENSHOT")
    print("======================================")

    print(
        "Dosya:",
        best_path
    )

    print(
        f"Netlik: {best_score:.2f}"
    )

    print()

    return best_path


# ==========================================
# SCREENSHOT İÇİNDEKİ QR'I OKU
# ==========================================

def read_qr(
    image_path
):

    image = cv2.imread(
        image_path
    )

    if image is None:

        print(
            "❌ Screenshot açılamadı."
        )

        return None

    detector = cv2.QRCodeDetector()

    data, points, _ = (
        detector.detectAndDecode(
            image
        )
    )

    if data:

        return data.strip()

    return None


# ==========================================
# FOTOĞRAFI TELEGRAM'A GÖNDER
# ==========================================

def send_photo_to_telegram(
    chat_id,
    image_path
):

    print(
        "📤 Screenshot Telegram'a gönderiliyor..."
    )

    with open(
        image_path,
        "rb"
    ) as photo:

        response = requests.post(
            f"{BASE_URL}/sendPhoto",

            data={
                "chat_id": chat_id
            },

            files={
                "photo": photo
            },

            timeout=10
        )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):

        raise Exception(
            f"Telegram sendPhoto hatası: "
            f"{data}"
        )

    print(
        "✅ Screenshot Telegram'a gönderildi."
    )


# ==========================================
# SCREENSHOT + QR + OBS + TELEGRAM
# ==========================================

def capture_and_send_screenshot(
    obs_client
):

    if not last_chat_id:

        print(
            "❌ Screenshot gönderilemedi: "
            "Telegram chat ID bulunamadı."
        )

        return

    driver = None

    try:

        print()
        print(
            "--------------------------------------"
        )

        print(
            "📱 Yeni screenshot işlemi başlıyor..."
        )

        print(
            "--------------------------------------"
        )

        # ----------------------------------
        # HER EVENT'TE YENİ APPIUM SESSION
        # ----------------------------------

        driver = connect_appium()

        # ----------------------------------
        # EN NET SCREENSHOT
        # ----------------------------------

        best_path = (
            take_best_screenshot(
                driver
            )
        )

        # ----------------------------------
        # QR OKU
        # ----------------------------------

        print(
            "🔎 Screenshot içindeki QR okunuyor..."
        )

        qr_data = read_qr(
            best_path
        )

        if qr_data:

            print()
            print(
                "======================================"
            )

            print(
                "✅ SCREENSHOT İÇİNDEKİ QR OKUNDU!"
            )

            print(
                "======================================"
            )

            print(
                "QR içeriği:"
            )

            print(
                qr_data
            )

            print()

            # ------------------------------
            # TOKEN → QR PNG
            # ------------------------------

            qr_image_path = (
                create_qr_image(
                    qr_data
                )
            )

            # ------------------------------
            # QR → OBS
            # ------------------------------

            send_qr_to_obs(
                obs_client,
                qr_image_path
            )

        else:

            print(
                "❌ Screenshot içindeki QR "
                "okunamadı."
            )

        # ----------------------------------
        # TELEGRAM
        # ----------------------------------

        send_photo_to_telegram(
            last_chat_id,
            best_path
        )

    except Exception as e:

        print()
        print(
            "❌ Screenshot/Telegram hatası:"
        )

        print(e)

        print()

    finally:

        # ----------------------------------
        # APPIUM SESSION'INI KAPAT
        # ----------------------------------

        if driver:

            try:

                print(
                    "📱 Appium session kapatılıyor..."
                )

                driver.quit()

                print(
                    "✅ Appium session kapatıldı."
                )

            except Exception as e:

                print(
                    "⚠️ Appium kapatılırken hata:"
                )

                print(e)


# ==========================================
# ANA PROGRAM
# ==========================================

print()
print(
    "======================================"
)

print(
    "Telegram QR dinleyicisi başladı."
)

print(
    "======================================"
)

print()


# ==========================================
# BAŞLANGIÇ
# ==========================================

obs_client = None

try:

    # --------------------------------------
    # OBS'YE BAĞLAN
    # --------------------------------------

    obs_client = connect_obs()

    # --------------------------------------
    # BOŞ EKRANI HAZIRLA
    # --------------------------------------

    create_empty_image()

    # --------------------------------------
    # BAŞLANGIÇTA OBS'Yİ TEMİZLE
    # --------------------------------------

    print(
        "🎯 Backend screenshot event'i "
        "bekleniyor..."
    )

    print()

    # ======================================
    # ANA DÖNGÜ
    # ======================================

    while True:

        try:

            # ------------------------------
            # QR 30 SANİYESİ DOLDU MU?
            # ------------------------------

            check_qr_expiration(
                obs_client
            )

            # ------------------------------
            # BACKEND EVENT
            # ------------------------------

            event = (
                check_screenshot_event()
            )

            if event:

                print()
                print(
                    "======================================"
                )

                print(
                    "📸 SCREENSHOT EVENT ALINDI!"
                )

                print(
                    "======================================"
                )

                print(
                    event
                )

                print()

                # --------------------------
                # SCREENSHOT + QR + OBS
                # --------------------------

                capture_and_send_screenshot(
                    obs_client
                )

            time.sleep(
                0.1
            )

        except (
            requests.exceptions.RequestException
        ) as e:

            print()
            print(
                "❌ Backend bağlantı hatası:"
            )

            print(e)

            time.sleep(
                2
            )

        except Exception as e:

            print()
            print(
                "❌ Ana döngü hatası:"
            )

            print(e)

            time.sleep(
                2
            )

finally:

    print()

    print(
        "🛑 Telegram QR dinleyicisi kapatılıyor..."
    )

    print(
        "✅ Program kapatıldı."
    )