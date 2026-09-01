import subprocess
import time
import sys
import re
import glob

from appium import webdriver
from appium.options.android import UiAutomator2Options

AVD_NAME = "qr1"

ADB = "/Users/zarashahbazova/Library/Android/sdk/platform-tools/adb"

EMULATOR = "/Users/zarashahbazova/Library/Android/sdk/emulator/emulator"

APPIUM_SERVER = "http://127.0.0.1:4723"


# AAPT aracının yolunu bul
def find_aapt():

    paths = glob.glob("/Users/zarashahbazova/Library/Android/sdk/build-tools/*/aapt")

    if not paths:

        raise Exception("AAPT bulunamadı.")

    paths.sort()

    return paths[-1]


# APK package ve activity bilgisini bul
def get_apk_info(apk_path):

    aapt = find_aapt()

    result = subprocess.run(
        [aapt, "dump", "badging", apk_path], capture_output=True, text=True
    )

    if result.returncode != 0:

        raise Exception("APK bilgileri okunamadı:\n" + result.stderr)

    package_match = re.search(r"package: name='([^']+)'", result.stdout)

    activity_match = re.search(r"launchable-activity: name='([^']+)'", result.stdout)

    if not package_match:

        raise Exception("APK package adı bulunamadı.")

    package_name = package_match.group(1)

    activity_name = None

    if activity_match:

        activity_name = activity_match.group(1)

    return package_name, activity_name


# Emulator tamamen hazır olana kadar bekle
def wait_for_emulator():

    print("Emulator bekleniyor...")

    while True:

        result = subprocess.run([ADB, "devices"], capture_output=True, text=True)

        if "emulator-5554\tdevice" not in result.stdout:

            time.sleep(2)

            continue

        boot_result = subprocess.run(
            [ADB, "-s", "emulator-5554", "shell", "getprop", "sys.boot_completed"],
            capture_output=True,
            text=True,
        )

        if boot_result.stdout.strip() != "1":

            print("Android başlatılıyor...")

            time.sleep(2)

            continue

        package_result = subprocess.run(
            [ADB, "-s", "emulator-5554", "shell", "service", "check", "package"],
            capture_output=True,
            text=True,
        )

        if "found" not in package_result.stdout:

            print("Android servisleri hazırlanıyor...")

            time.sleep(2)

            continue

        break

    print("Emulator tamamen hazır.")


# Emulatoru aç, APKyı kur ve Appium ile başlat
def install_and_start(apk_path, camera):

    if not apk_path:

        raise Exception("APK yolu gönderilmedi.")

    print("APK:", apk_path)

    print("Kamera:", camera)

    package_name, activity_name = get_apk_info(apk_path)

    print("APK package:", package_name)

    print("APK activity:", activity_name)

    result = subprocess.run([ADB, "devices"], capture_output=True, text=True)

    emulator_already_running = "emulator-5554\tdevice" in result.stdout

    if not emulator_already_running:

        print("Emulator başlatılıyor...")

        subprocess.Popen(
            [EMULATOR, "-avd", AVD_NAME, "-camera-back", camera],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    else:

        print("Emulator zaten açık.")

    wait_for_emulator()

    print("APK kuruluyor...")

    install_result = subprocess.run(
        [ADB, "-s", "emulator-5554", "install", "-r", apk_path],
        capture_output=True,
        text=True,
    )

    if install_result.returncode != 0:

        raise Exception(
            "APK kurulamadı:\n" + install_result.stdout + "\n" + install_result.stderr
        )

    print("APK başarıyla kuruldu.")

    if not activity_name:

        raise Exception("APK için launchable activity bulunamadı.")

    print("Appium'a bağlanılıyor...")

    options = UiAutomator2Options()

    options.platform_name = "Android"

    options.automation_name = "UiAutomator2"

    options.device_name = "emulator-5554"

    options.udid = "emulator-5554"

    options.app_package = package_name

    options.app_activity = activity_name

    options.no_reset = True

    driver = webdriver.Remote(APPIUM_SERVER, options=options)

    print("Uygulama Appium ile açıldı.")

    return driver


# APK ve kamera bilgisini komut satırından al
if __name__ == "__main__":

    if len(sys.argv) < 2:

        print("Hata: APK yolu verilmedi.")

        sys.exit(1)

    apk_path = sys.argv[1]

    camera = "webcam0"

    if len(sys.argv) >= 3:

        camera = sys.argv[2]

    try:

        install_and_start(apk_path, camera)

        print("İşlem tamamlandı.")

        while True:

            time.sleep(60)

    except Exception as error:

        print("Launcher hatası:", error)

        sys.exit(1)
