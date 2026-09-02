from flask import Flask, request, jsonify
from puma_manager import ensure_puma
from emulator_manager import start_emulator, is_emulator_running

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({
        "success": True,
        "service": "qr_controller",
        "emulatorRunning": is_emulator_running()
    })


@app.post("/qr")
def receive_qr():
    data = request.get_json(silent=True) or {}

    qr_data = data.get("qrData")

    if not qr_data:
        return jsonify({
            "success": False,
            "message": "QR verisi gönderilmedi"
        }), 400

    print()
    print("================================")
    print("CONTROLLER QR ALDI")
    print("QR:", qr_data)
    print("================================")

    emulator_ready = start_emulator()

    if not emulator_ready:
        return jsonify({
            "success": False,
            "message": "Emülatör başlatılamadı"
        }), 500


    puma_ready = ensure_puma()

    if not puma_ready:
        return jsonify({
            "success": False,
            "message": "Puma başlatılamadı"
        }), 500


    return jsonify({
        "success": True,
        "message": "Emülatör ve Puma hazır",
        "emulatorRunning": True,
        "pumaRunning": True
    })



if __name__ == "__main__":
    print("QR Controller başlatılıyor...")
    print("Controller: http://127.0.0.1:5050")

    app.run(
        host="127.0.0.1",
        port=5050
    )