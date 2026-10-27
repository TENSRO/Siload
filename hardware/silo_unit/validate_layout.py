from pathlib import Path
import json, math
import pcbnew as p
from layout_config import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    MOUNTING_HOLES,
    SCREW_HEAD_DIAMETER,
    HX_CENTER,
    MUX_POS,
    SENS_POSITIONS,
    TEMP_POS,
)

PORT_FRONT_Y = 2.5
ROOT = Path(__file__).resolve().parent
b = p.LoadBoard(str(ROOT / 'SILOAD LOAD CELL REV A.kicad_pcb'))
fps = {f.GetReference(): f for f in b.GetFootprints()}


def xy(ref):
    point = fps[ref].GetPosition()
    return p.ToMM(point.x), p.ToMM(point.y)


x, y = xy('J1')
envelopes = {
    'XIAO/Wio': (x - 1.28, y - 2.921, x + 16.52, y + 18.519),
    'HX711_34x21': (HX_CENTER[0] - 17.0, HX_CENTER[1] - 10.5, HX_CENTER[0] + 17.0, HX_CENTER[1] + 10.5),
    'U1': (MUX_POS[0] - 1.5, MUX_POS[1] - 8.0, MUX_POS[0] + 19.28, MUX_POS[1] + 1.88),
}
port_fronts = {'USB-C': 50 - y + 4.448}
assert all(abs(front - PORT_FRONT_Y) < 0.01 for front in port_fronts.values()), port_fronts

c1x, c1y = xy('C1')
envelopes['C1'] = (c1x - 1.25, c1y - 1.25, c1x + 3.75, c1y + 1.25)
c2x, c2y = xy('C2')
envelopes['C2'] = (c2x - 1.5, c2y - 2.5, c2x + 3.5, c2y + 2.5)
rx, ry = xy('R1')
envelopes['R1'] = (rx - 1.25, ry - 1.25, rx + 8.87, ry + 1.25)

for ref, tx, ty, rot in SENS_POSITIONS:
    if rot == 90:
        envelopes[ref] = (tx - 1.27, ty - 1.27, tx + 8.89, ty + 1.27)
    else:
        envelopes[ref] = (tx - 1.27, ty - 1.27, tx + 1.27, ty + 8.89)

tx, ty, _ = TEMP_POS
envelopes['J9'] = (tx - 1.27, ty - 1.27, tx + 6.35, ty + 1.27)

clearances = {}
names = list(envelopes.keys())
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        n1, n2 = names[i], names[j]
        a, c = envelopes[n1], envelopes[n2]
        dx = max(c[0] - a[2], a[0] - c[2], 0)
        dy = max(c[1] - a[3], a[1] - c[3], 0)
        gap = math.hypot(dx, dy)
        assert gap >= 2.0 - 1e-8, (n1, n2, gap)
        clearances[f'{n1} to {n2}'] = round(gap, 3)

angles = {'horizontal': 0, 'vertical': 0, 'diagonal45': 0}
for t in b.GetTracks():
    if isinstance(t, p.PCB_VIA):
        continue
    a = t.GetStart()
    c = t.GetEnd()
    dx = abs(a.x - c.x)
    dy = abs(a.y - c.y)
    assert dx == 0 or dy == 0 or abs(dx - dy) <= 2, ('Non-45-degree track', a, c)
    angles['vertical' if dx == 0 else 'horizontal' if dy == 0 else 'diagonal45'] += 1
assert angles['diagonal45'] > 0

mounting_clearances = {}
mounting_copper_clearances = {}
for ref, x, y in MOUNTING_HOLES:
    assert xy(ref) == (x, y)
    assert 50 + SCREW_HEAD_DIAMETER / 2 < x < 50 + BOARD_WIDTH - SCREW_HEAD_DIAMETER / 2
    assert 50 + SCREW_HEAD_DIAMETER / 2 < y < 50 + BOARD_HEIGHT - SCREW_HEAD_DIAMETER / 2
    for name, a in envelopes.items():
        dx = max(a[0] - x, x - a[2], 0)
        dy = max(a[1] - y, y - a[3], 0)
        gap = math.hypot(dx, dy) - SCREW_HEAD_DIAMETER / 2
        assert gap >= 0.75, (ref, name, gap)
        mounting_clearances[ref + ' to ' + name] = round(gap, 3)
    closest = float('inf')
    for track in b.GetTracks():
        if isinstance(track, p.PCB_VIA):
            continue
        a = track.GetStart()
        c = track.GetEnd()
        ax, ay = p.ToMM(a.x), p.ToMM(a.y)
        cx, cy = p.ToMM(c.x), p.ToMM(c.y)
        dx, dy = cx - ax, cy - ay
        den = dx * dx + dy * dy
        factor = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / den)) if den else 0
        distance = (
            math.hypot(x - ax - factor * dx, y - ay - factor * dy)
            - SCREW_HEAD_DIAMETER / 2
            - p.ToMM(track.GetWidth()) / 2
        )
        closest = min(closest, distance)
    assert closest >= 0.2, (ref, 'screw head to track', closest)
    mounting_copper_clearances[ref] = round(closest, 3)

assert len([ref for ref in fps if ref.startswith('H')]) == 4
report = {
    'board_mm': [BOARD_WIDTH, BOARD_HEIGHT],
    'connector_front_Y_mm': port_fronts,
    'panel_datum_Y_mm': PORT_FRONT_Y,
    'mounting_holes': MOUNTING_HOLES,
    'screw_head_diameter_mm': SCREW_HEAD_DIAMETER,
    'min_component_body_clearance_mm': min(clearances.values()),
    'min_screw_head_to_body_clearance_mm': min(mounting_clearances.values()),
    'screw_head_to_track_clearance_mm': mounting_copper_clearances,
    'track_segments': angles,
    'status': 'PASS: compact 68x44mm layout for Heemol 34x21mm HX711 meets >=2.0mm body clearance and 45-deg routing rules.',
}
(ROOT / 'layout-validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
