#!/usr/bin/env python3
"""
Flask web UI for ultra-responsive fan control.
Works with the Arduino sketch above (pin 11 PWM).
"""

from flask import Flask, render_template, jsonify, request
import serial
import serial.tools.list_ports
import threading
import time
import sys

app = Flask(__name__)

# -------------------------------------------------
# Auto-detect Arduino
# -------------------------------------------------
def find_arduino():
    for p in serial.tools.list_ports.comports():
        if 'Arduino' in p.description or 'ACM' in p.device or 'USB' in p.device:
            return p.device
    return '/dev/ttyACM0'

PORT = find_arduino()
BAUD = 115200

# Global serial
ser = None
serial_lock = threading.Lock()

# -------------------------------------------------
# Serial init with retry on "busy"
# -------------------------------------------------
def init_serial():
    global ser
    for attempt in range(6):
        try:
            ser = serial.Serial(PORT, BAUD, timeout=0)
            time.sleep(2)  # Arduino reset
            print(f"[OK] Connected to {PORT}")
            return
        except serial.SerialException as e:
            if 'Device or resource busy' in str(e):
                print(f"[BUSY] Port busy, retry {attempt+1}/6 in 1s...")
                time.sleep(1)
            else:
                print(f"[ERROR] Serial: {e}")
                sys.exit(1)
    sys.exit("[FATAL] Could not open serial port after retries")

init_serial()

# -------------------------------------------------
# Safe send
# -------------------------------------------------
def send_command(cmd: str):
    with serial_lock:
        if ser and ser.is_open:
            try:
                ser.write(cmd.encode())
                ser.flush()
            except Exception as e:
                print(f"[WRITE FAIL] {e}")

# -------------------------------------------------
# Background reader – pushes feedback to browser via SSE
# -------------------------------------------------
from collections import deque
feedback_buffer = deque(maxlen=50)  # last 50 messages

def serial_reader():
    while True:
        if ser and ser.in_waiting:
            try:
                line = ser.readline().decode(errors='ignore').strip()
                if line:
                    feedback_buffer.append(line)
            except:
                pass
        time.sleep(0.005)

threading.Thread(target=serial_reader, daemon=True).start()

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cmd/<key>')
def command(key):
    if len(key) == 1 and key.lower() in '0123456789fs':
        send_command(key)
        return jsonify(status="ok", key=key)
    return jsonify(status="invalid"), 400

# -------------------------------------------------
# Server-Sent Events (SSE) – live Arduino feedback
# -------------------------------------------------
from flask import Response

@app.route('/stream')
def stream():
    def event_stream():
        last_len = 0
        while True:
            if len(feedback_buffer) > last_len:
                msg = feedback_buffer[-1]
                last_len = len(feedback_buffer)
                yield f"data: {msg}\n\n"
            time.sleep(0.05)
    return Response(event_stream(), mimetype="text/event-stream")

# -------------------------------------------------
# Run
# -------------------------------------------------
if __name__ == '__main__':
    # Accessible from phone/tablet on same WiFi
    print(f"\nWeb UI: http://YOUR_IP:5000")
    print("   (Find YOUR_IP with: ip addr show | grep inet)")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
