"""Shared geometry configuration for SILOAD LOAD CELL REV A (compact 68x44 mm for Heemol 34x21mm HX711 + CD4052)."""

BOARD_WIDTH = 68
BOARD_HEIGHT = 44
SCREW_HEAD_DIAMETER = 5.0

# 4x M2.5 mounting holes inset 3.5 mm from all board corners
MOUNTING_HOLES = [
    ('H1', 53.5, 53.5),
    ('H2', 114.5, 53.5),
    ('H3', 53.5, 90.5),
    ('H4', 114.5, 90.5),
]

# Top-left: Seeed XIAO ESP32-S3 + Wio-SX1262 stack (USB-C at top edge y=50)
XIAO_HEADERS = (58.1, 51.948)

# Top-right: Horizontal Heemol HX711 module (34.0 x 21.0 mm, B0C9QBS2WL)
# Center of module is at (93.8, 62.0) -> body spans x=76.8..110.8, y=51.5..72.5
# Left header J3 (4-pin MCU side: VCC, SCK, DT, GND) at x = 93.8 - 12.7 = 81.10, y1 = 62.0 - 3.81 = 58.19
# Right header J4 (6-pin Bridge side: B+, B-, A+, A-, E-, E+) at x = 93.8 + 12.7 = 106.50, y1 = 62.0 - 6.35 = 55.65
HX_CENTER = (93.8, 62.0)
HX_MCU_POS = (81.10, 58.19)
HX_BRIDGE_POS = (106.50, 55.65)

# Middle-right (directly below HX711): Horizontal CD4052BE DIP-16 multiplexer
# Rotated 90 deg: Pin 1..8 along bottom row (y=82.62, x=80.0..97.78), Pin 16..9 along top row (y=75.00, x=80.0..97.78)
MUX_POS = (80.0, 82.62)

# 4x Load Cell 4-pin headers (SENS1..3 horizontal along bottom edge, SENS4 vertical at right)
SENS_POSITIONS = [
    ('J5', 73.0, 89.2, 90),
    ('J6', 85.5, 89.2, 90),
    ('J7', 98.0, 89.2, 90),
    ('J8', 109.5, 76.5, 0),
]

# Bottom-left: 1x DS18B20 temperature sensor 3-pin header (horizontal)
TEMP_POS = (60.0, 89.2, 90)

# SiLoad logo center on front silkscreen (centered in the 25.4 mm span between J3 and J4)
LOGO_CENTER = (93.8, 63.0)

REFERENCE_POSITIONS = {
    'J1': (58.1, 71.7),
    'J2': (73.3, 71.7),
    'J3': (78.6, 58.2),
    'J4': (109.0, 55.7),
    'U1': (76.8, 78.8),
    'J5': (70.5, 89.2),
    'J6': (83.0, 89.2),
    'J7': (95.5, 89.2),
    'J8': (109.5, 74.0),
    'J9': (57.5, 89.2),
    'R1': (62.3, 81.2),
    'C1': (59.8, 74.2),
    'C2': (70.5, 73.8),
    'H1': (53.5, 57.2),
    'H2': (114.5, 57.2),
    'H3': (53.5, 86.8),
    'H4': (114.5, 86.8),
}
