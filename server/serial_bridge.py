#!/usr/bin/env python3
"""Forward readings from an ESP32 on USB to the bench server.

The firmware prints one JSON reading per line on the serial port; this script
reads those lines and POSTs them to /api/readings. Other lines (boot messages,
errors) are echoed to the console.

    python3 server/serial_bridge.py                       # auto-detects /dev/cu.usbmodem*
    python3 server/serial_bridge.py --port /dev/cu.usbserial-0001

Standard library only (macOS / Linux).
"""

import argparse
import glob
import json
import os
import termios
import time
import urllib.request

PORT_PATTERNS = ["/dev/cu.usbmodem*", "/dev/cu.usbserial*", "/dev/cu.wchusbserial*", "/dev/cu.SLAB_USBtoUART*",
                 "/dev/ttyACM*", "/dev/ttyUSB*"]


def find_port():
    for pattern in PORT_PATTERNS:
        ports = sorted(glob.glob(pattern))
        if ports:
            return ports[0]
    return None


def open_serial(path, baud=115200):
    fd = os.open(path, os.O_RDONLY | os.O_NOCTTY)
    attrs = termios.tcgetattr(fd)
    speed = getattr(termios, f"B{baud}")
    attrs[0] = 0                                                    # iflag: raw input
    attrs[1] = 0                                                    # oflag
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL         # cflag: 8N1
    attrs[3] = 0                                                    # lflag: no echo / canonical
    attrs[4] = attrs[5] = speed
    attrs[6][termios.VMIN] = 1
    attrs[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    return os.fdopen(fd, "rb", buffering=0)


def post(url, line):
    req = urllib.request.Request(url, line.encode(), {"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=2).read()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", help="serial device (default: auto-detect)")
    p.add_argument("--baud", type=int, default=115200)
    p.add_argument("--url", default="http://localhost:8000/api/readings")
    args = p.parse_args()

    while True:
        port = args.port or find_port()
        if not port:
            print("No ESP32 found on USB, retrying… (plug it in, or pass --port)")
            time.sleep(2)
            continue

        print(f"Reading {port} → {args.url}")
        try:
            buf = b""
            count = 0
            with open_serial(port, args.baud) as ser:
                while True:
                    chunk = ser.read(256)
                    if not chunk:
                        raise OSError("port closed")
                    buf += chunk
                    while b"\n" in buf:
                        raw_line, buf = buf.split(b"\n", 1)
                        line = raw_line.decode(errors="replace").strip()
                        if not line.startswith("{"):
                            if line:
                                print(f"[esp32] {line}")
                            continue
                        try:
                            json.loads(line)
                            post(args.url, line)
                            count += 1
                            print(f"\r{count} readings forwarded · last: {line[:70]}", end="", flush=True)
                        except json.JSONDecodeError:
                            print(f"\n[skip] not valid JSON: {line[:80]}")
                        except OSError as e:
                            print(f"\n[server] {e} (is server/server.py running?)")
        except OSError as e:
            print(f"\nLost {port}: {e}. Reconnecting…")
            time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
