import subprocess
import time

from config import ADB, EMULATOR, AVD_NAME, DEVICE_ID


def get_connected_devices():
    try:
        result = subprocess.run(
            [ADB, "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )

        devices = []

        for line in result.stdout.splitlines():
            line = line.strip()

            if not line or line.startswith("List of devices"):
                continue

            parts = line.split()

            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])

        return devices

    except Exception as e:
        print("ADB kontrol hatası:", e)
        return []


def is_emulator_running():
    devices = get_connected_devices()

    return DEVICE_ID in devices


def start_emulator():
    if is_emulator_running():
        print("qr1 emülatörü zaten çalışıyor.")
        return True

    print("qr1 emülatörü başlatılıyor...")

    try:
        command = [
            EMULATOR,
            "-avd",
            AVD_NAME,
            "-camera-back",
            "webcam1"
        ]

        print("Emülatör komutu:", " ".join(command))

        subprocess.Popen(
            command,
            stdout=None,
            stderr=None
        )

        return wait_for_emulator()

    except Exception as e:
        print("Emülatör başlatma hatası:", e)
        return False
    
def wait_for_emulator(timeout=120):
    print("Emülatörün açılması bekleniyor...")

    start_time = time.time()

    while time.time() - start_time < timeout:

        if is_emulator_running():

            try:
                result = subprocess.run(
                    [
                        ADB,
                        "-s",
                        DEVICE_ID,
                        "shell",
                        "getprop",
                        "sys.boot_completed"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.stdout.strip() == "1":
                    print("Emülatör tamamen açıldı.")
                    return True

            except Exception:
                pass

        time.sleep(2)

    print("Emülatör zamanında açılmadı.")
    return False