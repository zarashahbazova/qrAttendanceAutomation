import time
import os
import obsws_python as obs


HOST = "127.0.0.1"
PORT = 4455

SCENE_ITEM_NAME = "Resim"

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

TEST1 = os.path.join(
    BASE_DIR,
    "test1.png"
)

TEST2 = os.path.join(
    BASE_DIR,
    "test2.png"
)


password = input("OBS WebSocket şifresi: ")

client = obs.ReqClient(
    host=HOST,
    port=PORT,
    password=password
)


print("✅ OBS'ye bağlandı.")


# TEST 1
print("🔴 TEST 1 gönderiliyor...")

client.set_input_settings(
    SCENE_ITEM_NAME,
    {
        "file": TEST1
    },
    True
)

time.sleep(3)


# TEST 2
print("🔵 TEST 2 gönderiliyor...")

client.set_input_settings(
    SCENE_ITEM_NAME,
    {
        "file": TEST2
    },
    True
)

time.sleep(3)


print("✅ Test tamamlandı.")