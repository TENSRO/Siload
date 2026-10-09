# Siload bench server

A small local web server for watching load cell readings live while testing on the bench.
It uses only the Python standard library and stores readings in SQLite (`server/siload.db`).

## Run

```bash
python3 server/server.py
```

Open http://localhost:8000. At startup the server prints the LAN address the ESP32 should post to.

No hardware yet? Send fake readings:

```bash
python3 server/simulate.py            # 4 legs; +5 kg on / off every 30 s
python3 server/simulate.py --legs 1 --rate 10
```

## Dashboard

- **Cards**: live raw value per leg, average and noise σ over the last 10 samples, temperature.
- **Chart**: raw counts, live scrolling. Default view is the last 30 seconds (also 10 s, 60 s, 10 min, 1 h, 24 h).
  Views longer than 60 s show averages (about 720 points per chart, e.g. one per 2 min for 24 h).
- **Temperature chart**: on the same time axis as the counts.
- **Counts vs temperature**: scatter of raw counts against °C (older points fainter) with a least-squares line.
  Its slope is the temperature drift in counts/°C; it's fitted once the window spans at least 0.3 °C.
- **CSV**: exports every raw reading for the selected device, for analysis in Excel or Python.

## Without the server (GitHub Pages / USB direct)

Opened anywhere other than `server.py` (e.g. GitHub Pages), the same page connects to the XIAO directly
over USB with Web Serial: click **Connect USB** and pick the board (Chrome or Edge on a computer).
Readings are kept in the browser tab for 24 h and can be downloaded as CSV; nothing is stored on a server.
Close `serial_bridge.py` first, since only one program can use the USB port at a time.

`.github/workflows/pages.yml` publishes `server/static` to Pages on every push to `main`.

## API

`POST /api/readings`

```json
{"device_id": "bench-01", "raw": [8388123, 8390012], "temp_c": [14.2, 14.5]}
```

`raw` is 1 to 4 raw ADC values (use `null` for a channel that didn't respond). `temp_c` is optional.

`GET /api/readings?device_id=…&minutes=10&after_id=0` (add `&bucket=120` for 120 s averages) · `GET /api/devices` · `GET /api/export.csv?device_id=…` · `POST /api/clear?device_id=…`

## Firmware (Seeed Studio XIAO ESP32S3)

`firmware/siload_bench/siload_bench.ino` reads up to 4 HX711 boards and prints each reading as a JSON line over USB.

Wiring (leg 1): HX711 DT → D9, SCK → D10, VCC → 3V3, GND → GND. Legs 2–4 (DT/SCK): D0/D1, D2/D3, D4/D5.

Temperature: DS18B20 DATA → D7, VDD → 3V3, GND → GND, with a 4.7 kΩ resistor between DATA and 3V3.
More DS18B20s can share D7; they are reported in bus order and their addresses are printed at boot.

One-time setup (already done on this Mac):

```bash
brew install arduino-cli
arduino-cli config add board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
arduino-cli core update-index && arduino-cli core install esp32:esp32
arduino-cli lib install "HX711 Arduino Library" OneWire DallasTemperature
```

Flash, then run the server and the USB bridge (each in its own terminal):

```bash
./firmware/flash.sh
python3 server/server.py
python3 server/serial_bridge.py
```

For Wi-Fi instead of USB, set `WIFI_SSID`, `WIFI_PASSWORD` and `SERVER_URL` in `firmware/siload_bench/secrets.h`
(copied from `secrets.h.example`, git-ignored) and reflash.
