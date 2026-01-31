from sense_hat import SenseHat
from time import time
import datetime
import csv
import os

sense = SenseHat()
sense.clear()

send = True
interval = 10
prevSec = 0

# Sea-level pressure for altitude calculation (hPa)
SEA_LEVEL_PRESSURE = 1013.25

# Path to save the CSV file
csv_file = "/home/Ardra/sensor_data.csv"

# Create a new CSV file each time the script is run
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Date", "Temperature (°C)", "Humidity (%)", "Pressure (hPa)",
                     "Altitude (m)", "Accelerometer", "Gyroscope", "Magnetometer"])

print("Sensor data from Sense HAT is being written to a new CSV file on Raspberry Pi")
print()

try:
    while True:
        for event in sense.stick.get_events():
            if event.direction == "left":
                send = False
                sense.show_letter("0", text_colour=(100, 0, 0))
                print("Stop!")
                print()

            if event.direction == "right":
                send = True
                sense.show_letter("1", text_colour=(0, 100, 0))
                print("Sending data...")
                print()

        if send:
            if time() - prevSec > interval:
                prevSec = time()

                # Collect data
                date = str(datetime.datetime.now())
                temperature = sense.get_temperature()
                humidity = sense.get_humidity()
                pressure = sense.get_pressure()

                # Calculate altitude from pressure
                altitude = 44330 * (1 - (pressure / SEA_LEVEL_PRESSURE) ** 0.1903)

                accelerometer = sense.get_accelerometer_raw()
                gyroscope = sense.get_gyroscope_raw()
                magnetometer = sense.get_compass()

                # Prepare data for CSV
                data_to_write = [
                    date,
                    round(temperature, 2),
                    round(humidity, 2),
                    round(pressure, 2),
                    round(altitude, 2),
                    str(accelerometer),
                    str(gyroscope),
                    round(magnetometer, 2)
                ]

                # Write data to CSV
                with open(csv_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(data_to_write)

                print("Data written to CSV:")
                print(data_to_write)
                print()
except KeyboardInterrupt:
    print("\nScript terminated by user. Data has been saved to the CSV file.")
    sense.clear()