from flask import Flask, request, jsonify

from puma_manager import ensure_puma
from emulator_manager import start_emulator, is_emulator_running
from appium_manager import connect_to_puma, login_to_puma, open_qr_scanner


app = Flask(__name__)


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
    data = request.get_json(silent=True) or {}

    qr_data = data.get("qrData")

    if not qr_data:
        return jsonify(
            {
                "success": False,
                "message": "QR verisi gönderilmedi"
            }
        ), 400

    print()
    print("================================")
    print("CONTROLLER QR ALDI")
    print("QR:", qr_data)
    print("================================")

    # 1. Emülatörü başlat
    emulator_ready = start_emulator()

    if not emulator_ready:
        return jsonify(
            {
                "success": False,
                "message": "Emülatör başlatılamadı"
            }
        ), 500

    # 2. Puma'yı kontrol et / kur / aç
    puma_ready = ensure_puma()

    if not puma_ready:
        return jsonify(
            {
                "success": False,
                "message": "Puma başlatılamadı"
            }
        ), 500

    # 3. Appium ile Puma'ya bağlan
    driver = connect_to_puma()

    # 4. Login yap
    login_success = login_to_puma(driver)

    if not login_success:
        return jsonify(
            {
                "success": False,
                "message": "Puma giriş yapılamadı"
            }
        ), 500

    # 5. QR Scanner ekranını aç
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
            "message": "Emülatör, Puma, login ve QR Scanner hazır",
            "emulatorRunning": True,
            "pumaRunning": True,
            "qrScannerReady": True
        }
    )


if __name__ == "__main__":
    print("QR Controller başlatılıyor...")
    print("Controller: http://127.0.0.1:5050")

    app.run(
        host="127.0.0.1",
        port=5050
    )