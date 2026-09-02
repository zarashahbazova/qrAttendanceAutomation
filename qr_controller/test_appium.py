from appium_manager import connect_to_puma


driver = connect_to_puma()

print()
print("PUMA BAĞLANTISI BAŞARILI")
print("Aktif uygulama:", driver.current_package)
print("Aktif activity:", driver.current_activity)
print()

print("PUMA EKRANINDAKİ ÖĞELER:")
print("--------------------------------")

elements = driver.find_elements(
    "xpath",
    "//*"
)

for element in elements:
    try:
        text = element.get_attribute("text")
        resource_id = element.get_attribute("resourceId")
        content_desc = element.get_attribute("contentDescription")
        class_name = element.get_attribute("className")

        if text or resource_id or content_desc:
            print(
                f"text={text!r} | "
                f"id={resource_id!r} | "
                f"desc={content_desc!r} | "
                f"class={class_name!r}"
            )

    except Exception:
        pass

driver.quit()