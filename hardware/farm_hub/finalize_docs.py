from pathlib import Path
import csv, json, xml.etree.ElementTree as ET
import pcbnew as p
root=Path(__file__).resolve().parent
b=p.LoadBoard(str(root/'SILOAD REV A.kicad_pcb'))
tree=ET.parse(root/'connectivity.xml')
schematic={n.attrib['name']:{(v.attrib['ref'],v.attrib['pin']) for v in n.findall('node')} for n in tree.findall('./nets/net')}
desired={}
for name in schematic:
 n=b.FindNet(name)
 if not n or n.GetNetname()!=name:
  n=p.NETINFO_ITEM(b,name);b.Add(n)
 desired[name]=n
for track in b.GetTracks():
 name=track.GetNetname()
 if name and not name.startswith('/') and not name.startswith('unconnected-'):
  track.SetNet(desired['/'+name])
for f in b.GetFootprints():
 for pad in f.Pads():
  node=(f.GetReference(),pad.GetNumber())
  for name,nodes in schematic.items():
   if node in nodes:pad.SetNet(desired[name]);break
b.BuildConnectivity()
p.SaveBoard(str(root/'SILOAD REV A.kicad_pcb'),b)
pcb={}
for f in b.GetFootprints():
 for pad in f.Pads():
  if pad.GetNetname():pcb.setdefault(pad.GetNetname(),set()).add((f.GetReference(),pad.GetNumber()))
