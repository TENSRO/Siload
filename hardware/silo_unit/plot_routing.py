from pathlib import Path
import sys, json
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'SILOAD REV A' / '.modeldeps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from layout_config import (
    BOARD_WIDTH,
    BOARD_HEIGHT,
    MOUNTING_HOLES,
    SCREW_HEAD_DIAMETER,
    XIAO_HEADERS,
    HX_CENTER,
    MUX_POS,
)

r = Path(__file__).resolve().parent
d = json.loads((r / 'routing-data.json').read_text())
fig, ax = plt.subplots(figsize=(12, 8), facecolor='#f4f6f8')
ax.set_facecolor('#102b22')
for t in d['tracks']:
    a, b = t['a'], t['b']
    ax.plot(
        [a[0], b[0]],
        [a[1], b[1]],
        color='#ff725e' if t['layer'] == 'F.Cu' else '#69b9ff',
        lw=1.6,
        solid_capstyle='round',
        zorder=2,
    )
for pad in d['pads']:
    x, y = pad['xy']
    ax.add_patch(Circle((x, y), 0.78, facecolor='#d8c27b', edgecolor='#fff5d7', lw=0.65, zorder=3))
    ax.add_patch(Circle((x, y), 0.4, facecolor='#102b22', zorder=4))
    if pad['pin'] == '1':
        ax.text(x - 1.4, y - 0.8, pad['ref'], color='white', fontsize=8.5, zorder=5)

envelopes = [
    (XIAO_HEADERS[0] - 51.28, XIAO_HEADERS[1] - 52.921, 17.8, 21.44, 'XIAO S3 + Wio'),
    (HX_CENTER[0] - 50 - 17.0, HX_CENTER[1] - 50 - 10.5, 34.0, 21.0, 'Heemol HX711 (34x21 mm)'),
    (MUX_POS[0] - 50 - 1.5, MUX_POS[1] - 50 - 8.0, 20.78, 9.88, 'CD4052 Mux (DIP-16)'),
]
for x, y, w, h, label in envelopes:
    ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor='#cfe9dc', lw=1.1, ls='--'))
    ax.text(x + w / 2, y + h / 2, label, color='#cfe9dc', ha='center', va='center', fontsize=9)

for ref, x, y in MOUNTING_HOLES:
    ax.add_patch(
        Circle(
            (x - 50, y - 50),
            SCREW_HEAD_DIAMETER / 2,
            facecolor='#17382d',
            edgecolor='#cfe9dc',
            lw=0.9,
            ls=':',
            zorder=1,
        )
    )
    ax.add_patch(Circle((x - 50, y - 50), 1.35, facecolor='#f4f6f8', edgecolor='#cfe9dc', lw=1, zorder=5))
    ax.text(x - 50, y - 46.2, f'{ref} M2.5', color='#cfe9dc', ha='center', fontsize=8)

ax.add_patch(Rectangle((0, 0), BOARD_WIDTH, BOARD_HEIGHT, fill=False, edgecolor='#f3d36b', lw=2.2))
ax.set_xlim(-3, BOARD_WIDTH + 3)
ax.set_ylim(BOARD_HEIGHT + 3, -4)
ax.set_aspect('equal')
ax.set_xlabel('X (mm)')
ax.set_ylabel('Y (mm)')
ax.set_title(f'SILOAD LOAD CELL REV A — {BOARD_WIDTH}x{BOARD_HEIGHT} mm (Heemol 34x21mm HX711 + CD4052 + 4x Load Cell + DS18B20)')
fig.tight_layout()
fig.savefig(r / 'SILOAD LOAD CELL REV A-routing.png', dpi=220)
print('Saved routing plot.')
