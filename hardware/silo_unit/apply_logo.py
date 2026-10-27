from pathlib import Path
import json
import pcbnew as p
from layout_config import LOGO_CENTER

r = Path(__file__).resolve().parent


def apply(board):
    data = json.loads((r / 'branding' / 'SiLoad-logo.json').read_text())
    data['center_pcb_mm'] = list(LOGO_CENTER)
    (r / 'branding' / 'SiLoad-logo.json').write_text(json.dumps(data, indent=2))
    previous = list(board.GetFootprints())
    fp = p.FOOTPRINT(board)
    board.Add(fp)
    fp.SetReference('LOGO1')
    fp.SetValue('SiLoad badge 20mm')
    fp.SetFPIDAsString('SILOAD:SiLoad_Badge_20mm')
    fp.SetAttributes(p.FP_BOARD_ONLY)
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    cx, cy = LOGO_CENTER
    polyset = p.SHAPE_POLY_SET()
    for poly in data['polygons']:
        outline = polyset.NewOutline()
        for x, y in poly['outer']:
            polyset.Append(p.FromMM(x), p.FromMM(y), outline, -1)
        for hole in poly['holes']:
            index = polyset.NewHole(outline)
            for x, y in hole:
                polyset.Append(p.FromMM(x), p.FromMM(y), outline, index)
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


if __name__ == '__main__':
    path = r / 'SILOAD LOAD CELL REV A.kicad_pcb'
    b = p.LoadBoard(str(path))
    fp = apply(b)
    p.SaveBoard(str(path), b)
    (r / 'fp-lib-table').write_text(
        '(fp_lib_table (version 7) (lib (name "SILOAD") (type "KiCad") (uri "${KIPRJMOD}/SILOAD.pretty") (options "") (descr "SiLoad branding")))'
    )
    print('Added actual F.Silkscreen logo, footprint LOGO1.')
