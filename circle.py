#!/usr/bin/env python3

import cv2
import numpy as np
import time
import datetime
import csv
from pymavlink import mavutil
from sense_hat import SenseHat

# ===================== CONFIG =====================

# Camera
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
CENTER_TOL = 40
MIN_RADIUS = 40
MAX_RADIUS = 350

# Telemetry
SEND_INTERVAL = 0.5  # seconds
MAVLINK_PORT = "/dev/ttyAMA0"
MAVLINK_BAUD = 57600

# Sense HAT logging
SENSOR_INTERVAL = 10  # seconds (logging rate)
SEA_LEVEL_PRESSURE = 1013.25
CSV_FILE = "/home/Ardra/sensor_data.csv"

# =================================================


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


def init_csv():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Date",
            "Temperature (°C)",
            "Humidity (%)",
            "Pressure (hPa)",
            "Altitude (m)",
            "Accelerometer",
            "Gyroscope",
            "Magnetometer"
        ])
    print("[INFO] CSV file initialized")


def main():
    # ---------- MAVLink ----------
    master = connect_mavlink()

    # ---------- Camera ----------
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("[ERROR] Camera not detected")
        return

    print("[INFO] Camera started")

    # ---------- Sense HAT ----------
    sense = SenseHat()
    sense.clear()

    init_csv()

    last_telem_send = 0
    last_sensor_log = 0

    print("[INFO] Continuous sensor logging ENABLED")
    print("[INFO] Vision + telemetry running")

    while True:
        # ================= CAMERA + TELEMETRY =================
        ret, frame = cap.read()
        if ret:
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

            now = time.time()
            if now - last_telem_send > SEND_INTERVAL:
                send_status(master, status)
                last_telem_send = now

        # ================= CONTINUOUS SENSE HAT LOGGING =================
        now = time.time()
        if now - last_sensor_log > SENSOR_INTERVAL:
            last_sensor_log = now

            date = str(datetime.datetime.now())
            temperature = sense.get_temperature()
            humidity = sense.get_humidity()
            pressure = sense.get_pressure()
            altitude = 44330 * (1 - (pressure / SEA_LEVEL_PRESSURE) ** 0.1903)

            accelerometer = sense.get_accelerometer_raw()
            gyroscope = sense.get_gyroscope_raw()
            magnetometer = sense.get_compass()

            data = [
                date,
                round(temperature, 2),
                round(humidity, 2),
                round(pressure, 2),
                round(altitude, 2),
                str(accelerometer),
                str(gyroscope),
                round(magnetometer, 2)
            ]

            with open(CSV_FILE, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(data)

            print("[SENSOR LOGGED]", data)

        time.sleep(0.01)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] Script terminated by user")
