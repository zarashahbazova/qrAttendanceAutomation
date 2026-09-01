from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

LAUNCHER = os.path.expanduser("~/Downloads/qrProjesi/camera/apk_launcher.py")


# Agent bağlantısını kontrol et
@app.route("/health", methods=["GET"])
def health():

    return jsonify({"status": "ok"})


# APK kurulumunu başlat
@app.route("/install", methods=["POST"])
def install():

    data = request.get_json()

    apk_path = data.get("apkPath")

    camera = data.get("camera", "webcam0")

    if not apk_path:

        return jsonify({"success": False, "error": "APK yolu gönderilmedi."}), 400

    if not os.path.isfile(apk_path):

        return jsonify({"success": False, "error": "APK dosyası bulunamadı."}), 400

    try:

        subprocess.Popen(["python3", LAUNCHER, apk_path, camera])

        return jsonify(
            {"success": True, "message": "APK launcher başlatıldı.", "camera": camera}
        )

    except Exception as error:

        return jsonify({"success": False, "error": str(error)}), 500


if __name__ == "__main__":

    app.run(host="127.0.0.1", port=5050)
