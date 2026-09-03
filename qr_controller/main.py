import os

import cv2
import numpy as np
from flask import Flask, request, jsonify, send_file

from puma_manager import ensure_puma
from emulator_manager import start_emulator, is_emulator_running
from appium_manager import connect_to_puma, login_to_puma, open_qr_scanner


app = Flask(__name__)

CURRENT_QR_IMAGE = os.path.join(
    os.path.dirname(__file__),
    "current_qr_image"
)

current_qr_mimetype = None


def order_points(points):
    """4 QR köşesini sol-üst, sağ-üst, sağ-alt, sol-alt sırasına koyar."""
    points = np.asarray(points, dtype=np.float32)

    ordered = np.zeros((4, 2), dtype=np.float32)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(-1)

    ordered[0] = points[np.argmin(sums)]
    ordered[2] = points[np.argmax(sums)]
    ordered[1] = points[np.argmin(diffs)]
    ordered[3] = points[np.argmax(diffs)]

    return ordered


def process_qr_image(image_bytes):
    """
    Telefondan gelen tam görüntüde QR'ı bulur.
    QR bulunursa sadece QR bölgesini perspektif olarak düzeltip
    kare biçiminde büyütür. QR içeriğini kullanmaz.
    """
    np_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    if image is None:
        return None

    detector = cv2.QRCodeDetector()
    points = None

    # Önce normal görüntüde dene. Bulamazsa gri ve büyütülmüş görüntüleri dene.
    candidates = [image]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    candidates.append(gray)

    # Küçük/uzak QR'larda tespiti kolaylaştırmak için görüntüyü 2 kat büyüt.
    enlarged = cv2.resize(
        image,
        None,
        fx=2.0,
        fy=2.0,
        interpolation=cv2.INTER_CUBIC
    )
    candidates.append(enlarged)

    for candidate in candidates:
        try:
            detected, detected_points = detector.detect(candidate)
            if detected and detected_points is not None:
                points = detected_points[0]
                # Eğer büyütülmüş görüntüde bulduysak koordinatları orijinale çevir.
                if candidate is enlarged:
                    points = points / 2.0
                break
        except cv2.error:
            continue

    # QR tespit edilemediyse mevcut görüntüyü olduğu gibi göster.
    if points is None:
        print("QR tespit edilemedi, orijinal görüntü kullanılacak.")
        return image_bytes

    points = order_points(points)

    # QR'ın kenarına biraz pay bırak.
    width = max(1.0, np.linalg.norm(points[1] - points[0]))
    height = max(1.0, np.linalg.norm(points[3] - points[0]))
    qr_size = int(max(width, height))

    # Çok küçük QR'ları da yeterli çözünürlüğe çıkar.
    qr_size = max(qr_size, 200)

    margin = max(20, int(qr_size * 0.10))
    output_size = 900

    src = np.array([
        points[0],
        points[1],
        points[2],
        points[3],
    ], dtype=np.float32)

    # QR'ı düz bir kareye dönüştür. Böylece telefon açılı tuttuysa bile
    # OBS'ye yamuk görüntü yerine düzgün bir kare gider.
    dst = np.array([
        [margin, margin],
        [output_size - margin, margin],
        [output_size - margin, output_size - margin],
        [margin, output_size - margin],
    ], dtype=np.float32)

    matrix = cv2.getPerspectiveTransform(src, dst)
    processed = cv2.warpPerspective(
        image,
        matrix,
        (output_size, output_size),
        borderValue=(255, 255, 255)
    )

    # Hafif keskinleştirme; bulanıklığı mucizevi şekilde düzeltmez ama
    # yeniden boyutlandırılmış QR'ın kenarlarını biraz daha belirgin yapar.
    blur = cv2.GaussianBlur(processed, (0, 0), 1.0)
    processed = cv2.addWeighted(processed, 1.25, blur, -0.25, 0)

    success, encoded = cv2.imencode(
        ".jpg",
        processed,
        [cv2.IMWRITE_JPEG_QUALITY, 95]
    )

    if not success:
        return image_bytes

    print(
        "QR tespit edildi → kırpıldı → kare yapıldı → "
        f"{output_size}x{output_size} olarak büyütüldü."
    )

    return encoded.tobytes()


