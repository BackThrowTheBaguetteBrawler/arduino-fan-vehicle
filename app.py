#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
import serial
import serial.tools.list_ports
import threading
import time

app = Flask(__name__)

# --- Auto-find Arduino ---
def find_arduino():
    for p in serial.tools.list_ports.comports():
        if 'Arduino' in p.description or 'ACM' in p.device or 'USB' in p.device:
            return p.device
    return '/dev/ttyACM0'

PORT = find_arduino()
BAUD = 115200

# Global serial object
ser = None
serial_lock = threading.Lock()

def init_serial():
    global ser
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0)
        time.sleep(2)  # wait for Arduino reset
        print(f"Connected to {PORT}")
    except Exception as e:
        print(f"Serial error: {e}")
        ser = None

init_serial()

# --- Send command safely ---
def send_command(cmd):
    with serial_lock:
        if ser and ser.is_open:
            try:
                ser.write(cmd.encode())
                ser.flush()
            except:
                print("Serial write failed")
        else:
            print("Serial not open")

# --- Background reader (optional: show live feedback) ---
def serial_reader():
    while True:
        if ser and ser.in_waiting:
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                print(f"Arduino: {line}")
        time.sleep(0.01)

threading.Thread(target=serial_reader, daemon=True).start()

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cmd/<key>')
def command(key):
    if len(key) == 1 and key in '0123456789fFsS':
        send_command(key)
        return jsonify(status="ok", key=key)
    return jsonify(status="invalid"), 400

if __name__ == '__main__':
    # Allow access from your phone/tablet on same WiFi
    app.run(host='0.0.0.0', port=5000, debug=False)
