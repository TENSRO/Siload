from pathlib import Path
import csv, json, xml.etree.ElementTree as ET
import pcbnew as p

root = Path(__file__).resolve().parent
NAME = 'SILOAD LOAD CELL REV A'
b = p.LoadBoard(str(root / (NAME + '.kicad_pcb')))
tree = ET.parse(root / 'connectivity.xml')
schematic = {
    n.attrib['name']: {(v.attrib['ref'], v.attrib['pin']) for v in n.findall('node')}
    for n in tree.findall('./nets/net')
}
desired = {}
for name in schematic:
    n = b.FindNet(name)
    if not n or n.GetNetname() != name:
        n = p.NETINFO_ITEM(b, name)
        b.Add(n)
    desired[name] = n

for track in b.GetTracks():
    name = track.GetNetname()
    if name and not name.startswith('/') and not name.startswith('unconnected-'):
        track.SetNet(desired['/' + name])

for f in b.GetFootprints():
    for pad in f.Pads():
        node = (f.GetReference(), pad.GetNumber())
        for name, nodes in schematic.items():
            if node in nodes:
                pad.SetNet(desired[name])
                break

b.BuildConnectivity()
p.SaveBoard(str(root / (NAME + '.kicad_pcb')), b)

pcb = {}
for f in b.GetFootprints():
    for pad in f.Pads():
        if pad.GetNetname():
            pcb.setdefault(pad.GetNetname(), set()).add((f.GetReference(), pad.GetNumber()))
assert pcb == schematic, (pcb, schematic)

with (root / 'pinout-concept.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['XIAO / Module', 'GPIO', 'Net', 'Connected pads'])
    w.writerows(
        [
            ['XIAO D0', '1', 'HX_DT', 'J1.1 -> J3.3 (HX711 DT)'],
            ['XIAO D6', '43', 'HX_SCK', 'J1.7 -> J3.2 (HX711 SCK)'],
            ['XIAO D7', '44', 'ONEWIRE_DQ', 'J2.7 -> J9.2 (DS18B20 DQ) + R1.2 (4.7k pull-up)'],
            ['XIAO D8 (idle SPI SCK)', '7', 'MUX_A', 'J2.6 -> U1.10 (CD4052BE SEL_A)'],
            ['XIAO D10 (idle SPI MOSI)', '9', 'MUX_B', 'J2.4 -> U1.9 (CD4052BE SEL_B)'],
            ['XIAO 3V3', '', '+3V3', 'J2.3 -> J3.1, U1.16, J9.1, R1.1, C1.1, C2.1'],
            ['XIAO GND', '', 'GND', 'J2.2 -> J3.4, U1.6, U1.7, U1.8, J9.3, C1.2, C2.2'],
            ['HX711 Excitation', '', 'LC_EP / LC_EN', 'J4.6 (E+) / J4.5 (E-) -> J5..J8 pins 1 & 2 (E+ red, E- blk)'],
            ['HX711 Differential In', '', 'HX_AP / HX_AN', 'J4.3 (A+) -> U1.13 (X_COM), J4.4 (A-) -> U1.3 (Y_COM)'],
            ['Sensor 1 (SEL=00)', '', 'LC1_AN / LC1_AP', 'J5.3 -> U1.1 (Y0), J5.4 -> U1.12 (X0)'],
            ['Sensor 2 (SEL=01)', '', 'LC2_AN / LC2_AP', 'J6.3 -> U1.5 (Y1), J6.4 -> U1.14 (X1)'],
            ['Sensor 3 (SEL=10)', '', 'LC3_AN / LC3_AP', 'J7.3 -> U1.2 (Y2), J7.4 -> U1.15 (X2)'],
            ['Sensor 4 (SEL=11)', '', 'LC4_AN / LC4_AP', 'J8.3 -> U1.4 (Y3), J8.4 -> U1.11 (X3)'],
        ]
    )

(root / 'ONTWERP.md').write_text(
    '''# SILOAD LOAD CELL REV A (Silo Unit — Load Cell & Temp PCB)

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
''',
    encoding='utf-8',
)
print('PASS: schematic netlist exactly matches PCB pad connections.')
