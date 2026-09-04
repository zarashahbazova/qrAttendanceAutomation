import os
import signal
import subprocess
import threading
import time
import urllib.request
import tkinter as tk
from tkinter import messagebox

# ---------------------------------------------------------
# PROJE YOLLARI
# ---------------------------------------------------------

MAC_APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(MAC_APP_DIR)

BACKEND_DIR = os.path.join(PROJECT_DIR, "qr_backend")
CONTROLLER_DIR = os.path.join(PROJECT_DIR, "qr_controller")

# GUI'nin çalıştıracağı gerçek terminal komutları
BACKEND_COMMAND = ["npm", "run", "dev"]
CONTROLLER_COMMAND = ["python3", "main.py"]
APPIUM_COMMAND = ["appium"]

# ---------------------------------------------------------
# PROCESSLER
# ---------------------------------------------------------

backend_process = None
controller_process = None
appium_process = None

system_running = False
starting = False


# ---------------------------------------------------------
# PROCESS BAŞLATMA
# ---------------------------------------------------------


def run_terminal_command(command, cwd):
    # Finder'dan açılan GUI'nin de terminaldeki komutları bulabilmesi için
    # login shell kullanıyoruz.
    command_text = " ".join("'" + arg.replace("'", "'\\''") + "'" for arg in command)

    return subprocess.Popen(
        ["/bin/zsh", "-lc", command_text],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid,
    )


def read_process_output(process, name):
    if process.stdout is None:
        return

    try:
        for line in process.stdout:
            print(f"[{name}] {line.rstrip()}")
    except Exception as e:
        print(f"{name} çıktı okuma hatası:", e)


def wait_for_url(url, timeout=20):
    end_time = time.time() + timeout

    while time.time() < end_time:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.5)

    return False


def start_backend():
    global backend_process

    if backend_process is not None and backend_process.poll() is None:
        return True

    try:
        backend_process = run_terminal_command(BACKEND_COMMAND, BACKEND_DIR)

        return wait_for_url("http://127.0.0.1:5001/", timeout=15)

    except Exception as e:
        print("Backend başlatma hatası:", e)
        return False


def start_controller():
    global controller_process

    if controller_process is not None and controller_process.poll() is None:
        return True

    try:
        controller_process = run_terminal_command(CONTROLLER_COMMAND, CONTROLLER_DIR)

        threading.Thread(
            target=read_process_output,
            args=(controller_process, "CONTROLLER"),
            daemon=True,
        ).start()

        return wait_for_url("http://127.0.0.1:5050/health", timeout=15)

    except Exception as e:
        print("Controller başlatma hatası:", e)
        return False


def start_appium():
    global appium_process

    if is_appium_running():
        return True

    try:
        appium_process = run_terminal_command(APPIUM_COMMAND, CONTROLLER_DIR)

        return wait_for_url("http://127.0.0.1:4723/status", timeout=20)

    except Exception as e:
        print("Appium başlatma hatası:", e)
        return False


# ---------------------------------------------------------
# PROCESS DURDURMA
# ---------------------------------------------------------


def stop_process(process):
    if process is None:
        return

    if process.poll() is not None:
        return

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except Exception:
        pass


def stop_backend():
    global backend_process

    stop_process(backend_process)
    backend_process = None


def stop_controller():
    global controller_process

    stop_process(controller_process)
    controller_process = None


def stop_appium():
    global appium_process

    stop_process(appium_process)
    appium_process = None


# ---------------------------------------------------------
# OBS
# ---------------------------------------------------------

OBS_EXECUTABLE = "/Applications/OBS.app/Contents/MacOS/OBS"


