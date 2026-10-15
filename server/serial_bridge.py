#!/usr/bin/env python3
"""Forward readings from an ESP32 on USB to the bench server.

The firmware prints one JSON reading per line on the serial port; this script
reads those lines and POSTs them to /api/readings. Other lines (boot messages,
errors) are echoed to the console.

    python3 server/serial_bridge.py                       # auto-detects /dev/cu.usbmodem* (or a COM port)
    python3 server/serial_bridge.py --port /dev/cu.usbserial-0001
    python server/serial_bridge.py --port COM5            # Windows

Standard library only (macOS / Linux / Windows).
"""

import argparse
import glob
import json
import os
import sys
import time
import urllib.request

if sys.platform == "win32":
    import ctypes
    import winreg
    from ctypes import wintypes
else:
    import termios

PORT_PATTERNS = ["/dev/cu.usbmodem*", "/dev/cu.usbserial*", "/dev/cu.wchusbserial*", "/dev/cu.SLAB_USBtoUART*",
                 "/dev/ttyACM*", "/dev/ttyUSB*"]


def find_port():
    if sys.platform == "win32":
        return find_com_port()
    for pattern in PORT_PATTERNS:
        ports = sorted(glob.glob(pattern))
        if ports:
            return ports[0]
    return None


def find_com_port():
    """First USB serial port listed in the registry (skips built-in and Bluetooth COM ports)."""
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DEVICEMAP\SERIALCOMM")
    except OSError:
        return None
    ports = []
    with key:
        for i in range(winreg.QueryInfoKey(key)[1]):
            device, port, _ = winreg.EnumValue(key, i)
            if not device.startswith((r"\Device\Serial", r"\Device\BthModem")):
                ports.append(port)
    return sorted(ports, key=lambda p: int(p[3:]) if p[3:].isdigit() else 0)[0] if ports else None


def open_serial(path, baud=115200):
    if sys.platform == "win32":
        return WinSerial(path, baud)
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


if sys.platform == "win32":
    class DCB(ctypes.Structure):
        _fields_ = [("DCBlength", wintypes.DWORD), ("BaudRate", wintypes.DWORD),
                    ("fBinary", wintypes.DWORD, 1), ("fParity", wintypes.DWORD, 1),
                    ("fOutxCtsFlow", wintypes.DWORD, 1), ("fOutxDsrFlow", wintypes.DWORD, 1),
                    ("fDtrControl", wintypes.DWORD, 2), ("fDsrSensitivity", wintypes.DWORD, 1),
                    ("fTXContinueOnXoff", wintypes.DWORD, 1), ("fOutX", wintypes.DWORD, 1),
                    ("fInX", wintypes.DWORD, 1), ("fErrorChar", wintypes.DWORD, 1),
                    ("fNull", wintypes.DWORD, 1), ("fRtsControl", wintypes.DWORD, 2),
                    ("fAbortOnError", wintypes.DWORD, 1), ("fDummy2", wintypes.DWORD, 17),
                    ("wReserved", wintypes.WORD), ("XonLim", wintypes.WORD), ("XoffLim", wintypes.WORD),
                    ("ByteSize", wintypes.BYTE), ("Parity", wintypes.BYTE), ("StopBits", wintypes.BYTE),
                    ("XonChar", ctypes.c_char), ("XoffChar", ctypes.c_char), ("ErrorChar", ctypes.c_char),
                    ("EofChar", ctypes.c_char), ("EvtChar", ctypes.c_char), ("wReserved1", wintypes.WORD)]

    class COMMTIMEOUTS(ctypes.Structure):
        _fields_ = [(name, wintypes.DWORD) for name in (
            "ReadIntervalTimeout", "ReadTotalTimeoutMultiplier", "ReadTotalTimeoutConstant",
            "WriteTotalTimeoutMultiplier", "WriteTotalTimeoutConstant")]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.restype = wintypes.HANDLE

    class WinSerial:
        """Minimal read-only COM port (8N1, raw) using the Win32 API."""

        def __init__(self, port, baud):
            self.handle = kernel32.CreateFileW("\\\\.\\" + port, 0x80000000, 0, None, 3, 0, None)  # GENERIC_READ, OPEN_EXISTING
            if self.handle == wintypes.HANDLE(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            dcb = DCB(DCBlength=ctypes.sizeof(DCB))
            kernel32.GetCommState(self.handle, ctypes.byref(dcb))
            dcb.BaudRate, dcb.ByteSize, dcb.Parity, dcb.StopBits = baud, 8, 0, 0
            dcb.fBinary, dcb.fParity, dcb.fOutxCtsFlow, dcb.fOutxDsrFlow = 1, 0, 0, 0
            dcb.fOutX = dcb.fInX = dcb.fNull = dcb.fAbortOnError = 0
            dcb.fDtrControl = dcb.fRtsControl = 1                       # assert DTR/RTS, like the macOS port
            # Return as soon as any bytes arrive, or after 1 s with none.
            timeouts = COMMTIMEOUTS(0xFFFFFFFF, 0xFFFFFFFF, 1000, 0, 0)
            if not (kernel32.SetCommState(self.handle, ctypes.byref(dcb))
                    and kernel32.SetCommTimeouts(self.handle, ctypes.byref(timeouts))):
                err = ctypes.get_last_error()
                self.close()
                raise ctypes.WinError(err)

        def read(self, size):
            buf = ctypes.create_string_buffer(size)
            n = wintypes.DWORD()
            while not n.value:                                          # empty read = timeout, not EOF
                if not kernel32.ReadFile(self.handle, buf, size, ctypes.byref(n), None):
                    raise ctypes.WinError(ctypes.get_last_error())      # e.g. board unplugged
            return buf.raw[:n.value]

        def close(self):
            if self.handle:
                kernel32.CloseHandle(self.handle)
                self.handle = None

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.close()


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
