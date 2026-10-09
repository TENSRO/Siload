#!/usr/bin/env python3
"""Send fake HX711 readings to the bench server, so the dashboard can be tested without hardware.

    python3 server/simulate.py                  # 4 legs, 1 reading/s
    python3 server/simulate.py --legs 1 --rate 10

Every 30 s a "weight" of 5 kg is placed on or removed from the load cells.
"""

import argparse
import json
import math
import random
import time
import urllib.request

COUNTS_PER_KG = 21000  # rough HX711 + 5 kg bar load cell at gain 128


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8000/api/readings")
    p.add_argument("--device", default="sim-01")
    p.add_argument("--legs", type=int, default=4, choices=range(1, 5))
    p.add_argument("--rate", type=float, default=1.0, help="readings per second")
    args = p.parse_args()

    offsets = [random.randint(-200000, 200000) for _ in range(args.legs)]
    factors = [COUNTS_PER_KG * random.uniform(0.9, 1.1) for _ in range(args.legs)]
    t0 = time.time()
    print(f"Sending to {args.url} as '{args.device}' — Ctrl+C to stop")

    while True:
        t = time.time() - t0
        load_kg = 5.0 if int(t // 30) % 2 else 0.0
        temp = 18 + 3 * math.sin(t / 300)
        raw = []
        for i in range(args.legs):
            drift = 40 * (temp - 18)                     # temperature drift, counts
            noise = random.gauss(0, 60)
            raw.append(round(offsets[i] + factors[i] * load_kg / args.legs + drift + noise))
        body = json.dumps({
            "device_id": args.device,
            "raw": raw,
            "temp_c": [round(temp + random.gauss(0, 0.05), 2) for _ in range(args.legs)],
        }).encode()
        req = urllib.request.Request(args.url, body, {"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=2).read()
        except OSError as e:
            print("post failed:", e)
        time.sleep(1 / args.rate)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
