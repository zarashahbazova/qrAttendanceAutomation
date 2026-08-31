import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import time
import sys

from appium import webdriver
from appium.options.android import UiAutomator2Options

AVD_NAME = "qr1"

ADB = "/Users/zarashahbazova/Library/Android/sdk/platform-tools/adb"

EMULATOR = "/Users/zarashahbazova/Library/Android/sdk/emulator/emulator"

APPIUM_SERVER = "http://127.0.0.1:4723"

APP_PACKAGE = "com.example.qr_app"


def select_apk():

    apk_path = filedialog.askopenfilename(
        title="APK seç", filetypes=[("Android APK", "*.apk"), ("Tüm dosyalar", "*.*")]
    )

    if not apk_path:
        return

    apk_label.config(text=apk_path)

    selected_apk.set(apk_path)


def start_emulator(apk_path=None):
    
    if apk_path is None:
        apk_path = selected_apk.get()

    if not apk_path:

        messagebox.showwarning("APK seçilmedi", "Önce bir APK seç.")

        return

    start_button.config(state="disabled")

    status_label.config(text="Emulator hazırlanıyor...")

    root.update()

    # =====================================================
    # EMULATOR
    # =====================================================

    result = subprocess.run([ADB, "devices"], capture_output=True, text=True)

    emulator_already_running = "emulator-5554\tdevice" in result.stdout

    if not emulator_already_running:

        status_label.config(text="Emulator başlatılıyor...")

        root.update()

        subprocess.Popen(
            [EMULATOR, "-avd", AVD_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # =====================================================
    # EMULATOR HAZIR OLANA KADAR BEKLE
    # =====================================================

    status_label.config(text="Emulator açılıyor...")

    root.update()

    while True:

        result = subprocess.run([ADB, "devices"], capture_output=True, text=True)

        if "emulator-5554\tdevice" in result.stdout:
            break

        time.sleep(2)

        root.update()

    # =====================================================
    # APK KUR
    # =====================================================

    status_label.config(text="APK kuruluyor...")

    root.update()

    install_result = subprocess.run(
        [ADB, "-s", "emulator-5554", "install", "-r", apk_path],
        capture_output=True,
        text=True,
    )

    if install_result.returncode != 0:

        messagebox.showerror(
            "APK kurulamadı", install_result.stdout + "\n" + install_result.stderr
        )

        status_label.config(text="APK kurulamadı.")

        start_button.config(state="normal")

        return

    # =====================================================
    # APPIUM İLE UYGULAMAYI AÇ
    # =====================================================

    status_label.config(text="Appium uygulamaya bağlanıyor...")

    root.update()

    try:

        options = UiAutomator2Options()

        options.platform_name = "Android"

        options.automation_name = "UiAutomator2"

        options.device_name = "emulator-5554"

        options.udid = "emulator-5554"

        options.app_package = APP_PACKAGE

        options.app_activity = "com.example.qr_app.MainActivity"

        options.no_reset = True

        driver = webdriver.Remote(APPIUM_SERVER, options=options)

        status_label.config(text="Uygulama başarıyla açıldı.")

        messagebox.showinfo("Başarılı", "APK kuruldu ve Appium ile uygulama açıldı.")

        # Driver'ı kapatmıyoruz.
        # Çünkü sonraki aşamada aynı bağlantıyı
        # login ve kamera otomasyonu için kullanacağız.

    except Exception as error:

        print("Appium bağlantı hatası:", error)

        status_label.config(text="APK kuruldu fakat Appium bağlanamadı.")

        messagebox.showerror("Appium hatası", str(error))

    finally:

        start_button.config(state="normal")


# =========================================================
# ARAYÜZ
# =========================================================

root = tk.Tk()

root.title("APK Emulator Manager")

root.geometry("600x300")

selected_apk = tk.StringVar()


title_label = tk.Label(root, text="APK Emulator Manager", font=("Arial", 20))

title_label.pack(pady=20)


select_button = tk.Button(root, text="APK Seç", command=select_apk, width=20, height=2)

select_button.pack(pady=10)


apk_label = tk.Label(root, text="Henüz APK seçilmedi.", wraplength=550)

apk_label.pack(pady=10)


start_button = tk.Button(
    root, text="Emulatoru Başlat ve APK Kur", command=start_emulator, width=30, height=2
)

start_button.pack(pady=15)


status_label = tk.Label(root, text="Hazır")

status_label.pack(pady=10)

if len(sys.argv) > 1:
    apk_path_from_flutter = sys.argv[1]

    root.after(
        100,
        lambda: start_emulator(apk_path_from_flutter)
    )
    
root.mainloop()
