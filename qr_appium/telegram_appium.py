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
    raise Exception("TELEGRAM_BOT_TOKEN bulunamadı!")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
BACKEND_URL = "http://127.0.0.1:5001"


# ==========================================
# OBS
# ==========================================

OBS_HOST = "127.0.0.1"
OBS_PORT = 4455

OBS_PASSWORD = os.getenv("OBS_WEBSOCKET_PASSWORD")

OBS_SOURCE_NAME = "Resim"


# ==========================================
# QR AYARLARI
# ==========================================

QR_VALID_SECONDS = 30

# Aynı QR tekrar tekrar işlenmesin
last_qr_data = None

# OBS'deki QR'ın ne zamana kadar gösterileceği
qr_display_until = None


# ==========================================
# TELEGRAM
# ==========================================

last_chat_id = 8815799297


# ==========================================
# KLASÖRLER
# ==========================================

os.makedirs("screenshots", exist_ok=True)

os.makedirs("generated_qr", exist_ok=True)


# ==========================================
# BOŞ EKRAN OLUŞTUR
# ==========================================


def create_empty_image():

    empty_path = os.path.abspath("generated_qr/empty.png")

    if not os.path.exists(empty_path):

        image = cv2.imread("generated_qr/empty.png")

        if image is None:

            image = 255 * __import__("numpy").ones(
                (480, 640, 3), dtype=__import__("numpy").uint8
            )

            cv2.imwrite(empty_path, image)

        print("✅ empty.png oluşturuldu.")

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

    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)

    print("✅ APPIUM BAĞLANDI.")

    print("📱 Driver hazır.")

    print()

    return driver


# ==========================================
# OBS'YE BAĞLAN
# ==========================================


def connect_obs():

    if not OBS_PASSWORD:

        raise Exception("OBS_WEBSOCKET_PASSWORD bulunamadı!")

    print()
    print("======================================")

    print("🎥 OBS'YE BAĞLANILIYOR...")

    print("======================================")

    client = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD)

    print("✅ OBS WebSocket bağlantısı başarılı.")

    print()

    return client


# ==========================================
# QR TOKEN → QR GÖRÜNTÜSÜ
# ==========================================


def create_qr_image(qr_data):

    filename = "generated_qr/qr_" f"{int(time.time() * 1000)}.png"

    qr = qrcode.QRCode(
        version=None,
        error_correction=(qrcode.constants.ERROR_CORRECT_M),
        box_size=12,
        border=4,
    )

    qr.add_data(qr_data)

    qr.make(fit=True)

    image = qr.make_image(fill_color="black", back_color="white")

    image.save(filename)

    print()
    print("======================================")

    print("✅ YENİ QR GÖRÜNTÜSÜ OLUŞTURULDU")

    print("======================================")

    print("Dosya:", filename)

    print()

    return os.path.abspath(filename)


# ==========================================
# QR'I OBS'YE GÖNDER
# ==========================================


def send_qr_to_obs(obs_client, qr_image_path):

    global qr_display_until

    print("📺 QR görüntüsü OBS'ye gönderiliyor...")

    obs_client.set_input_settings(OBS_SOURCE_NAME, {"file": qr_image_path}, True)

    qr_display_until = time.time() + QR_VALID_SECONDS

    print("✅ QR OBS'ye aktarıldı.")

    print(f"⏱️ QR {QR_VALID_SECONDS} saniye " "gösterilecek.")

    print()


# ==========================================
# OBS'DEKİ QR'I TEMİZLE
# ==========================================


def clear_qr_from_obs(obs_client):

    global qr_display_until

    empty_path = create_empty_image()

    print("⏰ QR süresi doldu.")

    print("🧹 OBS ekranındaki QR temizleniyor...")

    obs_client.set_input_settings(OBS_SOURCE_NAME, {"file": empty_path}, True)

    qr_display_until = None

    print("✅ QR OBS'den temizlendi.")

    print()


# ==========================================
# QR SÜRESİ DOLDU MU?
# ==========================================


def check_qr_expiration(obs_client):

    global qr_display_until

    if qr_display_until is None:
        return

    if time.time() >= qr_display_until:

        clear_qr_from_obs(obs_client)


# ==========================================
# QR OKU
# ==========================================


def read_qr(image_path):

    image = cv2.imread(image_path)

    if image is None:

        return None

    detector = cv2.QRCodeDetector()

    data, points, _ = detector.detectAndDecode(image)

    if data:

        return data.strip()

    return None


