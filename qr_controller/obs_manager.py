import subprocess
import time


OBS_EXECUTABLE = "/Applications/OBS.app/Contents/MacOS/OBS"


def is_obs_running():
    result = subprocess.run(
        ["pgrep", "-f", OBS_EXECUTABLE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return result.returncode == 0


def start_obs():
    """
    OBS kapalıysa açar.
    Zaten açıksa tekrar açmaz.
    """

    if is_obs_running():
        print("OBS zaten çalışıyor.")
        return True

    print("OBS başlatılıyor...")

    try:
        subprocess.Popen(
            [OBS_EXECUTABLE],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # OBS'nin tamamen açılmasını bekle
        for _ in range(15):
            time.sleep(1)

            if is_obs_running():
                print("OBS açıldı.")
                return True

        print("OBS başlatılamadı.")
        return False

    except Exception as e:
        print("OBS başlatma hatası:", e)
        return False


def start_virtual_camera():
    """
    OBS açıksa macOS Accessibility üzerinden
    'Start Virtual Camera' butonuna basar.
    """

    if not is_obs_running():
        print("OBS çalışmıyor.")
        return False

    print("OBS Virtual Camera başlatılıyor...")

    # OBS'nin kamera eklentisinin tamamen yüklenmesi için bekle
    time.sleep(5)

    applescript = r'''
tell application "System Events"
    tell process "OBS"
        set frontmost to true

        try
            click button "Start Virtual Camera" of window 1
            return "success"
        on error
            try
                click button "Sanal Kamerayı Başlat" of window 1
                return "success"
            on error
                return "not_found"
            end try
        end try
    end tell
end tell
'''

    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True
        )

        output = result.stdout.strip()

        if output == "success":
            print("OBS Virtual Camera başlatıldı.")
            return True

        print("OBS Virtual Camera butonu bulunamadı.")
        print(result.stderr.strip())

        return False

    except Exception as e:
        print("Virtual Camera başlatma hatası:", e)
        return False


def ensure_virtual_camera():
    """
    OBS'nin açık olduğundan ve Virtual Camera'nın başlatıldığından emin olur.
    """

    print("OBS Virtual Camera kontrol ediliyor...")

    # 1. OBS kapalıysa aç
    if not is_obs_running():
        if not start_obs():
            return False

    # 2. OBS zaten açıksa tekrar açma.
    #    Her iki durumda da Virtual Camera'yı başlatmayı dene.
    return start_virtual_camera()