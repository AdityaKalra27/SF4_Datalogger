# arduino_communication.py
# Serial Communication between Arduino and PC
# SF4: Data Logger
# jz587 and ak2444

# Import Necessary Modules
import serial
import threading
import csv
from datetime import datetime

# Arduino Setup
PORT      = 'COM9'
BAUD_RATE = 9600
LOG_FILE  = "weather_monitoring.csv"
MAX_POINTS = 50
MAX_BUFFER_SIZE = 200000

# Buffers for Storing Data
temperatures = []
humidities   = []
pressures    = []
luxintensities = []
wind_speeds  = []
time_data    = []

# Create new log file everytime program is running (clearing any past data)
with open(LOG_FILE, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "temp", "hum", "pres", "lux", "wind"])

# function for computing checksum
def compute_xor_checksum(s: str) -> int:
    cs = 0
    for ch in s:
        cs ^= ord(ch)
    return cs

# thread for reading from and writing to serial
def reader_thread():
    # Communications protocol

    # Check if Arduino port can be accessed
    try:
        ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
    except serial.SerialException:
        print("Could not open", PORT)
        return
    

    with open(LOG_FILE, 'a', newline='') as log_file:
        csv_writer = csv.writer(log_file)

        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            # print(line)

            # Check if data has been transmitted
            if not line:
                print("No data received from Arduino")
                continue

            # Check if checksum has been transmitted
            if " CHK:" not in line:
                print("Checksum not transmitted error has occured")
                continue

            payload, check_sum = line.split(" CHK:")
            #print(payload, check_sum)
            
            # Check if valid checksum has been received
            try:
                rx_checksum = int(check_sum, 16)
            except ValueError:
                print("Invalid checksum")
                # Flash LED by sending command to serial
                sent_command = "LED_ON" + '\n'
                ser.write(sent_command.encode('ascii'))
                ser.flush()
                continue
            
            # Recalculate checksum and compare to received checksum
            if compute_xor_checksum(payload) != rx_checksum:
                print("Data has been corrupted")
                # Flash LED by sending command to serial
                sent_command = "LED_ON" + '\n'
                ser.write(sent_command.encode('ascii'))
                ser.flush()
                continue
            
            # Ensuring all sensor values have been transmitted
            parts = payload.split()
            #print(parts)
            if len(parts) != 5:
                print("Number of elements in line error has occured")
                # Flash LED by sending command to serial
                sent_command = "LED_ON" + '\n'
                ser.write(sent_command.encode('ascii'))
                ser.flush()
                continue
            
            # Parsing payload data
            try:
                sensor_to_val = {}
                for sv in parts:
                    k, v = sv.split(':')
                    sensor_to_val[k] = float(v)

                hum  = sensor_to_val['HUM']
                temp = sensor_to_val['T']
                lux  = sensor_to_val['LUX']
                pres = sensor_to_val['PRES']
                wind = sensor_to_val['WIND']

            except (KeyError, ValueError):
                # Flash LED by sending command to serial
                sent_command = "LED_ON" + '\n'
                ser.write(sent_command.encode('ascii'))
                ser.flush()
                continue

            # Obtaining time stamp
            now = datetime.now()
            ts = now.strftime("%H:%M:%S")
            
            # Clear last element if size of buffer exceeded
            if len(temperatures) >= MAX_BUFFER_SIZE:
                temperatures.pop(0)
                humidities.pop(0)
                pressures.pop(0)
                luxintensities.pop(0)
                wind_speeds.pop(0)
                time_data.pop(0)

            # Add latest value to buffers
            temperatures.append(temp)
            humidities.append(hum)
            pressures.append(pres)
            luxintensities.append(lux)
            wind_speeds.append(wind)
            time_data.append(ts)

            # Write latest data to log file
            csv_writer.writerow([
                now.isoformat(),
                f"{temp:.2f}",
                f"{hum:.2f}",
                f"{pres:.2f}",
                f"{lux:.2f}",
                f"{wind:.2f}"
            ])
            log_file.flush()

def start_reader():
    thread = threading.Thread(target=reader_thread, daemon=True)
    thread.start()
