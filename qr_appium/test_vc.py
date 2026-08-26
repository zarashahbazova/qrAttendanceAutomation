import time
import numpy as np
import pyvirtualcam


WIDTH = 640
HEIGHT = 480
FPS = 30


with pyvirtualcam.Camera(
    width=WIDTH,
    height=HEIGHT,
    fps=FPS
) as cam:

    print("======================================")
    print("🎥 Virtual Camera bağlandı")
    print("Camera:", cam.device)
    print("Backend:", cam.backend)
    print("======================================")

    while True:

        frame = np.zeros(
            (HEIGHT, WIDTH, 3),
            dtype=np.uint8
        )

        # KIRMIZI EKRAN
        frame[:, :] = (255, 0, 0)

        cam.send(frame)

        cam.sleep_until_next_frame()