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
- **Chart**: raw counts, live scrolling. Default view is the last 30 seconds (also 10 s, 60 s, 10 min, 1 h).
- **Temperature chart**: appears below it, on the same time axis, as soon as readings include `temp_c`.
- **CSV**: exports every raw reading for the selected device, for analysis in Excel or Python.

## API

`POST /api/readings`

```json
{"device_id": "bench-01", "raw": [8388123, 8390012], "temp_c": [14.2, 14.5]}
```

`raw` is 1 to 4 raw ADC values (use `null` for a channel that didn't respond). `temp_c` is optional.

`GET /api/readings?device_id=…&minutes=10&after_id=0` · `GET /api/devices` · `GET /api/export.csv?device_id=…` · `POST /api/clear?device_id=…`

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