@app.get("/health")
def health():
    return jsonify(
        {
            "success": True,
            "service": "qr_controller",
            "emulatorRunning": is_emulator_running(),
        }
    )


@app.post("/qr")
def receive_qr():
    global current_qr_mimetype

    qr_image = request.files.get("qrImage")

    if qr_image is None:
        return jsonify(
            {
                "success": False,
                "message": "QR görüntüsü gönderilmedi"
            }
        ), 400

    image_bytes = qr_image.read()

    if not image_bytes:
        return jsonify(
            {
                "success": False,
                "message": "QR görüntüsü boş"
            }
        ), 400

    print()
    print("================================")
    print("CONTROLLER QR GÖRÜNTÜSÜ ALDI")
    print("Boyut:", len(image_bytes), "bytes")
    print("Tip:", qr_image.mimetype or "image/jpeg")
    print("================================")

    # Telefonun çektiği görüntüde QR'ı tespit et; sadece QR bölgesini
    # kırpıp kare biçiminde büyüterek OBS'ye bunu ver.
    processed_image = process_qr_image(image_bytes)

    if processed_image is None:
        return jsonify(
            {
                "success": False,
                "message": "Telefon görüntüsü işlenemedi"
            }
        ), 400

    temp_image = CURRENT_QR_IMAGE + ".tmp"
    with open(temp_image, "wb") as file:
        file.write(processed_image)
    os.replace(temp_image, CURRENT_QR_IMAGE)

    current_qr_mimetype = "image/jpeg"

    emulator_ready = start_emulator()

    if not emulator_ready:
        return jsonify(
            {
                "success": False,
                "message": "Emülatör başlatılamadı"
            }
        ), 500

    puma_ready = ensure_puma()

    if not puma_ready:
        return jsonify(
            {
                "success": False,
                "message": "Puma başlatılamadı"
            }
        ), 500

    driver = connect_to_puma()

    login_success = login_to_puma(driver)

    if not login_success:
        return jsonify(
            {
                "success": False,
                "message": "Puma giriş yapılamadı"
            }
        ), 500

    qr_success = open_qr_scanner(driver)

    if not qr_success:
        return jsonify(
            {
                "success": False,
                "message": "QR Scanner açılamadı"
            }
        ), 500

    return jsonify(
        {
            "success": True,
            "message": "QR görüntüsü alındı, emülatör ve Puma QR Scanner hazır",
            "emulatorRunning": True,
            "pumaRunning": True,
            "qrScannerReady": True
        }
    )


@app.get("/qr-image")
def qr_image():
    if not os.path.exists(CURRENT_QR_IMAGE):
        return "", 204

    return send_file(
        CURRENT_QR_IMAGE,
        mimetype=current_qr_mimetype or "image/jpeg",
        max_age=0,
        etag=False,
        conditional=False,
    )


@app.get("/qr-display")
def qr_display():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">

        <style>
            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                background: white;
                overflow: hidden;
            }

            body {
                display: flex;
                align-items: center;
                justify-content: center;
            }

            #qr {
                width: 90vmin;
                height: 90vmin;
                object-fit: contain;
            }
        </style>
    </head>

    <body>
        <img id="qr" alt="QR">

        <script>
            async function updateQR() {
                const qr = document.getElementById("qr");
                qr.src = "/qr-image?t=" + Date.now();
            }

            updateQR();
            setInterval(updateQR, 300);
        </script>
    </body>
    </html>
    '''


if __name__ == "__main__":
    print("QR Controller başlatılıyor...")
    print("Controller: http://127.0.0.1:5050")

    app.run(
        host="127.0.0.1",
        port=5050
    )
