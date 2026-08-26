from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
import time

# ==========================================
# 1. ANDROID AYARLARI
# ==========================================

options = UiAutomator2Options()

options.platform_name = "Android"
options.device_name = "emulator-5554"
options.automation_name = "UiAutomator2"

options.app_package = "com.android.settings"
options.app_activity = ".Settings"


# ==========================================
# 2. APPIUM'A BAĞLAN
# ==========================================

driver = webdriver.Remote(
    "http://127.0.0.1:4723",
    options=options
)

print("Ayarlar açıldı!")

time.sleep(2)

# # Ekrandaki "Network & internet" yazısını bul
# element = driver.find_element(
#     AppiumBy.XPATH,
#     "//*[contains(@text, 'Notifications')]"
# )

# element.click()

# time.sleep(2)

# # 3. Yeni ekranda başka bir elementi bul
# second = driver.find_element(
#     AppiumBy.XPATH,
#     "//*[contains(@text, 'Bubbles')]"
# )

# # 4. Ona da tıkla
# second.click()
# time.sleep(2)


# third = driver.find_element(
#     AppiumBy.XPATH,
#     "//*[contains(@text, 'Allow apps to show bubbles')]"
# )
# print("Network & internet'e tıklandı!")
# third.click()

# time.sleep(3)

# driver.back()
# driver.back()

# driver.swipe(500, 1500, 500, 500, 800)

# time.sleep(2)


# ==========================================
# 3. AYARLARDA ARAMA EKRANINI AÇ
# ==========================================

search_button = driver.find_element(
    AppiumBy.XPATH,
    "//*[contains(@text, 'Search')]"
)

search_button.click()

print("Arama ekranı açıldı!")

time.sleep(2)


# ==========================================
# 4. ARAMA KUTUSUNU BUL
# ==========================================

search = driver.find_element(
    AppiumBy.XPATH,
    "//*[contains(@text, 'Search settings')]"
)

print("Arama kutusu bulundu!")


# ==========================================
# 5. ARAMA KUTUSUNA TIKLA
# ==========================================

search.click()

time.sleep(2)

print("Arama kutusuna tıklandı!")

print(
    "Klavye açık mı?:",
    driver.is_keyboard_shown()
)


# ==========================================
# 6. ARAMA YAP
# ==========================================

search.send_keys("Notifications")

time.sleep(3)

print("Wi-Fi yazıldı!")


# ==========================================
# 7. EKRAN GÖRÜNTÜSÜ
# ==========================================

driver.save_screenshot("search_result.png")

time.sleep(2)


# ==========================================
# 8. APPIUM'U KAPAT
# ==========================================

driver.quit()

print("Appium session kapatıldı!")