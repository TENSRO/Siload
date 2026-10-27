# Siload pinout (rev B)

| Unit | Board | On top |
|---|---|---|
| Silo unit | Seeed XIAO ESP32-S3 **Plus** | Wio-SX1262 for XIAO (LoRa, EU868) |
| Farm hub | Seeed XIAO ESP32-S3 | Wio-SX1262 for XIAO (LoRa, EU868) |

```
Wio-SX1262 (LoRa)      U.FL → SMA
XIAO ESP32-S3 (Plus)   USB-C for flashing
Carrier PCB            female headers
```

**LoRa** = on the stacked LoRa board, don't route on the carrier PCB.

## Silo unit: LoRa · 4 × HX711 · temperature

| Pin | GPIO | Connects to |
|---|---|---|
| D0 | 1 | HX711 leg 1 · DT |
| D1 | 2 | **LoRa** DIO1 |
| D2 | 3 | **LoRa** RESET |
| D3 | 4 | **LoRa** BUSY |
| D4 | 5 | **LoRa** NSS |
| D5 | 6 | **LoRa** RF switch |
| D6 | 43 | HX711 leg 1 · SCK |
| D7 | 44 | DS18B20 bus · 1–2 sensors · 4.7 kΩ to 3V3 |
| D8 | 7 | **LoRa** SPI SCK |
| D9 | 8 | **LoRa** SPI MISO |
| D10 | 9 | **LoRa** SPI MOSI |
| D11 | 38 | HX711 leg 2 · DT |
| D12 | 39 | HX711 leg 2 · SCK |
| D13 | 40 | HX711 leg 3 · DT |
| D14 | 41 | HX711 leg 3 · SCK |
| D15 | 42 | HX711 leg 4 · DT |
| D16 | 10 | HX711 leg 4 · SCK |
| D17–D19 | 13 · 12 · 11 | spare |
| 5V | – | power in, via Schottky diode |
| 3V3 | – | LoRa, 4 × HX711, DS18B20 |

| Load cell / bridge wire | HX711 |
|---|---|
| red | E+ |
| black | E− |
| green | A+ |
| white | A− |

HX711 ×4: VCC (+VDD) → 3V3, GND → GND. DS18B20: VDD → 3V3, DATA → D7, GND → GND.

## Farm hub: LoRa · Ethernet

| Pin | GPIO | Connects to |
|---|---|---|
| D0 | 1 | W5500 CS |
| D1 | 2 | **LoRa** DIO1 |
| D2 | 3 | **LoRa** RESET |
| D3 | 4 | **LoRa** BUSY |
| D4 | 5 | **LoRa** NSS |
| D5 | 6 | **LoRa** RF switch |
| D6 | 43 | W5500 RST |
| D7 | 44 | W5500 INT (optional) |
| D8 | 7 | SPI SCK → **LoRa** + W5500 (shared) |
| D9 | 8 | SPI MISO → **LoRa** + W5500 (shared) |
| D10 | 9 | SPI MOSI → **LoRa** + W5500 (shared) |
| 5V | – | power in (USB-C or PoE 5 V), via Schottky diode |
| 3V3 | – | LoRa · W5500 on its own 3.3 V regulator |

## Rules

- **D1–D5:** no traces on the carrier PCB.
- **10 kΩ pull-up to 3V3** on every chip select: D4 (LoRa) on both units, D0 (W5500) on the hub.
- **D11–D19** exist on the XIAO ESP32-S3 Plus only: check their position (underside pads) before layout.
- **RJ45** with magnetics, at the board edge opposite the antenna. TX± / RX± as 100 Ω pairs, no vias.
- **HX711 and bridge traces** short and paired, away from SPI and LoRa.
- **Decoupling** 100 nF + 10 µF at every module.
- **USB-C** on the XIAO stays reachable through the enclosure.

LoRa, temperature and HX711 leg 1 match the current firmware (`firmware/siload_bench`, `firmware/farm_hub`).
HX711 legs 2–4 and the W5500 pins are proposed; firmware support follows.