assert pcb==schematic,(pcb,schematic)
with (root/'pinout-concept.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.writer(f);w.writerow(['XIAO','GPIO','Net','W5500 module pin'])
 w.writerows([['D0',1,'ETH_CSn','J3.5 CS'],['D6',43,'ETH_RESETn','J4.5 RST'],['D7',44,'ETH_INTn','J3.6 INT'],['D8',7,'SPI_SCK','J3.4 SCLK'],['D9',8,'SPI_MISO','J4.6 MISO'],['D10',9,'SPI_MOSI','J3.3 MOSI'],['3V3','','+3V3','J4.2 + J4.3'],['GND','','GND','J3.1 + J3.2 + J4.1']])
(root/'ONTWERP.md').write_text('''# SILOAD REV A

KiCad 10 ontwerpconcept voor de Farm hub, 59 x 36 mm, 2 koperlagen, 1,6 mm FR4. De breedte is 4 mm groter dan de vorige compacte versie om beide poorten aan dezelfde voorrand te plaatsen en de vier hoekgaten vrij te houden.
Het schema en de PCB zijn aanwezig en de aansluitingen zijn gerouteerd. Dit is een reviewversie: de mechanische passing van de eigen modules is nog niet bevestigd. Er zijn geen Gerbers voor productie gemaakt.

## Opbouw en voeding

- Complete bestaande XIAO ESP32-S3 / Wio-SX1262-stack op J1 en J2, twee female headers van 1x7 pins. De carrier maakt geen nieuwe verbindingen met de LoRa-besturingssignalen.
- ARCELI W5500 AA0003, ASIN B09DYFLMJG, op J3 en J4, twee female headers van 1x6 pins.
- Voeding via USB-C op de XIAO. De XIAO 3V3 voedt de W5500 rechtstreeks, volgens de gekozen opzet. Geen aparte regelaar of voedingsdiode op de carrier.
- Geen ingebouwde PoE. Een eventuele latere PoE-aansluiting vraagt een afzonderlijke uitwerking van het voedingspad.
- C1: 100nF keramisch, steek 2,50 mm. C2: 10uF/16V radiale elco, diameter 5 mm, steek 2,00 mm. Let bij C2 op de plusmarkering.
- Alle zelf te plaatsen componenten zijn through-hole. De kant-en-klare modules bevatten hun eigen SMD-onderdelen.
- C1 en C2 zijn buiten de verwachte module-omtrekken geplaatst, met minimaal 2,0 mm tussen de module-envelop en de condensatorbehuizingen. Tussen de twee modules zit 2,0 mm. De routing gebruikt horizontale, verticale en 45-graden segmenten.
- Vier bevestigingsgaten van 2,7 mm voor M2.5, elk 3,5 mm vanaf de twee aangrenzende randen. Het gatenpatroon is 52 x 29 mm. Er is gecontroleerd op vrije ruimte voor schroefkoppen met een diameter van 5 mm; grotere koppen of ringen moeten apart worden gecontroleerd.
- USB-C en RJ45 zijn naar dezelfde voorrand verplaatst. De referentie-frontvlakken van de connectoren liggen 2,5 mm buiten de carrier-rand. De module-PCB's steken ongeveer 1 mm uit; de voorwand moet die printneuzen vrijhouden. Definitieve wanddikte en paneeluitsparingen volgen na controle van de echte modules en gebruikte kabelstekkers. Een rechte wand van 2 mm vanaf 1,3 mm voor de carrier-rand zou de connectorfronten ongeveer 0,8 mm verdiepen; reserveer dan ook ruimte voor de stekkerbehuizing in de openingen. Een inwendige wanduitsparing is een alternatief.
- De USB-positie volgt de officiële XIAO-CAD. Voor de RJ45 is nog een vergelijkbaar Amphenol-model gebruikt; de exacte ARCELI/HanRun-maat en het 20,32 mm headerpatroon moeten fysiek worden gecontroleerd. De pinnen van beide modules staan in de visualisatie op de echte carrier-headercoördinaten.
- LoRa U.FL-naar-SMA via een coaxpigtail naar de behuizing; geen RF-baan of SMA-connector op deze carrier.
- Het aangeleverde SiLoad-logo staat als vectorfootprint LOGO1 op F.Silkscreen, 20,0 x 3,918 mm, onder de Ethernet-module. REV A staat eronder. De herbruikbare footprint staat in SILOAD.pretty; het originele beeld en de SVG staan in branding.

## Ethernet-aansluitingen

| XIAO | GPIO | W5500 |
| --- | --- | --- |
| D0 | 1 | CSn |
| D6 | 43 | RESETn |
| D7 | 44 | INTn |
| D8 | 7 | SCLK |
| D9 | 8 | MISO |
| D10 | 9 | MOSI |
| 3V3 | | Beide 3V3-pinnen |
| GND | | Alle drie GND-pinnen |

Pin 1 van J1/J2 zit aan de USB-C-zijde. Pin 1 van J3/J4 zit aan de RJ45-zijde, bovenaanzicht op de module. J4 pin 4 (NC) blijft open. XIAO D1-D5 en de 5V-pin worden niet op de carrier aangesloten; bestaande verbindingen binnen de stack blijven daarvan onafhankelijk.

## Nog controleren voor fabricage

De XIAO-headerafstand is 15,24 mm, met 2,54 mm pinsteek. De ARCELI-rijafstand is voorlopig op 20,32 mm gezet; dit is een ontwerpaanname, geen maatbevestiging van de verkoper. Controleer die afstand, de pinvolgorde en de module-omtrek op het eigen printje voordat er besteld wordt. Controleer ook dat de onderzijde van de complete XIAO/Wio-stack op de gekozen headerhoogte vrij blijft, en dat USB-C en RJ45 met hun stekkers bereikbaar zijn. De gekozen voeding is niet met echte hardware belast getest.

De 3D-render gebruikt vereenvoudigde, zelfgemaakte envelopmodellen voor beide modules. Het is een visuele indruk, geen maatvaste fabrikant-CAD. De componentmodellen voor sockets en condensatoren komen uit KiCad. `SILOAD REV A-assembly.step` bevat de samengestelde print met sockets, condensatoren en vereenvoudigde modules. `SILOAD REV A-carrier.step` bevat alleen de carrier-PCB. `SILOAD REV A-assembly.wrl` is de gekleurde 3D-uitvoering. De STEP-bestanden gebruiken millimeters en een oorsprong bij de hoek van de carrier.

## Bestanden en controle

Open `SILOAD REV A.kicad_pro` in KiCad. `SILOAD REV A-schema.pdf` bevat het schema; `SILOAD REV A-layout.svg` toont de koperbanen. De nieuwste renders heten `SILOAD REV A-compact-render.png`, `SILOAD REV A-compact-top.png` en `SILOAD REV A-compact-routing.png`. `BOM.csv` bevat de onderdelen, `pinout-concept.csv` de carrierverbindingen. `erc.rpt` en `drc.json` bevatten de KiCad-controles. Een aanvullende vergelijking tussen de geëxporteerde schemanetlijst en alle PCB-pads is geslaagd. `layout-validation.json` bevat de controle van de tracehoeken, de vier gaten en de ruimte tussen de aangenomen module-omtrekken, condensatorbehuizingen en schroefkoppen. KiCad DRC controleert de koperafstanden; deze extra controle behandelt de grotere module-omtrekken die niet in de socket-footprints zitten.

Opnieuw opbouwen: voer `build_design.py`, `route_board.py` en `add_preview_models.py` uit met de Python uit KiCad. Dit vervangt de gegenereerde bestanden. Exporteer daarna de netlijst en draai `finalize_docs.py`. Voer KiCad ERC/DRC en `validate_layout.py` opnieuw uit. Maak STEP-modellen voor de modules met `make_step_models.py`, systeem-Python en de lokale dependency `cadquery-ocp-novtk`; exporteer de assembly met `kicad-cli pcb export step --subst-models`.

## Bronnen

- Opgegeven product: https://www.amazon.nl/dp/B09DYFLMJG
- Foto met pinlabels bij hetzelfde ASIN: https://www.odkarla.cz/arceli-w5500-spi-na-lan-ethernet-sitovy-modul-tcp-ip-stm32-rozhrani-33v-5v-pro-arduino-wiz820io-r~p1604160
- Voorbeeld met hetzelfde ASIN en aansluitingen: https://maker.wiznet.io/praveen_k/projects/Arduino-Nano-web-server-with-w5500/
- XIAO voeding en pinout: https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/
- Wio-stack-uitvoeringen: https://wiki.seeedstudio.com/wio_sx1262_with_xiao_esp32s3_kit/

Bijgewerkt: 2026-10-27.
''',encoding='utf-8')
print('PASS: schematic netlist exactly matches PCB pad connections.')
