import os
import time
import cv2
import requests

from dotenv import load_dotenv
from appium import webdriver
from appium.options.android import UiAutomator2Options


# ==========================================
# ENV / TELEGRAM
# ==========================================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise Exception("TELEGRAM_BOT_TOKEN bulunamadı!")

BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


# Telegram'a gönderilecek chat ID
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not CHAT_ID:
    raise Exception("TELEGRAM_CHAT_ID bulunamadı!")


# ==========================================
# APPIUM AYARLARI
# ==========================================

options = UiAutomator2Options()

options.platform_name = "Android"
options.device_name = "emulator-5554"
options.automation_name = "UiAutomator2"


# ==========================================
# APPIUM'A BAĞLAN
# ==========================================

driver = webdriver.Remote(
    "http://127.0.0.1:4723",
    options=options
)

print("✅ Appium bağlandı.")


# ==========================================
# SCREENSHOT KLASÖRÜ
# ==========================================

os.makedirs("screenshots", exist_ok=True)


# ==========================================
# 3 HIZLI SCREENSHOT AL
# ==========================================

screenshots = []

print()
print("📸 3 hızlı screenshot alınıyor...")

for i in range(3):

    path = f"screenshots/shot_{i}.png"

    driver.save_screenshot(path)

    image = cv2.imread(path)

    if image is None:
        print(f"❌ Screenshot okunamadı: {path}")
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


# ==========================================
# EN NET FOTOĞRAFI SEÇ
# ==========================================

if not screenshots:

    driver.quit()

    raise Exception(
        "Hiç screenshot alınamadı!"
    )


best_path, best_score = max(
    screenshots,
    key=lambda item: item[1]
)


print()
print("======================================")
print("✅ EN NET FOTOĞRAF SEÇİLDİ")
print("======================================")
print("Dosya:", best_path)
print(f"Netlik: {best_score:.2f}")
print()


# ==========================================
# TELEGRAM'A FOTOĞRAF GÖNDER
# ==========================================

print("📤 En net fotoğraf Telegram'a gönderiliyor...")

with open(best_path, "rb") as photo:

    response = requests.post(
        f"{BASE_URL}/sendPhoto",
        data={
            "chat_id": CHAT_ID
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
        f"Telegram fotoğraf gönderme hatası: {data}"
    )


print("✅ Fotoğraf Telegram'a gönderildi.")


# ==========================================
# APPIUM BAĞLANTISINI KAPAT
# ==========================================

driver.quit()

print("✅ Appium bağlantısı kapatıldı.")