def is_obs_running():
    result = subprocess.run(
        ["pgrep", "-f", OBS_EXECUTABLE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return result.returncode == 0


def start_virtual_camera_button():
    script = r"""
tell application "System Events"
    tell process "OBS"
        set frontmost to true

        try
            click button "Sanal Kamerayı Durdur" of window 1
            return "already"
        on error
        end try

        try
            click button "Sanal Kamerayı Başlat" of window 1
            return "success"
        on error
            return "not_found"
        end try
    end tell
end tell
"""

    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=10
        )

        output = result.stdout.strip()
        print("OBS Virtual Camera:", output)

        return output in ("success", "already")

    except Exception as e:
        print("Virtual Camera hatası:", e)
        return False


def start_obs():
    try:
        # OBS açık değilse normal şekilde aç
        if not is_obs_running():
            print("OBS başlatılıyor...")

            subprocess.Popen(
                [OBS_EXECUTABLE], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # OBS'nin tamamen açılmasını bekle
            for _ in range(20):
                if is_obs_running():
                    break
                time.sleep(1)

        if not is_obs_running():
            print("OBS açılamadı.")
            return False

        print("OBS açıldı.")

        # OBS açıldıktan sonra biraz bekle
        time.sleep(3)

        # Virtual Camera butonuna bas
        for attempt in range(5):
            print(f"Virtual Camera başlatılıyor... " f"deneme {attempt + 1}/5")

            result = start_virtual_camera_button()

            if result:
                print("OBS Virtual Camera hazır.")
                return True

            time.sleep(2)

        print("OBS Virtual Camera başlatılamadı.")
        return False

    except Exception as e:
        print("OBS hatası:", e)
        return False


# ---------------------------------------------------------
# EMULATOR
# ---------------------------------------------------------
# Emulator GUI tarafından BAŞLATILMAZ.
# qr_controller/main.py /qr isteği geldiğinde start_emulator() çağırır.


def is_emulator_running():
    try:
        result = subprocess.run(
            ["/bin/zsh", "-lc", "adb -s emulator-5554 get-state 2>/dev/null"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() == "device"
    except Exception:
        return False


# ---------------------------------------------------------
# PUMA
# ---------------------------------------------------------
# Puma da GUI tarafından BAŞLATILMAZ.
# QR geldiğinde controller ensure_puma() çağırır.


def is_puma_running():
    try:
        result = subprocess.run(
            [
                "/bin/zsh",
                "-lc",
                "adb -s emulator-5554 shell pidof com.nes.puma 2>/dev/null",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception:
        return False


# ---------------------------------------------------------
# APPIUM
# ---------------------------------------------------------


def is_appium_running():
    try:
        urllib.request.urlopen("http://127.0.0.1:4723/status", timeout=2)
        return True
    except Exception:
        return False


# ---------------------------------------------------------
# SİSTEM BAŞLAT
# ---------------------------------------------------------


def start_system():
    global system_running
    global starting

    if starting or system_running:
        return

    starting = True

    start_button.config(state="disabled", text="Başlatılıyor...")

    stop_button.config(state="disabled")

    def worker():
        global system_running
        global starting

        try:
            # 1. qr_backend -> npm run dev
            set_status("Backend", "Başlatılıyor...", "yellow")

            if not start_backend():
                set_status("Backend", "Hata", "red")
                raise Exception("Backend başlatılamadı.")
            set_status("Backend", "Çalışıyor", "green")

            # 2. qr_controller -> python3 main.py
            # Mevcut controller dosyası main.py'dir.
            set_status("Controller", "Başlatılıyor...", "yellow")

            if not start_controller():
                set_status("Controller", "Hata", "red")
                raise Exception("Controller başlatılamadı.")
            set_status("Controller", "Çalışıyor", "green")

            # 3. Appium -> appium
            set_status("Appium", "Başlatılıyor...", "yellow")

            if not start_appium():
                set_status("Appium", "Hata", "red")
                raise Exception("Appium başlatılamadı.")
            set_status("Appium", "Çalışıyor", "green")

            # 4. OBS'yi aç + Start Virtual Camera'a bas
            set_status("OBS", "Başlatılıyor...", "yellow")

            if not start_obs():
                set_status("OBS", "Hata", "red")
                raise Exception("OBS / Virtual Camera başlatılamadı.")
            set_status("OBS", "Çalışıyor", "green")

            # 5-6. Emulator + Puma BURADA BAŞLATILMAZ.
            # Controller /qr geldiğinde bunları açar.
            set_status("Emulator", "QR ile açılacak", "yellow")
            set_status("Puma", "QR ile açılacak", "yellow")

            system_running = True

            root.after(
                0,
                lambda: start_button.config(state="disabled", text="Sistem Çalışıyor"),
            )

            root.after(0, lambda: stop_button.config(state="normal"))

        except Exception as e:
            print("Sistem başlatma hatası:", e)

            system_running = False

            root.after(0, lambda: messagebox.showerror("Sistem Hatası", str(e)))

            root.after(
                0, lambda: start_button.config(state="normal", text="Sistemi Başlat")
            )

        finally:
            starting = False

    threading.Thread(target=worker, daemon=True).start()


# ---------------------------------------------------------
# SİSTEM DURDUR
# ---------------------------------------------------------


def stop_system():

    global system_running

    if not system_running:
        return

    stop_button.config(state="disabled", text="Durduruluyor...")

    def worker():
        global system_running

        stop_controller()
        set_status("Controller", "Kapalı", "red")

        stop_backend()
        set_status("Backend", "Kapalı", "red")

        stop_appium()

        try:
            subprocess.run(
                ["pkill", "-f", "appium"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

        set_status("Appium", "Kapalı", "red")

        try:
            subprocess.run(
                [
                    "/bin/zsh",
                    "-lc",
                    "adb -s emulator-5554 shell am force-stop com.nes.puma 2>/dev/null",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

        set_status("Puma", "Kapalı", "red")

        try:
            subprocess.run(
                ["/bin/zsh", "-lc", "adb -s emulator-5554 emu kill 2>/dev/null"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass

        set_status("Emulator", "Kapalı", "red")

        # OBS açık bırakılıyor.
        if is_obs_running():
            set_status("OBS", "Açık", "green")
        else:
            set_status("OBS", "Kapalı", "red")

        system_running = False

        root.after(
            0, lambda: start_button.config(state="normal", text="Sistemi Başlat")
        )

        root.after(
            0, lambda: stop_button.config(state="disabled", text="Sistemi Durdur")
        )

    threading.Thread(target=worker, daemon=True).start()


# ---------------------------------------------------------
# DURUM GÜNCELLEME
# ---------------------------------------------------------

status_labels = {}


def set_status(name, text, color):
    def update():
        status_labels[name].config(text=text)

        if color == "green":
            status_labels[name].config(fg="#1a9c45")
        elif color == "red":
            status_labels[name].config(fg="#d93025")
        elif color == "yellow":
            status_labels[name].config(fg="#c58a00")

    root.after(0, update)


def update_statuses():

    backend_ok = backend_process is not None and backend_process.poll() is None

    set_status(
        "Backend",
        "Çalışıyor" if backend_ok else "Kapalı",
        "green" if backend_ok else "red",
    )

    controller_ok = controller_process is not None and controller_process.poll() is None

    set_status(
        "Controller",
        "Çalışıyor" if controller_ok else "Kapalı",
        "green" if controller_ok else "red",
    )

    obs_ok = is_obs_running()

    set_status("OBS", "Çalışıyor" if obs_ok else "Kapalı", "green" if obs_ok else "red")

    emulator_ok = is_emulator_running()

    set_status(
        "Emulator",
        "Çalışıyor" if emulator_ok else "QR ile açılacak",
        "green" if emulator_ok else "yellow",
    )

    puma_ok = is_puma_running()

    set_status(
        "Puma",
        "Çalışıyor" if puma_ok else "QR ile açılacak",
        "green" if puma_ok else "yellow",
    )

    appium_ok = is_appium_running()

    set_status(
        "Appium",
        "Çalışıyor" if appium_ok else "Kapalı",
        "green" if appium_ok else "red",
    )

    root.after(2000, update_statuses)


# ---------------------------------------------------------
# ARAYÜZ
# ---------------------------------------------------------

root = tk.Tk()

root.title("QR Automation")
root.geometry("520x600")
root.resizable(False, False)

title = tk.Label(root, text="QR Automation", font=("Arial", 26, "bold"))

title.pack(pady=(30, 5))

subtitle = tk.Label(
    root, text="QR otomasyon sistemi kontrol paneli", font=("Arial", 12)
)

subtitle.pack(pady=(0, 30))


# ---------------------------------------------------------
# DURUMLAR
# ---------------------------------------------------------

status_frame = tk.Frame(root)

status_frame.pack(padx=50, fill="x")

components = ["Backend", "Controller", "OBS", "Emulator", "Puma", "Appium"]

for component in components:

    row = tk.Frame(status_frame)

    row.pack(fill="x", pady=7)

    name_label = tk.Label(row, text=component, font=("Arial", 14), anchor="w", width=15)

    name_label.pack(side="left")

    status_label = tk.Label(
        row, text="Kapalı", font=("Arial", 14, "bold"), fg="#d93025", anchor="e"
    )

    status_label.pack(side="right")

    status_labels[component] = status_label


# ---------------------------------------------------------
# BUTONLAR
# ---------------------------------------------------------

button_frame = tk.Frame(root)

button_frame.pack(pady=45)

start_button = tk.Button(
    button_frame,
    text="Sistemi Başlat",
    font=("Arial", 14, "bold"),
    width=18,
    height=2,
    command=start_system,
)

start_button.pack(pady=8)

stop_button = tk.Button(
    button_frame,
    text="Sistemi Durdur",
    font=("Arial", 14, "bold"),
    width=18,
    height=2,
    command=stop_system,
    state="disabled",
)

stop_button.pack(pady=8)


# ---------------------------------------------------------
# PROGRAM BAŞLANGICI
# ---------------------------------------------------------

update_statuses()

root.mainloop()
