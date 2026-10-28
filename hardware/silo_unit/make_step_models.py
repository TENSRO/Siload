"""Create STEP models for XIAO/Wio and HX711 using local cadquery-ocp-novtk."""
from pathlib import Path
import sys, json

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'SILOAD REV A' / '.modeldeps'))
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.gp import gp_Pnt
from OCP.STEPControl import STEPControl_Writer, STEPControl_AsIs
from OCP.IFSelect import IFSelect_RetDone

for name, boxes in json.loads((ROOT / 'models' / 'module-geometry.json').read_text()).items():
    writer = STEPControl_Writer()
    for box in boxes:
        x, y, z = box['center']
        dx, dy, dz = box['size']
        shape = BRepPrimAPI_MakeBox(gp_Pnt(x - dx / 2, y - dy / 2, z - dz / 2), dx, dy, dz).Shape()
        assert writer.Transfer(shape, STEPControl_AsIs) == IFSelect_RetDone
    dest = ROOT / 'models' / (name + '.step')
    assert writer.Write(str(dest)) == IFSelect_RetDone
    print('Created', dest.name)
