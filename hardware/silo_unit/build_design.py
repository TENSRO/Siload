"""Generate the compact 68x44mm Silo Unit PCB (horizontal Heemol 34x21mm HX711 + horizontal CD4052 + 4x Load Cell + DS18B20)."""
from pathlib import Path
import uuid, json, csv
import pcbnew as p
from layout_config import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    MOUNTING_HOLES,
    REFERENCE_POSITIONS,
    XIAO_HEADERS,
    HX_CENTER,
    HX_MCU_POS,
    HX_BRIDGE_POS,
    MUX_POS,
    SENS_POSITIONS,
    TEMP_POS,
    LOGO_CENTER,
)

ROOT = Path(__file__).resolve().parent
NAME = 'SILOAD LOAD CELL REV A'
LIB = Path(r'C:\Program Files\KiCad\10.0\share\kicad\footprints')
uid = lambda: str(uuid.uuid4())
sheet = uid()

# (ref, value, libname, fpname, x, y, rot_deg, count, connections, pinnames, schem_xy)
spec = [
    (
        'J1',
        'XIAO_LEFT',
        'Connector_PinSocket_2.54mm',
        'PinSocket_1x07_P2.54mm_Vertical',
        XIAO_HEADERS[0],
        XIAO_HEADERS[1],
        0,
        7,
        ['HX_DT', None, None, None, None, None, 'HX_SCK'],
        ['D0_GPIO1', 'D1_GPIO2', 'D2_GPIO3', 'D3_GPIO4', 'D4_GPIO5', 'D5_GPIO6', 'D6_GPIO43'],
        (38.10, 30.48),
    ),
    (
        'J2',
        'XIAO_RIGHT',
        'Connector_PinSocket_2.54mm',
        'PinSocket_1x07_P2.54mm_Vertical',
        XIAO_HEADERS[0] + 15.24,
        XIAO_HEADERS[1],
        0,
        7,
        [None, 'GND', '+3V3', 'MUX_B', None, 'MUX_A', 'ONEWIRE_DQ'],
        ['5V_USB', 'GND', '3V3', 'D10_GPIO9', 'D9_GPIO8', 'D8_GPIO7', 'D7_GPIO44'],
        (91.44, 30.48),
    ),
    (
        'J3',
        'HX711_MCU',
        'Connector_PinSocket_2.54mm',
        'PinSocket_1x04_P2.54mm_Vertical',
        HX_MCU_POS[0],
        HX_MCU_POS[1],
        0,
        4,
        ['+3V3', 'HX_SCK', 'HX_DT', 'GND'],
        ['VCC', 'SCK', 'DT', 'GND'],
        (144.78, 30.48),
    ),
    (
        'J4',
        'HX711_BRIDGE',
        'Connector_PinSocket_2.54mm',
        'PinSocket_1x06_P2.54mm_Vertical',
        HX_BRIDGE_POS[0],
        HX_BRIDGE_POS[1],
        0,
        6,
        [None, None, 'HX_AP', 'HX_AN', 'LC_EN', 'LC_EP'],
        ['B+', 'B-', 'A+', 'A-', 'E-', 'E+'],
        (144.78, 58.42),
    ),
    (
        'U1',
        'CD4052BE_MUX',
        'Package_DIP',
        'DIP-16_W7.62mm_Socket',
        MUX_POS[0],
        MUX_POS[1],
        90,
        16,
        [
            'LC1_AN',
            'LC3_AN',
            'HX_AN',
            'LC4_AN',
            'LC2_AN',
            'GND',
            'GND',
            'GND',
            'MUX_B',
            'MUX_A',
            'LC4_AP',
            'LC1_AP',
            'HX_AP',
            'LC2_AP',
            'LC3_AP',
            '+3V3',
        ],
        [
            'Y0_S1_A-',
            'Y2_S3_A-',
            'Y_COM_A-',
            'Y3_S4_A-',
            'Y1_S2_A-',
            'INH',
            'VEE',
            'VSS',
            'SEL_B',
            'SEL_A',
            'X3_S4_A+',
            'X0_S1_A+',
            'X_COM_A+',
            'X1_S2_A+',
            'X2_S3_A+',
            'VDD',
        ],
        (198.12, 30.48),
    ),
]

for idx, (ref, tx, ty, rot) in enumerate(SENS_POSITIONS, start=1):
    col_x = 38.10 + (idx - 1) * 53.34
    spec.append(
        (
            ref,
            f'SENS{idx}_LOADCELL',
            'Connector_PinSocket_2.54mm',
            'PinSocket_1x04_P2.54mm_Vertical',
            tx,
            ty,
            rot,
            4,
            ['LC_EP', 'LC_EN', f'LC{idx}_AN', f'LC{idx}_AP'],
            ['E+_RED', 'E-_BLK', 'A-_WHT', 'A+_GRN'],
            (col_x, 121.92),
        )
    )

