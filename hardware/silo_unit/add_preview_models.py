"""Indicative module envelopes for 3D preview (XIAO/Wio stack + horizontal Heemol 34x21mm HX711 module)."""
from pathlib import Path
import json
import pcbnew as p

ROOT = Path(__file__).resolve().parent
(ROOT / 'models').mkdir(exist_ok=True)
boxes = []


def box(x, y, z, dx, dy, dz, color):
    boxes.append(dict(center=[x, y, z], size=[dx, dy, dz], color=[float(v) for v in color.split()]))
    return (
        f'Transform {{ translation {x/2.54} {y/2.54} {z/2.54} children [ '
        f'Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} }} }} '
        f'geometry Box {{ size {dx/2.54} {dy/2.54} {dz/2.54} }} }} ] }}\n'
    )


green = '.009 .012 .016'
hx_green = '.018 .22 .09'
black = '.055 .055 .065'
metal = '.7 .72 .75'
gold = '.8 .58 .12'

stack = '#VRML V2.0 utf8\n'
stack += box(7.62, -7.5565, 9.125, 17.8, 20.955, 1.25, green)
stack += box(7.62, -8, 10.4, 12, 10, 2.7, metal)
stack += box(7.62, 1.198, 10.86, 8.94, 6.5, 4.2, metal)
stack += box(7.62, 4.448, 10.86, 6.8, 0.15, 2.5, black)
stack += box(7.62, -7.799, 16.2, 17.8, 21.44, 1.6, green)
stack += box(7.62, -12.402, 18.225, 11, 11.6, 2.15, metal)
stack += box(13, -16, 18.2, 2.5, 2.5, 1.8, gold)
stack_boxes = boxes
boxes = []

# J3 is unrotated (deg=0) at (81.10, 58.19); J4 (6-pin) is at (106.50, 55.65).
# Center of horizontal Heemol HX711 (34.0 x 21.0 mm) relative to J3 pad 1 is dx = +12.7 mm, dy = -3.81 mm.
hx = '#VRML V2.0 utf8\n'
hx += box(12.7, -3.81, 9.3, 34.0, 21.0, 1.6, hx_green)
hx += box(12.7, -3.81, 10.8, 4.0, 9.9, 1.5, black)
hx += box(17.5, -0.5, 10.6, 3.0, 2.5, 1.2, black)
hx_boxes = boxes

(ROOT / 'models' / 'xiao-wio-indicative.wrl').write_text(stack)
(ROOT / 'models' / 'hx711-indicative.wrl').write_text(hx)
(ROOT / 'models' / 'module-geometry.json').write_text(
    json.dumps({'xiao-wio-indicative': stack_boxes, 'hx711-indicative': hx_boxes}, indent=2)
)

board = p.LoadBoard(str(ROOT / 'SILOAD LOAD CELL REV A.kicad_pcb'))
for fp in board.GetFootprints():
    ref = fp.GetReference()
    if ref in ['J1', 'J3']:
        while len(fp.Models()) > 1:
            fp.Models().pop()
        model = p.FP_3DMODEL()
        fn = 'xiao-wio-indicative.wrl' if ref == 'J1' else 'hx711-indicative.wrl'
        model.m_Filename = '${KIPRJMOD}/models/' + fn
        model.m_Scale.x = model.m_Scale.y = model.m_Scale.z = 1
        fp.Models().append(model)
p.SaveBoard(str(ROOT / 'SILOAD LOAD CELL REV A.kicad_pcb'), board)
print('Added indicative module geometry for XIAO/Wio stack and horizontal 34x21mm Heemol HX711 module.')
