import subprocess
import shutil
import urllib.request
import time

from appium import webdriver
from appium.options.android import UiAutomator2Options

from config import (
    ADB,
    DEVICE_ID,
    PUMA_PACKAGE,
    PUMA_ACTIVITY,
    PUMA_USERNAME,
    PUMA_PASSWORD
)


def ensure_appium():
    try:
        urllib.request.urlopen(
            "http://127.0.0.1:4723/status",
            timeout=2
        )

        print("Appium zaten çalışıyor.")
        return True

    except Exception:
        pass

    appium_path = shutil.which("appium")

    if not appium_path:
        print("Appium komutu bulunamadı.")
        return False

    print("Appium çalışmıyor. Başlatılıyor...")

    subprocess.Popen(
        [
            appium_path,
            "--address",
            "127.0.0.1",
            "--port",
            "4723"
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    for _ in range(30):
        try:
            urllib.request.urlopen(
                "http://127.0.0.1:4723/status",
                timeout=2
            )

            print("Appium hazır.")
            return True

        except Exception:
            time.sleep(1)

    print("Appium başlatıldı fakat hazır olmadı.")
    return False


def connect_to_puma():

    if not ensure_appium():
        raise RuntimeError("Appium başlatılamadı.")

    options = UiAutomator2Options()

    options.platform_name = "Android"
    options.device_name = DEVICE_ID
    options.udid = DEVICE_ID

    options.app_package = PUMA_PACKAGE
    options.app_activity = PUMA_ACTIVITY

    options.automation_name = "UiAutomator2"
    options.no_reset = True

    print("Appium → Puma bağlantısı kuruluyor...")

    driver = webdriver.Remote(
        "http://127.0.0.1:4723",
        options=options
    )

    print("Appium Puma'ya bağlandı.")

    time.sleep(2)

    return driver


def login_to_puma(driver):

    print("Puma giriş ekranı kontrol ediliyor...")

    edit_texts = driver.find_elements(
        "class name",
        "android.widget.EditText"
    )

    if len(edit_texts) < 2:

        print("Zaten giriş yapılmış. Login atlanıyor.")

        return True

    print("Login ekranı bulundu.")

    username_field = edit_texts[0]
    password_field = edit_texts[1]

    username_field.click()
    username_field.send_keys(PUMA_USERNAME)

    password_field.click()
    password_field.send_keys(PUMA_PASSWORD)

    print("Öğrenci numarası ve şifre girildi.")

    try:

        login_button = driver.find_element(
            "-android uiautomator",
            'new UiSelector().text("Giriş Yap")'
        )

        login_button.click()

    except Exception:

        print(
            "Giriş Yap butonu metinle bulunamadı, "
            "koordinatla basılıyor."
        )

        driver.tap([(360, 2100)])

    print("Giriş Yap butonuna basıldı.")

    time.sleep(5)

    return True


def open_qr_scanner(driver):

    print("QR Scanner açılıyor...")

    # ÖNEMLİ:
    # Puma QR Scanner açıksa veya Puma başka bir ekrandaysa,
    # önce Puma'nın MainActivity'sini yeniden öne getiriyoruz.
    try:

        result = subprocess.run(
            [
                ADB,
                "-s",
                DEVICE_ID,
                "shell",
                "am",
                "start",
                "-n",
                f"{PUMA_PACKAGE}/{PUMA_ACTIVITY}",
                "-f",
                "0x04000000"
            ],
            capture_output=True,
            text=True,
            timeout=20
        )

        print(result.stdout)

        if result.returncode != 0:
            print(result.stderr)

    except Exception as e:

        print("Puma ana ekranına dönme hatası:", e)

    # MainActivity'nin gerçekten ekrana gelmesini bekle.
    time.sleep(2)

    try:

        driver.activate_app(PUMA_PACKAGE)

    except Exception as e:

        print("Puma activate_app hatası:", e)

    time.sleep(2)

    print("Puma ana ekranı hazır.")

    # QR butonuna bas.
    print("Puma QR butonuna basılıyor...")

    driver.tap([(320, 2270)])

    time.sleep(3)

    print("QR Scanner açıldı.")

    return True