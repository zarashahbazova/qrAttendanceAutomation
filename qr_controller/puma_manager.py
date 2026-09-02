import os
import subprocess

from config import (
    ADB,
    DEVICE_ID,
    PUMA_PACKAGE,
    PUMA_ACTIVITY,
    PUMA_APK_DIR
)


def is_puma_installed():
    try:
        result = subprocess.run(
            [
                ADB,
                "-s",
                DEVICE_ID,
                "shell",
                "pm",
                "list",
                "packages"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        return f"package:{PUMA_PACKAGE}" in result.stdout

    except Exception as e:
        print("Puma kontrol hatası:", e)
        return False


def get_puma_apks():
    if not os.path.exists(PUMA_APK_DIR):
        return []

    apk_files = []

    for filename in os.listdir(PUMA_APK_DIR):
        if filename.endswith(".apk"):
            apk_files.append(
                os.path.join(PUMA_APK_DIR, filename)
            )

    return apk_files


def install_puma():
    apk_files = get_puma_apks()

    if not apk_files:
        print("Puma APK dosyaları bulunamadı.")
        return False

    print("Puma kurulu değil.")
    print("Puma APK'ları kuruluyor...")

    try:
        command = [
            ADB,
            "-s",
            DEVICE_ID,
            "install-multiple",
            "-r"
        ]

        command.extend(apk_files)

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120
        )

        print(result.stdout)

        if result.returncode != 0:
            print("Puma kurulum hatası:")
            print(result.stderr)
            return False

        print("Puma başarıyla kuruldu.")
        return True

    except Exception as e:
        print("Puma kurulum hatası:", e)
        return False


def start_puma():
    print("Puma başlatılıyor...")

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
                f"{PUMA_PACKAGE}/{PUMA_ACTIVITY}"
            ],
            capture_output=True,
            text=True,
            timeout=20
        )

        print(result.stdout)

        if result.returncode != 0:
            print(result.stderr)
            return False

        print("Puma açıldı.")
        return True

    except Exception as e:
        print("Puma başlatma hatası:", e)
        return False


def ensure_puma():
    if is_puma_installed():
        print("Puma zaten kurulu.")
    else:
        success = install_puma()

        if not success:
            return False

    return start_puma()