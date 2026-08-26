"""
appium_static_qr_test.py

Emulator, `-camera-back videofile:camera_test/qr_test.mp4` ile (yani sabit,
tek seferlik bir test QR görüntüsüyle) ÖNCEDEN başlatılmış olmalı.
Bu script sadece Flutter uygulamasını (com.example.qr_app) Appium üzerinden
açar ve Scanner ekranına geçer; kamera görüntüsünü değiştirmez.

Ön koşullar:
  1. `python make_camera_video.py` ile camera_test/qr_test.mp4 üretilmiş olmalı.
  2. Emulator şu şekilde başlatılmış olmalı:
     emulator -avd <AVD_ADIN> -camera-back videofile:camera_test/qr_test.mp4
  3. Appium server ayakta olmalı (appium).
  4. Uygulama emulator'e kurulu olmalı (flutter install / apk).

Kullanım:
    python appium_static_qr_test.py
"""

import time

from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


# ==========================================
# 1. ANDROID / UYGULAMA AYARLARI
# ==========================================

APP_PACKAGE = "com.example.qr_app"
APP_ACTIVITY = ".MainActivity"

options = UiAutomator2Options()
options.platform_name = "Android"
options.device_name = "emulator-5554"
options.automation_name = "UiAutomator2"
options.app_package = APP_PACKAGE
options.app_activity = APP_ACTIVITY
# Uygulama zaten kuruluysa yeniden kurmasın, sadece açsın:
options.no_reset = True


# Test için kullanılacak kullanıcı numarası ve şifresi.
# login.dart: numberController -> "Kullanıcı Numarası" (numeric keyboard)
#             passwordController -> "Şifre"
TEST_STUDENT_NUMBER = "1001"
TEST_PASSWORD = "1111"


def main():
    driver = webdriver.Remote("http://127.0.0.1:4723", options=options)
    print(f"{APP_PACKAGE} açıldı.")

    time.sleep(3)

    # ==========================================
    # 2. GİRİŞ EKRANI
    # ==========================================
    # login.dart'ta sırasıyla iki TextField var:
    #   1) numberController -> Kullanıcı Numarası (keyboardType: number)
    #   2) passwordController -> Şifre (obscureText)
    # Flutter widget'larında ayrı bir resourceId/key olmadığı için
    # sıraya göre (class_name = EditText) eşleştiriyoruz.

    edit_texts = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")

    if len(edit_texts) >= 2:
        print("Login ekranı algılandı, numara ve şifre giriliyor...")
        number_field = edit_texts[0]
        password_field = edit_texts[1]

        number_field.click()
        number_field.send_keys(TEST_STUDENT_NUMBER)

        password_field.click()
        password_field.send_keys(TEST_PASSWORD)

        login_button = driver.find_element(
            AppiumBy.XPATH, "//*[contains(@text,'Giriş Yap')]"
        )
        login_button.click()
        print("Giriş Yap butonuna tıklandı.")
        time.sleep(3)
    else:
        print(
            "Login ekranı görünmüyor (EditText bulunamadı), "
            "muhtemelen no_reset=True nedeniyle zaten giriş yapılmış durumda."
        )

    # ==========================================
    # 3. SCANNER (KAMERA) SEKMESİNE GEÇ
    # ==========================================
    # home.dart -> alt navigasyonda 'Kamera' etiketli sekme ScannerPage'i açıyor.

    camera_tab = driver.find_element(AppiumBy.XPATH, "//*[contains(@text,'Kamera')]")
    camera_tab.click()
    print("Kamera sekmesine geçildi.")

    time.sleep(3)

    # ==========================================
    # 4. SONUCU GÖR
    # ==========================================
    # MobileScanner, emulator'ün videofile: kaynağından okuduğu sabit test
    # QR'ını algılayıp processQr() -> apiClient.joinAttendance() akışını
    # otomatik tetikleyecektir (scanner.dart zaten bunu yapıyor).
    # Ekran görüntüsü alarak sonucu doğrula:

    driver.save_screenshot("scanner_result.png")
    print("Ekran görüntüsü kaydedildi: scanner_result.png")

    time.sleep(5)

    driver.quit()
    print("Appium session kapatıldı.")


if __name__ == "__main__":
    main()