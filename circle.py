#!/usr/bin/env python3

import cv2
import numpy as np
import time
from pymavlink import mavutil

# ===================== USER-CONFIGURABLE =====================

# Camera resolution (safe for Pi 5)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Center tolerance (pixels)
CENTER_TOL = 40

# Circle size limits (pixels)
MIN_RADIUS = 40
MAX_RADIUS = 350

# Telemetry update rate (seconds)
SEND_INTERVAL = 0.5   # 2 Hz

# MAVLink serial port (MOST COMMON for Pi)
MAVLINK_PORT = "/dev/ttyAMA0"
MAVLINK_BAUD = 57600

# ============================================================


def connect_mavlink():
    print("[INFO] Connecting to MAVLink...")
    master = mavutil.mavlink_connection(MAVLINK_PORT, baud=MAVLINK_BAUD)
    master.wait_heartbeat()
    print("[INFO] MAVLink heartbeat received")
    return master


def send_status(master, text):
    master.mav.statustext_send(
        mavutil.mavlink.MAV_SEVERITY_INFO,
        text.encode("utf-8")
    )


def main():
    # Connect telemetry
    master = connect_mavlink()

    # Open camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("[ERROR] Camera not detected")
        return

    print("[INFO] Camera started")

    last_send = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # ---- Image processing ----
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
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

        status = "TARGET NOT FOUND"

        if circles is not None:
            circles = np.uint16(np.around(circles))
            # Pick largest circle (closest / most dominant)
            circles = sorted(circles[0], key=lambda c: c[2], reverse=True)
            x, y, r = circles[0]

            dx = x - FRAME_WIDTH // 2
            dy = y - FRAME_HEIGHT // 2

            if abs(dx) < CENTER_TOL and abs(dy) < CENTER_TOL:
                status = "INSIDE TARGET CIRCLE - HOLD"
            elif abs(dx) > abs(dy):
                status = "MOVE RIGHT" if dx > 0 else "MOVE LEFT"
            else:
                status = "MOVE BACK" if dy > 0 else "MOVE FORWARD"

        # ---- Send telemetry (rate limited) ----
        now = time.time()
        if now - last_send > SEND_INTERVAL:
            send_status(master, status)
            last_send = now

        time.sleep(0.01)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user")
