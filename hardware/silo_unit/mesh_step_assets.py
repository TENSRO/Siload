"""Tessellate carrier-base.step with XCAF colors and reuse xiao/wio meshes."""
from pathlib import Path
import sys, json, shutil

ROOT = Path(__file__).resolve().parent
HUB = ROOT.parent / 'SILOAD REV A'
sys.path.insert(0, str(HUB / '.modeldeps'))
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDataStd import TDataStd_Name
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen
from OCP.TDF import TDF_Label
from OCP.collections import Sequence_TDF_Label
from OCP.Quantity import Quantity_Color
from OCP.gp import gp_Trsf, gp_Pnt
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.TopLoc import TopLoc_Location
from OCP.BRep import BRep_Tool
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib


def bounds(shape, trsf):
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    lo = box.CornerMin()
    hi = box.CornerMax()
    pts = []
    for x in [lo.X(), hi.X()]:
        for y in [lo.Y(), hi.Y()]:
            for z in [lo.Z(), hi.Z()]:
                a = gp_Pnt(x, y, z).Transformed(trsf)
                pts.append([a.X(), a.Y(), a.Z()])
    return [min(pt[i] for pt in pts) for i in range(3)] + [max(pt[i] for pt in pts) for i in range(3)]


def read_model(path, role):
    doc = TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    reader.ReadFile(str(path))
    assert reader.Transfer(doc)
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    colors = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    roots = Sequence_TDF_Label()
    tool.GetFreeShapes(roots)
    parts = []

    def get_color(shape):
        color = Quantity_Color()
        if colors.GetColor(shape, XCAFDoc_ColorSurf, color) or colors.GetColor(shape, XCAFDoc_ColorGen, color):
            return [color.Red(), color.Green(), color.Blue()]
        return None

    def walk(label, parent):
        if tool.IsReference_s(label):
            target = TDF_Label()
            tool.GetReferredShape_s(label, target)
            walk(target, parent.Multiplied(tool.GetLocation_s(label).Transformation()))
            return
        if tool.IsAssembly_s(label):
            children = Sequence_TDF_Label()
            tool.GetComponents_s(label, children)
            for i in range(1, children.Length() + 1):
                walk(children.Value(i), parent)
            return
        shape = tool.GetShape_s(label)
        if shape.IsNull():
            return
        attr = TDataStd_Name()
        name = 'part'
        if label.FindAttribute(TDataStd_Name.GetID_s(), attr):
            name = attr.Get().ToExtString()
        bbox = bounds(shape, parent)
        base_color = get_color(shape)
        BRepMesh_IncrementalMesh(shape, 0.05, False, 0.35, True)
        groups = {}
        explorer = TopExp_Explorer(shape, TopAbs_FACE)
        while explorer.More():
            face = TopoDS.Face(explorer.Current())
            loc = TopLoc_Location()
            tri = BRep_Tool.Triangulation_s(face, loc)
            if tri is not None:
                color = get_color(face) or base_color or [0.22, 0.22, 0.22]
                key = tuple(round(v, 4) for v in color)
                data = groups.setdefault(key, {'vertices': [], 'triangles': []})
                offset = len(data['vertices'])
                transform = parent.Multiplied(loc.Transformation())
                for i in range(1, tri.NbNodes() + 1):
                    point = tri.Node(i).Transformed(transform)
                    data['vertices'].append([point.X(), point.Y(), point.Z()])
                for i in range(1, tri.NbTriangles() + 1):
                    triangle = tri.Triangle(i)
                    a, c, d = [triangle.Value(k) for k in [1, 2, 3]]
                    indices = [offset + a - 1, offset + c - 1, offset + d - 1]
                    if face.Orientation() == TopAbs_REVERSED:
                        indices.reverse()
                    data['triangles'].append(indices)
            explorer.Next()
        for color, data in groups.items():
            if data['triangles']:
                parts.append({'name': name, 'color': color, 'bounds': bbox, **data})

    for i in range(1, roots.Length() + 1):
        walk(roots.Value(i), gp_Trsf())
    print(role, 'parts', len(parts), 'triangles', sum(len(p['triangles']) for p in parts), flush=True)
    summary = [{'name': p['name'], 'color': p['color'], 'bounds': [round(v, 3) for v in p['bounds']]} for p in parts]
    return {'parts': parts, 'summary': summary}


if __name__ == '__main__':
    out = ROOT / 'visuals' / 'meshes'
    out.mkdir(parents=True, exist_ok=True)
    for shared in ['xiao.json', 'wio.json']:
        shutil.copy2(HUB / 'visuals' / 'meshes' / shared, out / shared)
    data = read_model(ROOT / 'visuals' / 'carrier-base.step', 'carrier')
    (out / 'carrier.json').write_text(json.dumps(data, separators=(',', ':')))
    (out / 'summary.json').write_text(json.dumps({'carrier': data['summary']}, indent=2))
