# SILOAD REV A — gedetailleerd model en studiorenders

De Blender-scène bevat de compacte carrier van 55 x 36 mm met vier M2.5-gaten, de door KiCad geleverde modellen van sockets en condensatoren, en officiële Seeed STEP-geometrie voor de XIAO ESP32-S3 en Wio-SX1262. Alle PCB's hebben zwart soldeermasker als gekozen presentatie-afwerking; dat is een visuele aanpassing van de bronmodellen. Tussen de XIAO en Wio zijn twee zwarte 1x7 headerstrips met zichtbare goudkleurige pinnen toegevoegd en op de gaten uit de Seeed-CAD uitgelijnd. De ARCELI W5500-module is gereconstrueerd op basis van de productfoto: de W5500-chip en RJ45-connector gebruiken gedetailleerde KiCad-geometrie. Het RJ45-model is een vergelijkbare Amphenol-uitvoering, geen exact HanRun-fabrikantmodel. Kleine componenten, printopdruk, materialen en montagehardware zijn toegevoegd voor de presentatie.

Dit is een productvisualisatie. De ARCELI-headerafstand, de precieze modulevariant, de stackhoogte en de toegevoegde hardware zijn niet fysiek gevalideerd. Gebruik de render niet als bewijs dat alle componenten mechanisch passen. Het elektrische KiCad-ontwerp is door deze visualisatie niet aangepast.

`SILOAD REV A-studio.blend` is de bewerkbare scène met camera's, belichting en componenten. `SILOAD REV A-detailed.glb` is het draagbare 3D-model. De losse PNG's tonen de verschillende camerahoeken. De montagehardware kan in Blender afzonderlijk verborgen worden.

De nieuwste versies met het aangeleverde SiLoad-logo zijn `SILOAD REV A-studio-branded.blend`, `SILOAD REV A-detailed-branded.glb`, `SILOAD REV A-hero-logo.png` en `SILOAD REV A-top-logo.png`. Hetzelfde logo staat als vectorfootprint `LOGO1` op F.Silkscreen van de echte carrier-PCB, 20,0 x 3,918 mm, met REV A eronder. De overige camerahoeken blijven beschikbaar als aanvullende detailbeelden.

- `SILOAD REV A-01-hero.png`: overzicht op 1800 x 1350 pixels.
- `SILOAD REV A-02-connectors.png`: RJ45 en USB-C, 1600 x 1200 pixels.
- `SILOAD REV A-03-detail.png`: detail van radio, headerpinnen en Ethernet-controller, 1600 x 1200 pixels.
- `SILOAD REV A-04-top.png`: bovenaanzicht, 1600 x 1200 pixels.

De scène gebruikt een naadloze lichte studio-achtergrond en vier grote lichtbronnen. De camera's staan ook in het Blender-bestand, zodat nieuwe hoeken en uitsneden gemaakt kunnen worden. Modelgeometrie en gebruikt lettertype zijn in het Blender-bestand opgenomen. Het GLB-bestand bevat de componenten en montagehardware, zonder studiovloer of lampen. De herbruikbare meshbestanden en het render-script zijn in het ZIP-pakket opgenomen; voor opnieuw renderen is Blender 4.5 nodig.

## Bronnen en herkomst

- XIAO ESP32-S3 STEP, Seeed Studio: https://files.seeedstudio.com/wiki/SeeedStudio-XIAO-ESP32S3/res/seeed-studio-xiao-esp32s3-3d_model.zip
- Wio-SX1262 STEP, Seeed Studio: https://files.seeedstudio.com/products/SenseCAP/Wio_SX1262/Wio-SX1262_for_XIAO_3D_file.step
- Documentatie bij de Seeed-modellen: https://wiki.seeedstudio.com/wio_sx1262_with_xiao_esp32s3_kit/ en https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/
- KiCad 3D-modelbibliotheek: https://gitlab.com/kicad/libraries/kicad-packages3D — KiCad Library License, CC BY-SA 4.0 met bibliotheekuitzondering; zie de bibliotheek voor de volledige voorwaarden.
- ARCELI-module: https://www.amazon.nl/dp/B09DYFLMJG
- Foto van hetzelfde ARCELI-artikelnummer: https://www.odkarla.cz/arceli-w5500-spi-na-lan-ethernet-sitovy-modul-tcp-ip-stm32-rozhrani-33v-5v-pro-arduino-wiz820io-r~p1604160

De bewerkte visualisatie en het Blender-script zijn lokaal voor dit project gemaakt. Bron-CAD blijft afkomstig van de genoemde makers.
