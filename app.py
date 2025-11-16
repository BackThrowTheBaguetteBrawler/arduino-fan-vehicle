#!/usr/bin/env python3
"""
Flask Dual Fan Control – Pin 11 (A), Pin 10 (B)
"""
from flask import Flask, render_template, jsonify, Response
import serial, serial.tools.list_ports, threading, time, sys
from collections import deque

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
ser = None
serial_lock = threading.Lock()

def init_serial():
    global ser
    for attempt in range(6):
        try:
            ser = serial.Serial(PORT, BAUD, timeout=0)
            time.sleep(2)
            print(f"[OK] Connected to {PORT}")
            return
        except serial.SerialException as e:
            if 'Device or resource busy' in str(e):
                print(f"[BUSY] Retry {attempt+1}/6...")
                time.sleep(1)
            else:
                print(f"[ERROR] {e}")
                sys.exit(1)
    sys.exit("[FATAL] Port open failed")
init_serial()

# -------------------------------------------------
# Send command: 'a5', 'bf', 'as', etc.
# -------------------------------------------------
def send_command(fan: str, cmd: str):
    """fan = 'a' or 'b', cmd = '0'-'9','f','s'"""
    if fan not in ('a', 'b') or cmd not in '0123456789fs':
        return
    with serial_lock:
        if ser and ser.is_open:
            try:
                ser.write(fan.encode())
                time.sleep(0.001)
                ser.write(cmd.encode())
                ser.flush()
            except Exception as e:
                print(f"[WRITE FAIL] {e}")

# -------------------------------------------------
# Background reader → SSE
# -------------------------------------------------
feedback_buffer = deque(maxlen=50)

def serial_reader():
    buffer = ""
    while True:
        if ser and ser.in_waiting:
            try:
                buffer += ser.read(ser.in_waiting).decode(errors='ignore')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
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

@app.route('/cmd/<fan>/<key>')
def command(fan, key):
    """fan = a|b, key = 0-9,f,s"""
    if fan in ('a', 'b') and len(key) == 1 and key.lower() in '0123456789fs':
        send_command(fan, key.lower())
        return jsonify(status="ok", fan=fan.upper(), key=key.upper())
    return jsonify(status="invalid"), 400

# SSE Stream
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
if __name__ == '__main__':
    ip = [l.split()[1] for l in __import__('subprocess')
          .check_output(["ip", "route"]).decode().splitlines()
          if 'default' in l][0].split('/')[0]
    print(f"\nWeb UI: http://{ip}:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
