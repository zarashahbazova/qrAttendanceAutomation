import subprocess
import shutil
import urllib.request
import time

from appium import webdriver
from appium.options.android import UiAutomator2Options

from config import (
    DEVICE_ID,
    PUMA_PACKAGE,
    PUMA_ACTIVITY,
    PUMA_USERNAME,
    PUMA_PASSWORD
)


_DRIVER = None


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

    global _DRIVER

    if not ensure_appium():
        raise RuntimeError("Appium başlatılamadı.")

    # Daha önce kurulmuş çalışan bağlantı varsa onu kullan.
    if _DRIVER is not None:

        try:

            _DRIVER.current_package

            print("Mevcut Appium Puma bağlantısı kullanılıyor.")

            return _DRIVER

        except Exception:

            try:
                _DRIVER.quit()
            except Exception:
                pass

            _DRIVER = None

    options = UiAutomator2Options()

    options.platform_name = "Android"
    options.device_name = DEVICE_ID
    options.udid = DEVICE_ID

    options.app_package = PUMA_PACKAGE
    options.app_activity = PUMA_ACTIVITY

    options.automation_name = "UiAutomator2"

    options.no_reset = True

    print("Appium → Puma bağlantısı kuruluyor...")

    _DRIVER = webdriver.Remote(
        "http://127.0.0.1:4723",
        options=options
    )

    print("Appium Puma'ya bağlandı.")

    time.sleep(2)

    return _DRIVER


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

    # Önce Puma'yı öne getir.
    try:

        driver.activate_app(PUMA_PACKAGE)

        time.sleep(2)

    except Exception as e:

        print("Puma öne getirilemedi:", e)

    # Puma ana sayfasındaki QR butonu.
    driver.tap([(320, 2270)])

    time.sleep(3)

    print("QR Scanner açıldı.")

    return True