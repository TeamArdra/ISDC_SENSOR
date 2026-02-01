#!/usr/bin/env python3

import cv2
import numpy as np
import time
import datetime
import os
from picamera2 import Picamera2

# ================= CONFIG =================

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

MIN_RADIUS = 40
MAX_RADIUS = 350

CAPTURE_COOLDOWN = 2.0  # seconds
SAVE_DIR = "/home/pi/circle_snapshots"

# =========================================


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)

    picam2 = Picamera2()
    picam2.configure(
        picam2.create_video_configuration(
            main={"size": (FRAME_WIDTH, FRAME_HEIGHT), "format": "RGB888"}
        )
    )
    picam2.start()

    print("[INFO] Pi Camera Module 3 started")
    print("[INFO] Waiting for circle detection...")

    last_capture = 0

    while True:
        frame = picam2.capture_array()

        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (9, 9), 1.5)

        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=100,
            param1=100,
            param2=30,
            minRadius=MIN_RADIUS,
            maxRadius=MAX_RADIUS
        )

        if circles is not None:
            now = time.time()
            if now - last_capture > CAPTURE_COOLDOWN:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filepath = os.path.join(SAVE_DIR, f"circle_{timestamp}.jpg")

                # Convert RGB → BGR for OpenCV save
                cv2.imwrite(filepath, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

                last_capture = now
                print(f"[SAVED] {filepath}")

        time.sleep(0.01)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Script stopped")
