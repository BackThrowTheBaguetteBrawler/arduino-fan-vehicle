#!/usr/bin/env python3
"""
Ultra-responsive fan control – every key press is sent instantly.
Uses raw stdin + select() with zero timeout.
"""
import serial
import sys
import select
import termios
import tty
import serial.tools.list_ports

# -------------------------------------------------
# Auto-detect Arduino port
# -------------------------------------------------
def find_arduino():
    for p in serial.tools.list_ports.comports():
        if 'Arduino' in p.description or 'ACM' in p.device or 'USB' in p.device:
            return p.device
    return None

PORT = find_arduino() or '/dev/ttyACM0'
BAUD = 115200

# -------------------------------------------------
def raw_stdin():
    """Put stdin into raw mode and return old settings."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    return old

# -------------------------------------------------
def main():
    # --- open serial -------------------------------------------------
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0)   # non-blocking
    except Exception as e:
        sys.exit(f"Cannot open {PORT}: {e}")

    print(f"Connected to {PORT}")
    print("Keys: 0-9, f=full, s=stop, q=quit   (every press is sent immediately)")

    old_term = raw_stdin()
    try:
        while True:
            # ---- non-blocking read from keyboard (0-second timeout) ----
            rlist, _, _ = select.select([sys.stdin], [], [], 0)
            if rlist:
                key = sys.stdin.read(1)          # exactly one char
                if key.lower() == 'q':
                    print("\nBye!")
                    break
                ser.write(key.encode())          # send raw byte
                print(f" → {key}", end='', flush=True)

            # ---- echo any reply from Arduino (non-blocking) ----
            if ser.in_waiting:
                reply = ser.read(ser.in_waiting).decode(errors='ignore')
                print(reply, end='', flush=True)

    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_term)
        ser.close()

if __name__ == '__main__':
    main()