# ==========================================
# TELEGRAM'A FOTO GÖNDER
# ==========================================


def send_photo_to_telegram(chat_id, image_path):

    print("📤 Screenshot Telegram'a gönderiliyor...")

    with open(image_path, "rb") as photo:

        response = requests.post(
            f"{BASE_URL}/sendPhoto",
            data={"chat_id": chat_id},
            files={"photo": photo},
            timeout=10,
        )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):

        raise Exception(f"Telegram sendPhoto hatası: {data}")

    print("✅ Screenshot Telegram'a gönderildi.")


# ==========================================
# QR BULUNDUĞUNDA İŞLE
# ==========================================


def process_qr(driver, obs_client, qr_data, screenshot_path):

    global last_qr_data

    # Aynı QR tekrar işlenmesin
    if qr_data == last_qr_data:
        return

    print()
    print("======================================")
    print("🎯 YENİ QR BULUNDU!")
    print("======================================")
    print("QR:", qr_data)
    print()

    # --------------------------------------
    # QR'I BULDUĞUMUZ AYNI SCREENSHOT
    # TELEGRAM'A GÖNDER
    # --------------------------------------

    print("📸 QR screenshot hazır.")

    send_photo_to_telegram(last_chat_id, screenshot_path)

    # --------------------------------------
    # TOKEN → YENİ QR
    # --------------------------------------

    qr_image_path = create_qr_image(qr_data)

    # --------------------------------------
    # YENİ QR → OBS
    # --------------------------------------

    send_qr_to_obs(obs_client, qr_image_path)

    # --------------------------------------
    # SON QR'I HATIRLA
    # --------------------------------------

    last_qr_data = qr_data

    print()
    print("======================================")
    print("✅ QR İŞLEMİ TAMAMLANDI")
    print("======================================")
    print()


# ==========================================
# APPIUM EKRANINI SÜREKLİ KONTROL ET
# ==========================================


def watch_for_qr(driver, obs_client):

    global last_qr_data

    print()
    print("======================================")

    print("👀 EMULATOR EKRANI İZLENİYOR...")

    print("QR görünür görünmez alınacak.")

    print("======================================")

    print()

    last_scan_time = 0

    while True:

        try:

            # ----------------------------------
            # QR SÜRESİNİ KONTROL ET
            # ----------------------------------

            check_qr_expiration(obs_client)

            # ----------------------------------
            # ÇOK SIK SCREENSHOT ALMAYALIM
            # ----------------------------------

            now = time.time()

            if now - last_scan_time < 0.2:

                time.sleep(0.05)

                continue

            last_scan_time = now

            # ----------------------------------
            # SCREENSHOT
            # ----------------------------------

            path = "screenshots/current_scan.png"

            driver.save_screenshot(path)

            # ----------------------------------
            # QR'I OKU
            # ----------------------------------

            qr_data = read_qr(path)

            # ----------------------------------
            # QR BULUNDU
            # ----------------------------------

            if qr_data:

                process_qr(driver, obs_client, qr_data, path)

            time.sleep(0.05)

        except Exception as e:

            print()
            print("⚠️ QR izleme hatası:")

            print(e)

            print("🔄 Appium yeniden bağlanacak.")

            break


# ==========================================
# ANA PROGRAM
# ==========================================

print()
print("======================================")

print("Telegram QR sistemi başladı.")

print("======================================")

print()


obs_client = None
driver = None


try:

    # ======================================
    # OBS
    # ======================================

    obs_client = connect_obs()

    create_empty_image()

    print("🎯 OBS hazır.")

    print()

    # ======================================
    # APPIUM
    # ======================================

    driver = connect_appium()

    # ======================================
    # QR İZLE
    # ======================================

    while True:

        try:

            watch_for_qr(driver, obs_client)

        except Exception as e:

            print()
            print("❌ Appium izleme hatası:")

            print(e)

        # ----------------------------------
        # Appium session düşerse yeniden bağlan
        # ----------------------------------

        if driver:

            try:
                driver.quit()
            except:
                pass

        print()
        print("🔄 Appium yeniden bağlanıyor...")

        time.sleep(1)

        driver = connect_appium()


finally:

    if driver:

        try:

            driver.quit()

        except:
            pass

    print()
    print("🛑 Telegram QR sistemi kapatıldı.")