spec.extend(
    [
        (
            'J9',
            'TEMP_DS18B20',
            'Connector_PinSocket_2.54mm',
            'PinSocket_1x03_P2.54mm_Vertical',
            TEMP_POS[0],
            TEMP_POS[1],
            TEMP_POS[2],
            3,
            ['+3V3', 'ONEWIRE_DQ', 'GND'],
            ['VDD_3V3', 'DQ_D7', 'GND'],
            (251.46, 30.48),
        ),
        (
            'R1',
            '4.7k_1Wire_pullup',
            'Resistor_THT',
            'R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',
            58.5,
            83.5,
            0,
            2,
            ['+3V3', 'ONEWIRE_DQ'],
            ['1', '2'],
            (251.46, 58.42),
        ),
        (
            'C1',
            '100nF_50V_ceramic_THT',
            'Capacitor_THT',
            'C_Disc_D5.0mm_W2.5mm_P2.50mm',
            58.5,
            76.5,
            0,
            2,
            ['+3V3', 'GND'],
            ['1', '2'],
            (251.46, 83.82),
        ),
        (
            'C2',
            '10uF_16V_electrolytic_THT',
            'Capacitor_THT',
            'CP_Radial_D5.0mm_P2.00mm',
            70.5,
            77.5,
            0,
            2,
            ['+3V3', 'GND'],
            ['+', '-'],
            (251.46, 109.22),
        ),
    ]
)

board = p.BOARD()
board.SetCopperLayerCount(2)
board.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
nets = {}
for name in sorted({n for s in spec for n in s[8] if n}):
    n = p.NETINFO_ITEM(board, name)
    board.Add(n)
    nets[name] = n


