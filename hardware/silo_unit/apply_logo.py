from pathlib import Path
import json
import pcbnew as p
from layout_config import LOGO_CENTER, LOGO_SCALE, LOGO_VERTICAL

r = Path(__file__).resolve().parent


def transform_xy(x, y):
    if LOGO_VERTICAL:
        return (y * LOGO_SCALE, -x * LOGO_SCALE)
    return (x * LOGO_SCALE, y * LOGO_SCALE)


def apply(board):
    data = json.loads((r / 'branding' / 'SiLoad-logo.json').read_text())
    data['center_pcb_mm'] = list(LOGO_CENTER)
    data['scale'] = LOGO_SCALE
    data['vertical'] = LOGO_VERTICAL
    (r / 'branding' / 'SiLoad-logo.json').write_text(json.dumps(data, indent=2))
    previous = list(board.GetFootprints())
    fp = p.FOOTPRINT(board)
    board.Add(fp)
    fp.SetReference('LOGO1')
    fp.SetValue('SiLoad badge vertical')
    fp.SetAttributes(p.FP_BOARD_ONLY)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    cx, cy = LOGO_CENTER
    polyset = p.SHAPE_POLY_SET()
    for poly in data['polygons']:
        outline = polyset.NewOutline()
        for x, y in poly['outer']:
            tx, ty = transform_xy(x, y)
            polyset.Append(p.FromMM(tx), p.FromMM(ty), outline, -1)
        for hole in poly['holes']:
            index = polyset.NewHole(outline)
            for x, y in hole:
                tx, ty = transform_xy(x, y)
                polyset.Append(p.FromMM(tx), p.FromMM(ty), outline, index)
    polyset.Fracture()
    for index in range(polyset.OutlineCount()):
        shape = p.PCB_SHAPE(fp)
        shape.SetShape(p.SHAPE_T_POLY)
        shape.SetLayer(p.F_SilkS)
        shape.SetWidth(0)
        shape.SetFilled(True)
        part = p.SHAPE_POLY_SET()
        part.AddOutline(polyset.COutline(index))
        shape.SetPolyShape(part)
        fp.Add(shape)
    fp.SetPosition(p.VECTOR2I(p.FromMM(cx), p.FromMM(cy)))
    for old in previous:
        if old.GetReference() == 'LOGO1':
            board.Remove(old)
    return fp
