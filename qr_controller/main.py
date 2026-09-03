import os
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

    # Telefonun çektiği gerçek görüntüyü kaydet.
    # QR'ın içeriğini burada okumuyoruz.
    with open(CURRENT_QR_IMAGE, "wb") as file:
        file.write(image_bytes)

    current_qr_mimetype = qr_image.mimetype

    if current_qr_mimetype == "application/octet-stream":
        current_qr_mimetype = "image/jpeg"

    if not current_qr_mimetype:
        current_qr_mimetype = "image/jpeg"
        
    print()
    print("================================")
    print("CONTROLLER QR GÖRÜNTÜSÜ ALDI")
    print("Boyut:", len(image_bytes), "bytes")
    print("Tip:", current_qr_mimetype)
    print("================================")

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

    try:
        driver = connect_to_puma()
    except Exception as e:
        print("Appium/Puma bağlantı hatası:", e)

        return jsonify(
            {
                "success": False,
                "message": "Appium/Puma bağlantısı kurulamadı"
            }
        ), 500

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
