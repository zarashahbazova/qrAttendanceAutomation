import os

ANDROID_SDK = os.environ.get(
    "ANDROID_SDK_ROOT",
    os.path.expanduser("~/Library/Android/sdk")
)

ADB = os.path.join(
    ANDROID_SDK,
    "platform-tools",
    "adb"
)

EMULATOR = os.path.join(
    ANDROID_SDK,
    "emulator",
    "emulator"
)

AVD_NAME = "qr1"

DEVICE_ID = "emulator-5554"

CONTROLLER_HOST = "127.0.0.1"
CONTROLLER_PORT = 5050

PUMA_PACKAGE = "com.nes.puma"
PUMA_ACTIVITY = "com.nes.puma.MainActivity"

PUMA_APK_DIR = os.path.join(
    os.path.dirname(__file__),
    "PumaAPK"
)