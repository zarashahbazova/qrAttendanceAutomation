import os
import time
import requests
import cv2

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

last_update_id = None
last_chat_id = None

os.makedirs("received_qr", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)


# ==========================================
# TELEGRAM'DAN YENİ MESAJLARI AL
# ==========================================

def get_updates():

    global last_update_id

    params = {}

    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    response = requests.get(
        f"{BASE_URL}/getUpdates",
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise Exception(
            f"Telegram API hatası: {data}"
        )

    return data["result"]


# ==========================================
# TELEGRAM'DAKİ FOTOĞRAFI İNDİR
# ==========================================

def download_file(file_id):

    response = requests.get(
        f"{BASE_URL}/getFile",
        params={
            "file_id": file_id
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise Exception(
            f"Telegram getFile hatası: {data}"
        )

    file_path = data["result"]["file_path"]

    file_url = (
        f"https://api.telegram.org/file/"
        f"bot{TOKEN}/{file_path}"
    )

    image_response = requests.get(
        file_url,
        timeout=20
    )

    image_response.raise_for_status()

    local_path = "received_qr/qr.jpg"

    with open(local_path, "wb") as file:
        file.write(image_response.content)

    return local_path


# ==========================================
# FOTOĞRAFTAKİ QR'I OKU
# ==========================================

def read_qr(image_path):

    image = cv2.imread(image_path)

    if image is None:
        print("❌ Fotoğraf açılamadı.")
        return None

    detector = cv2.QRCodeDetector()

    data, points, _ = detector.detectAndDecode(image)

    if data:
        return data.strip()

    return None


# ==========================================
# EN NET SCREENSHOT'I AL
# ==========================================

def take_best_screenshot():

    options = UiAutomator2Options()

    options.platform_name = "Android"
    options.device_name = "emulator-5554"
    options.automation_name = "UiAutomator2"

    driver = None
    screenshots = []

    try:

        print("📱 Appium emulator'e bağlanıyor...")

        driver = webdriver.Remote(
            "http://127.0.0.1:4723",
            options=options
        )

        print("✅ Appium bağlandı.")
        print("📸 3 hızlı screenshot alınıyor...")

        for i in range(3):

            path = f"screenshots/shot_{i}.png"

            driver.save_screenshot(path)

            image = cv2.imread(path)

            if image is None:
                print(
                    f"❌ Screenshot okunamadı: {path}"
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
                (path, sharpness)
            )

            print(
                f"📷 Fotoğraf {i + 1}: "
                f"netlik = {sharpness:.2f}"
            )

            time.sleep(0.1)

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
        print("Dosya:", best_path)
        print(f"Netlik: {best_score:.2f}")
        print()

        return best_path

    finally:

        if driver:
            driver.quit()


# ==========================================
# FOTOĞRAFI TELEGRAM'A GÖNDER
# ==========================================

def send_photo_to_telegram(
    chat_id,
    image_path
):

    print("📤 Screenshot Telegram'a gönderiliyor...")

    with open(image_path, "rb") as photo:

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
            f"Telegram sendPhoto hatası: {data}"
        )

    print("✅ Screenshot Telegram'a gönderildi.")


# ==========================================
# SCREENSHOT + TELEGRAM
# ==========================================

def capture_and_send_screenshot():

    global last_chat_id

    if not last_chat_id:

        print(
            "❌ Screenshot gönderilemedi: "
            "Telegram chat ID bulunamadı."
        )

        return False

    try:

        print()
        print("--------------------------------------")
        print("📱 Screenshot işlemi başlıyor...")
        print("--------------------------------------")

        best_path = take_best_screenshot()

        send_photo_to_telegram(
            last_chat_id,
            best_path
        )

        return True

    except Exception as e:

        print()
        print("❌ Screenshot/Telegram hatası:")
        print(e)

        return False


# ==========================================
# ANA PROGRAM
# ==========================================

print()
print("======================================")
print("Telegram QR dinleyicisi başladı.")
print("Yeni QR bekleniyor...")
print("======================================")
print()


while True:

    try:

        updates = get_updates()

        for update in updates:

            last_update_id = update["update_id"]

            message = update.get(
                "message",
                {}
            )

            # ----------------------------------
            # CHAT ID'Yİ AL
            # ----------------------------------

            chat_id = message.get(
                "chat",
                {}
            ).get("id")

            if chat_id:

                last_chat_id = chat_id

                print(
                    f"💬 Telegram chat ID kaydedildi: "
                    f"{last_chat_id}"
                )

            # ----------------------------------
            # FOTOĞRAF VAR MI?
            # ----------------------------------

            photo = message.get("photo")

            if not photo:
                continue

            print()
            print("--------------------------------------")
            print("📷 Telegram'dan fotoğraf geldi!")
            print("--------------------------------------")

            # Telegram'ın en büyük fotoğrafını seç
            largest_photo = photo[-1]

            file_id = largest_photo["file_id"]

            # Fotoğrafı indir
            image_path = download_file(file_id)

            print("✅ Fotoğraf indirildi:")
            print(image_path)

            # QR'ı oku
            qr_data = read_qr(image_path)

            if not qr_data:

                print("❌ QR okunamadı.")
                print("Yeni QR bekleniyor...")
                continue

            print()
            print("✅ QR OKUNDU!")
            print()
            print("QR içeriği:")
            print(qr_data)
            print()

            print("Yeni QR bekleniyor...")

        time.sleep(0.5)

    except requests.exceptions.RequestException as e:

        print()
        print("❌ Telegram bağlantı hatası:")
        print(e)

        time.sleep(2)

    except Exception as e:

        print()
        print("❌ Hata:")
        print(e)

        time.sleep(2)