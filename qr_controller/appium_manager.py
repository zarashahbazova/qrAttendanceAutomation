import time

from appium import webdriver
from appium.options.android import UiAutomator2Options

from config import DEVICE_ID, PUMA_PACKAGE, PUMA_ACTIVITY


def connect_to_puma():
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