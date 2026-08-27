import cv2
import numpy as np
import os

INPUT = "received_qr/qr.jpg"
OUTPUT = "camera_test/camera_qr.jpg"

# Android Emulator'ün sanal kamerası (videofile:) telefon ekran oranını değil,
# 4:3 standart YATAY kamera çözünürlüğünü bekliyor. 1280x960 (landscape),
# senin daha önce emulator'de başarıyla gösterdiğin qr_camera.mp4 ile birebir
# aynı oran/yön -- dikey (960x1280) verince kayma/kırpma oluyordu.
WIDTH = 1280
HEIGHT = 960

os.makedirs("camera_test", exist_ok=True)

image = cv2.imread(INPUT)

if image is None:
    raise Exception(f"QR görüntüsü bulunamadı: {INPUT}")

detector = cv2.QRCodeDetector()

# QR'ın konumunu bul
data, points, _ = detector.detectAndDecode(image)

if points is None:
    raise Exception("QR'ın konumu bulunamadı!")

points = points[0].astype(int)

# QR'ın çevresindeki bounding box
x, y, w, h = cv2.boundingRect(points)

print("QR bulundu:")
print("x:", x)
print("y:", y)
print("width:", w)
print("height:", h)

# Biraz güvenlik payı bırak
padding = int(max(w, h) * 0.15)

x1 = max(0, x - padding)
y1 = max(0, y - padding)
x2 = min(image.shape[1], x + w + padding)
y2 = min(image.shape[0], y + h + padding)

qr = image[y1:y2, x1:x2]

if qr.size == 0:
    raise Exception("QR crop edilemedi!")

# Kare canvas oluştur
size = max(qr.shape[0], qr.shape[1])

canvas = np.ones(
    (size, size, 3),
    dtype=np.uint8
) * 255

# QR görüntüsünü karenin ortasına yerleştir
offset_x = (size - qr.shape[1]) // 2
offset_y = (size - qr.shape[0]) // 2

canvas[
    offset_y:offset_y + qr.shape[0],
    offset_x:offset_x + qr.shape[1]
] = qr

# QR'ı kamera görüntüsünde makul boyuta getir (dikey sınır olan 960'ın ~%65'i)
qr_size = 300

canvas = cv2.resize(
    canvas,
    (qr_size, qr_size),
    interpolation=cv2.INTER_CUBIC
)

# 1080x2400 beyaz kamera görüntüsü
camera_image = np.ones(
    (HEIGHT, WIDTH, 3),
    dtype=np.uint8
) * 255

# Tam ortaya yerleştir
start_x = (WIDTH - qr_size) // 2
start_y = (HEIGHT - qr_size) // 2

camera_image[
    start_y:start_y + qr_size,
    start_x:start_x + qr_size
] = canvas

cv2.imwrite(OUTPUT, camera_image)

print()
print("✅ Kamera görüntüsü hazır!")
print("Kaydedildi:", OUTPUT)
print(f"Boyut: {WIDTH}x{HEIGHT}")
print("QR merkeze yerleştirildi.")