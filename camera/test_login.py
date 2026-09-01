from appium import webdriver
from appium.options.android import UiAutomator2Options
import time

APPIUM_SERVER = "http://127.0.0.1:4723"

options = UiAutomator2Options()
options.platform_name = "Android"
options.automation_name = "UiAutomator2"
options.device_name = "emulator-5554"
options.udid = "emulator-5554"

options.app_package = "com.example.qr_app"
options.app_activity = "com.example.qr_app.MainActivity"

options.no_reset = True

driver = webdriver.Remote(
    APPIUM_SERVER,
    options=options
)

print("Appium bağlandı.")

time.sleep(3)

print("Ekrandaki elementler:")

elements = driver.find_elements("xpath", "//*")

for element in elements:
    try:
        print(
            "TEXT:", element.text,
            "| CLASS:", element.get_attribute("className"),
            "| RESOURCE:", element.get_attribute("resourceId"),
            "| CONTENT:", element.get_attribute("contentDescription")
        )
    except:
        pass

print("Test tamamlandı.")

while True:
    time.sleep(60)
    