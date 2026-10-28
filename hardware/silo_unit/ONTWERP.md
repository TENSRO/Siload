# SILOAD LOAD CELL REV A (Silo Unit — Load Cell & Temp PCB)

Compacte KiCad 10 prototype carrier-PCB voor de **Siload Silo Unit**, **68 x 44 mm**, 2 koperlagen, 1,6 mm FR4, 100% through-hole.
Op deze print prikt dezelfde **Seeed XIAO ESP32-S3 + Wio-SX1262 LoRa-stack (`J1`/`J2`)** als op de Farm Hub, samen met **1x groene Heemol HX711 module (`34 x 21 mm`, `J3` 4-pin + `J4` 6-pin)**, een goedkope **CD4052BE / 74HC4052N DIP-16 multiplexer (`U1`)**, **4 load-cell headers (`J5`–`J8`)** en **1 DS18B20 temperatuursensor-header (`J9`)**.

## Hoe de 4-sensor selectie werkt

- **Exacte pasvorm voor de Heemol HX711 (`34 x 21 mm`, ASIN `B0C9QBS2WL`):**
  - Links (`J3`, 4-polig): `VCC` (`+3V3`), `SCK` (`D6`), `DT` (`D0`), `GND`.
  - Rechts (`J4`, 6-polig, `25,4 mm` rij-afstand): `B+` (NC), `B-` (NC), `A+` (`HX_AP`), `A-` (`HX_AN`), `E-` (`LC_EN`), `E+` (`LC_EP`).
- **Continue brugvoeding (`E+` en `E-`):** Alle 4 de sensoren (`J5`–`J8`) krijgen continu excitatie (`E+` en `E-`) vanaf de HX711 (`J4.6` en `J4.5`), zodat de rekstrookbruggen thermisch stabiel blijven.
- **Actieve kanaalselectie via `U1` (`CD4052BE` / `74HC4052N`, DIP-16, ~€0,25):**
  - De 4 differentiële meetparen `(A+, A-)` van sensor 1 t/m 4 gaan naar de dubbele 4-kanaals multiplexer `U1` (`X0..X3` voor `A+`, `Y0..Y3` voor `A-`).
  - De gemeenschappelijke uitgang `(X_COM, Y_COM)` gaat rechtstreeks naar `A+` (`J4.3`) en `A-` (`J4.4`) van de HX711. Omdat de ingangsimpedantie van de HX711 hoogohmig is, loopt er vrijwel geen stroom door de mux-kanalen.
  - De twee adreslijnen `SEL_A` (`U1.10`) en `SEL_B` (`U1.9`) zitten op `D8` (`GPIO7`) en `D10` (`GPIO9`). Tussen de LoRa-pakketten door is `LORA_NSS` (`D4`) hoog en negeert de SX1262 LoRa-radio `D8`/`D10` volledig, zodat de ESP32 vrij sensor 1 (`00`), 2 (`01`), 3 (`10`) of 4 (`11`) kan selecteren en uitlezen via `D0` (`DT`) en `D6` (`SCK`).
- **Temperatuursensor (`J9` + `R1`):**
  - 3-polige header `J9` (`3V3`, `DQ` op `D7`/`GPIO44`, `GND`) met een through-hole `4,7 kΩ` pull-up weerstand (`R1`) naar `+3V3`.

## Pinout-overzicht

| Onderdeel | XIAO Pin | GPIO | Net | Carrier-verbinding |
| --- | --- | --- | --- | --- |
| HX711 DT | D0 | 1 | `HX_DT` | `J1.1` -> `J3.3` |
| HX711 SCK | D6 | 43 | `HX_SCK` | `J1.7` -> `J3.2` |
| DS18B20 1-Wire | D7 | 44 | `ONEWIRE_DQ` | `J2.7` -> `J9.2` + `R1.2` (`4.7k` naar `+3V3`) |
| Mux Select A (bit 0) | D8 | 7 | `MUX_A` | `J2.6` -> `U1.10` (`SEL_A`) |
| Mux Select B (bit 1) | D10 | 9 | `MUX_B` | `J2.4` -> `U1.9` (`SEL_B`) |
| Voeding 3,3 V | 3V3 | – | `+3V3` | `J2.3` -> `J3.1, U1.16, J9.1, R1.1, C1.1, C2.1` |
| Massa | GND | – | `GND` | `J2.2` -> `J3.4, U1.6..8, J9.3, C1.2, C2.2` |
