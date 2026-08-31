from flask import Flask, request, jsonify
import threading
import subprocess
import os

app = Flask(__name__)

LAUNCHER = os.path.expanduser(
    "~/Downloads/camera/apk_launcher.py"
)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/install", methods=["POST"])
def install():
    data = request.get_json()

    apk_path = data.get("apkPath")

    if not apk_path:
        return jsonify({
            "success": False,
            "error": "APK yolu gönderilmedi."
        }), 400

    if not os.path.isfile(apk_path):
        return jsonify({
            "success": False,
            "error": "APK dosyası bulunamadı."
        }), 400

    try:
        subprocess.Popen([
            "python3",
            LAUNCHER,
            apk_path
        ])

        return jsonify({
            "success": True,
            "message": "APK launcher başlatıldı."
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5050
    )