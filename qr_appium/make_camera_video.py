import subprocess
import os

INPUT_IMAGE = "camera_test/camera_qr.jpg"
OUTPUT_VIDEO = "camera_test/qr_test.mp4"

DURATION_SECONDS = 120

def main():

    if not os.path.exists(INPUT_IMAGE):
        raise FileNotFoundError(
            f"{INPUT_IMAGE} bulunamadı. "
            f"Önce prepare_camera_qr.py çalıştır."
        )

    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", INPUT_IMAGE,
        "-t", str(DURATION_SECONDS),
        "-r", "15",
        "-vf", "scale=1080:2400,setsar=1",
        "-pix_fmt", "yuv420p",
        OUTPUT_VIDEO
    ]

    print("Video oluşturuluyor...")
    subprocess.run(cmd, check=True)

    print()
    print("✅ Kamera videosu hazır:")
    print(OUTPUT_VIDEO)
    print()


if __name__ == "__main__":
    main()

    