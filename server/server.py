#!/usr/bin/env python3
"""Siload bench server: receives load cell readings and serves a live dashboard.

No dependencies beyond the Python standard library.

    python3 server/server.py            # listens on 0.0.0.0:8000
    python3 server/server.py --port 8080

Devices POST JSON to /api/readings:

    {"device_id": "silo-01", "raw": [8388123, 8390012, 8387761, 8389540],
     "temp_c": [14.2, 14.5, 14.1, 14.3]}

`raw` holds one raw ADC value per channel (1 to 4 legs); `temp_c` is optional.
"""

import argparse
import csv
import io
import json
import socket
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB_PATH = ROOT / "siload.db"
MAX_CHANNELS = 4


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ts        REAL    NOT NULL,          -- server receive time, unix seconds
                device_id TEXT    NOT NULL,
                raw       TEXT    NOT NULL,          -- JSON array of raw ADC values
                temp_c    TEXT                       -- JSON array of temperatures, or NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_readings_device_ts ON readings(device_id, ts)")


def parse_reading(body):
    data = json.loads(body)
    device_id = str(data.get("device_id", "unknown"))[:64]

    raw = data.get("raw")
    if isinstance(raw, (int, float)):
        raw = [raw]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_CHANNELS:
        raise ValueError(f"'raw' must be a number or a list of 1-{MAX_CHANNELS} numbers")
    raw = [None if v is None else float(v) for v in raw]  # null = HX711 not responding

    temp = data.get("temp_c")
    if isinstance(temp, (int, float)):
        temp = [temp]
    if temp is not None:
        temp = [None if v is None else float(v) for v in temp]

    return device_id, raw, temp


def row_to_dict(row):
    return {
        "id": row["id"],
        "ts": row["ts"],
        "device_id": row["device_id"],
        "raw": json.loads(row["raw"]),
        "temp_c": json.loads(row["temp_c"]) if row["temp_c"] else None,
    }


def bucket_average(readings, bucket):
    """Average readings per `bucket` seconds, per channel, ignoring nulls.

    Each output row has the mean `ts` of its bucket and `n`, the number of readings averaged.
    """
    def mean_columns(lists):
        width = max((len(l) for l in lists), default=0)
        out = []
        for i in range(width):
            vals = [l[i] for l in lists if i < len(l) and l[i] is not None]
            out.append(sum(vals) / len(vals) if vals else None)
        return out

    groups = {}
    for r in readings:
        groups.setdefault(int(r["ts"] // bucket), []).append(r)

    result = []
    for _, rows in sorted(groups.items()):
        temps = [r["temp_c"] for r in rows if r["temp_c"]]
        result.append({
            "id": rows[-1]["id"],
            "ts": sum(r["ts"] for r in rows) / len(rows),
            "device_id": rows[-1]["device_id"],
            "raw": mean_columns([r["raw"] for r in rows]),
            "temp_c": mean_columns(temps) if temps else None,
            "n": len(rows),
        })
    return result


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Keep the console quiet for the dashboard's polling requests.
        if not self.path.startswith("/api/readings?"):
            super().log_message(fmt, *args)

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        qs = parse_qs(url.query)

        if url.path in ("/", "/index.html"):
            body = (STATIC / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif url.path == "/api/devices":
            with db() as conn:
                rows = conn.execute(
                    "SELECT device_id, COUNT(*) AS n, MAX(ts) AS last_ts FROM readings GROUP BY device_id ORDER BY last_ts DESC"
                ).fetchall()
            self.send_json([dict(r) for r in rows])

        elif url.path == "/api/readings":
            # ?device_id=...&after_id=123  -> only new rows (for live polling)
            # ?device_id=...&minutes=10    -> history window
            # ?device_id=...&minutes=1440&bucket=120 -> averages per 120 s bucket (long windows)
            device_id = qs.get("device_id", [None])[0]
            after_id = int(qs.get("after_id", ["0"])[0])
            minutes = float(qs.get("minutes", ["10"])[0])
            limit = min(int(qs.get("limit", ["5000"])[0]), 50000)
            bucket = float(qs.get("bucket", ["0"])[0])

            sql = "SELECT * FROM readings WHERE id > ? AND ts >= ?"
            args = [after_id, time.time() - minutes * 60]
            if device_id:
                sql += " AND device_id = ?"
                args.append(device_id)

            if bucket > 0:
                with db() as conn:
                    rows = conn.execute(sql + " ORDER BY id", args).fetchall()
                self.send_json(bucket_average([row_to_dict(r) for r in rows], bucket))
                return

            sql += " ORDER BY id DESC LIMIT ?"
            args.append(limit)
            with db() as conn:
                rows = conn.execute(sql, args).fetchall()
            self.send_json([row_to_dict(r) for r in reversed(rows)])

        elif url.path == "/api/export.csv":
            device_id = qs.get("device_id", [None])[0]
            sql, args = "SELECT * FROM readings", []
            if device_id:
                sql += " WHERE device_id = ?"
                args.append(device_id)
            sql += " ORDER BY id"

            out = io.StringIO()
            w = csv.writer(out)
            w.writerow(["id", "iso_time", "ts", "device_id"]
                       + [f"raw_{i + 1}" for i in range(MAX_CHANNELS)]
                       + [f"temp_c_{i + 1}" for i in range(MAX_CHANNELS)])
            with db() as conn:
                for r in conn.execute(sql, args):
                    d = row_to_dict(r)
                    raw = d["raw"] + [""] * (MAX_CHANNELS - len(d["raw"]))
                    temp = (d["temp_c"] or []) + [""] * (MAX_CHANNELS - len(d["temp_c"] or []))
                    iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(d["ts"]))
                    w.writerow([d["id"], iso, f"{d['ts']:.3f}", d["device_id"]] + raw + temp[:MAX_CHANNELS])

            body = out.getvalue().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", 'attachment; filename="siload-readings.csv"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        url = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""

        if url.path == "/api/readings":
            try:
                device_id, raw, temp = parse_reading(body)
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                self.send_json({"error": str(e)}, 400)
                return
            with db() as conn:
                cur = conn.execute(
                    "INSERT INTO readings (ts, device_id, raw, temp_c) VALUES (?, ?, ?, ?)",
                    (time.time(), device_id, json.dumps(raw), json.dumps(temp) if temp else None),
                )
            self.send_json({"ok": True, "id": cur.lastrowid}, 201)

        elif url.path == "/api/clear":
            qs = parse_qs(url.query)
            device_id = qs.get("device_id", [None])[0]
            with db() as conn:
                if device_id:
                    conn.execute("DELETE FROM readings WHERE device_id = ?", (device_id,))
                else:
                    conn.execute("DELETE FROM readings")
            self.send_json({"ok": True})

        else:
            self.send_json({"error": "not found"}, 404)


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(description="Siload bench server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    init_db()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Siload bench server")
    print(f"  Dashboard:    http://localhost:{args.port}")
    print(f"  ESP32 posts:  http://{lan_ip()}:{args.port}/api/readings")
    print(f"  Database:     {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