def pos(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def line(x1, y1, x2, y2, layer=p.Edge_Cuts, width=0.05):
    s = p.PCB_SHAPE()
    s.SetShape(p.SHAPE_T_SEGMENT)
    s.SetStart(pos(x1, y1))
    s.SetEnd(pos(x2, y2))
    s.SetLayer(layer)
    s.SetWidth(p.FromMM(width))
    board.Add(s)


def text(t, x, y, size=0.85, layer=p.F_SilkS):
    a = p.PCB_TEXT(board)
    a.SetText(t)
    a.SetPosition(pos(x, y))
    a.SetTextSize(pos(size, size))
    a.SetTextThickness(p.FromMM(0.15))
    a.SetLayer(layer)
    board.Add(a)


x1 = 50 + BOARD_WIDTH
y1 = 50 + BOARD_HEIGHT
for a, b, c, d in [(50, 50, x1, 50), (x1, 50, x1, y1), (x1, y1, 50, y1), (50, y1, 50, 50)]:
    line(a, b, c, d)

text('SILO UNIT - REV A', 65.72, 60.0, 0.85)
text('USB-C', 65.62, 50.9, 0.8)
text('HX711 (34x21)', HX_CENTER[0], 53.0, 0.8)
text('VCC', HX_MCU_POS[0] + 3.2, HX_MCU_POS[1], 0.8)
text('GND', HX_MCU_POS[0] + 3.2, HX_MCU_POS[1] + 7.62, 0.8)
text('B+', HX_BRIDGE_POS[0] - 3.0, HX_BRIDGE_POS[1], 0.8)
text('E+', HX_BRIDGE_POS[0] - 3.0, HX_BRIDGE_POS[1] + 12.70, 0.8)
text('CD4052 MUX', 88.9, 78.8, 0.8)
text('S1', 76.8, 86.6, 0.8)
text('S2', 89.3, 86.6, 0.8)
text('S3', 101.8, 86.6, 0.8)
text('S4', 113.5, 80.3, 0.8)
text('TMP', 62.5, 86.6, 0.8)

# Documentation-layer module envelopes: XIAO/Wio stack + horizontal Heemol HX711 module (34x21 mm)
hx_x0, hx_y0 = HX_CENTER[0] - 17.0, HX_CENTER[1] - 10.5
hx_x1, hx_y1 = HX_CENTER[0] + 17.0, HX_CENTER[1] + 10.5
for x0, y0, ex1, ey1 in [(56.72, 49.027, 74.52, 70.467), (hx_x0, hx_y0, hx_x1, hx_y1)]:
    for a, b, c, d in [(x0, y0, ex1, y0), (ex1, y0, ex1, ey1), (ex1, ey1, x0, ey1), (x0, ey1, x0, y0)]:
        line(a, b, c, d, p.Dwgs_User, 0.1)

defs = []
instances = []
wires = []
labels = []
ncs = []
footprints = {}
ids = {}

for ref, value, libname, fpname, x, y, rot_deg, count, connections, pinnames, (sx, sy) in spec:
    identifier = uid()
    ids[ref] = identifier
    fp = p.FootprintLoad(str(LIB / (libname + '.pretty')), fpname)
    fp.SetFPIDAsString(libname + ':' + fpname)
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(pos(x, y))
    if rot_deg:
        fp.SetOrientationDegrees(rot_deg)
    fp.SetPath(p.KIID_PATH('/' + sheet + '/' + identifier))
    for pad in fp.Pads():
        net = connections[int(pad.GetNumber()) - 1]
        if net:
            pad.SetNet(nets[net])
    fp.Reference().SetTextSize(pos(0.8, 0.8))
    fp.Reference().SetTextThickness(p.FromMM(0.12))
    fp.Value().SetVisible(False)
    board.Add(fp)
    footprints[ref] = fp

    symbol_name = f'{ref}_part'
    pins = []
    for k, pinname in enumerate(pinnames):
        py = -k * 2.54
        pins.append(
            f'(pin passive line (at -10.16 {py} 0) (length 5.08) (name "{pinname}" (effects (font (size 1 1)))) (number "{k+1}" (effects (font (size 1 1)))))'
        )
    defs.append(
        f'''(symbol "SILOAD:{symbol_name}"
 (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
 (property "Reference" "{ref[0]}" (at 0 3.81 0) (effects (font (size 1.27 1.27))))
 (property "Value" "{value}" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
 (symbol "{symbol_name}_0_1" (rectangle (start -5.08 1.27) (end 15.24 {-count*2.54+1.27}) (stroke (width .254) (type default)) (fill (type background))))
 (symbol "{symbol_name}_1_1" {''.join(pins)}))'''
    )
    instances.append(
        f'''(symbol (lib_id "SILOAD:{symbol_name}") (at {sx} {sy} 0) (unit 1)
 (in_bom yes) (on_board yes) (dnp no) (uuid "{identifier}")
 (property "Reference" "{ref}" (at {sx} {sy-4.5} 0) (effects (font (size 1.1 1.1))))
 (property "Value" "{value}" (at {sx} {sy-2.2} 0) (effects (font (size 1.0 1.0))))
 (property "Footprint" "{libname}:{fpname}" (at {sx} {sy} 0) (effects (font (size 1 1)) hide))
 {''.join(f'(pin "{k+1}" (uuid "{uid()}"))' for k in range(count))}
 (instances (project "{NAME}" (path "/{sheet}" (reference "{ref}") (unit 1)))))'''
    )
    for k, net in enumerate(connections):
        px = round(sx - 10.16, 4)
        py = round(sy + k * 2.54, 4)
        lx = round(px - 6.35, 4)
        if net:
            wires.append(
                f'(wire (pts (xy {lx} {py}) (xy {px} {py})) (stroke (width 0) (type default)) (uuid "{uid()}"))'
            )
            labels.append(
                f'(label "{net}" (at {lx} {py} 0) (effects (font (size 0.9 0.9)) (justify left bottom)) (uuid "{uid()}"))'
            )
        else:
            ncs.append(f'(no_connect (at {px} {py}) (uuid "{uid()}"))')

for ref, x, y in MOUNTING_HOLES:
    fp = p.FootprintLoad(str(LIB / 'MountingHole.pretty'), 'MountingHole_2.7mm_M2.5')
    fp.SetReference(ref)
    fp.SetValue('M2.5')
    fp.SetPosition(pos(x, y))
    fp.Reference().SetTextSize(pos(0.8, 0.8))
    fp.Reference().SetTextThickness(p.FromMM(0.12))
    fp.Value().SetVisible(False)
    for item in list(fp.GraphicalItems()):
        if item.GetLayer() == p.F_CrtYd:
            fp.Remove(item)
    board.Add(fp)
    fp.SetAttributes(fp.GetAttributes() | p.FP_BOARD_ONLY)

notes = [
    ('Compact Silo unit (Load Cell PCB, 68x44 mm): Seeed XIAO ESP32-S3 + stacked Wio-SX1262 on J1/J2.', 25, 160),
    ('Horizontal Heemol HX711 module (34x21 mm, 4-pin J3 + 6-pin J4) at top-right; horizontal CD4052BE DIP-16 mux (U1) directly below it.', 25, 165),
    ('DS18B20 temperature sensor connects to J9 (3V3, DQ=D7, GND) with R1 = 4.7k pull-up to +3V3.', 25, 170),
]
note_text = ''.join(
    f'(text "{t}" (at {x} {y} 0) (effects (font (size 1.1 1.1)) (justify left bottom)) (uuid "{uid()}"))'
    for t, x, y in notes
)
sch = f'''(kicad_sch (version 20250114) (generator "eeschema") (uuid "{sheet}") (paper "A4")
 (title_block (title "SILOAD LOAD CELL REV A - Silo unit carrier (68x44 mm)") (date "2026-10-27") (rev "A PROTOTYPE") (comment 1 "4x Load Cell Sensors + CD4052 Mux + Heemol HX711 (34x21mm) + DS18B20"))
 (lib_symbols {''.join(defs)})
 {''.join(wires)} {''.join(labels)} {''.join(ncs)} {note_text} {''.join(instances)}
 (sheet_instances (path "/" (page "1"))))'''

(ROOT / (NAME + '.kicad_sch')).write_text(sch, encoding='utf-8')
(ROOT / 'SILOAD.kicad_sym').write_text(
    '(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") '
    + ''.join(d.replace('"SILOAD:', '"') for d in defs)
    + ')',
    encoding='utf-8',
)
(ROOT / 'sym-lib-table').write_text(
    '(sym_lib_table (version 7) (lib (name "SILOAD") (type "KiCad") (uri "${KIPRJMOD}/SILOAD.kicad_sym") (options "") (descr "SILOAD carrier symbols")))',
    encoding='utf-8',
)
(ROOT / 'fp-lib-table').write_text(
    '(fp_lib_table (version 7) (lib (name "SILOAD") (type "KiCad") (uri "${KIPRJMOD}/SILOAD.pretty") (options "") (descr "SiLoad branding")))',
    encoding='utf-8',
)

for fp in board.GetFootprints():
    if fp.GetReference() in REFERENCE_POSITIONS:
        fp.Reference().SetPosition(pos(*REFERENCE_POSITIONS[fp.GetReference()]))

if (ROOT / 'branding' / 'SiLoad-logo.json').exists():
    from apply_logo import apply

    apply(board)

p.SaveBoard(str(ROOT / (NAME + '.kicad_pcb')), board)
(ROOT / (NAME + '.kicad_pro')).write_text(
    json.dumps(
        {
            'meta': {'filename': NAME + '.kicad_pro', 'version': 1},
            'board': {
                'design_settings': {
                    'rules': {
                        'min_clearance': 0.2,
                        'min_track_width': 0.2,
                        'min_hole_clearance': 0.25,
                        'min_copper_edge_clearance': 0.3,
                    }
                }
            },
        },
        indent=2,
    ),
    encoding='utf-8',
)

with (ROOT / 'BOM.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Reference', 'Quantity', 'Description', 'Footprint'])
    w.writerow(['J1,J2', 2, 'Female header 1x7 2.54mm for XIAO ESP32-S3 + Wio-SX1262 stack', 'PinSocket_1x07_P2.54mm_Vertical'])
    w.writerow(['J3', 1, 'Female header 1x4 2.54mm for Heemol HX711 MCU side (VCC, SCK, DT, GND)', 'PinSocket_1x04_P2.54mm_Vertical'])
    w.writerow(['J4', 1, 'Female header 1x6 2.54mm for Heemol HX711 Bridge side (B+, B-, A+, A-, E-, E+)', 'PinSocket_1x06_P2.54mm_Vertical'])
    w.writerow(['U1', 1, 'CD4052BE or 74HC4052N dual 4-channel analog multiplexer (DIP-16) + 16-pin DIP socket', 'DIP-16_W7.62mm_Socket'])
    w.writerow(['J5..J8', 4, '4-pin 2.54mm header/socket for 4 load-cell sensors (E+, E-, A-, A+)', 'PinSocket_1x04_P2.54mm_Vertical'])
    w.writerow(['J9', 1, '3-pin 2.54mm header/socket for DS18B20 temperature sensor (3V3, DQ, GND)', 'PinSocket_1x03_P2.54mm_Vertical'])
    w.writerow(['R1', 1, '4.7k Ohm axial through-hole resistor (1-Wire pull-up to 3V3)', 'R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal'])
    w.writerow(['C1', 1, '100nF 50V ceramic through-hole decoupling capacitor', 'C_Disc_D5.0mm_W2.5mm_P2.50mm'])
    w.writerow(['C2', 1, '10uF 16V radial electrolytic bulk decoupling capacitor on 3V3', 'CP_Radial_D5.0mm_P2.00mm'])
    w.writerow(['H1..H4', 4, 'M2.5 mounting holes (2.7mm drill, screw head <=5mm)', 'MountingHole_2.7mm_M2.5'])

print('Created compact 68x44mm schematic, project, PCB placement draft and BOM in', ROOT)
