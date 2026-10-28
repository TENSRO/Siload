"""Indicative module envelopes for the 3D preview, not dimensioned vendor CAD."""
from pathlib import Path
import json
import pcbnew as p
ROOT=Path(__file__).resolve().parent
(ROOT/'models').mkdir(exist_ok=True)
boxes=[]
def box(x,y,z,dx,dy,dz,color):
 boxes.append(dict(center=[x,y,z],size=[dx,dy,dz],color=[float(v) for v in color.split()]))
 return f'Transform {{ translation {x/2.54} {y/2.54} {z/2.54} children [ Shape {{ appearance Appearance {{ material Material {{ diffuseColor {color} }} }} geometry Box {{ size {dx/2.54} {dy/2.54} {dz/2.54} }} }} ] }}\n'
green='.009 .012 .016'; black='.055 .055 .065'; metal='.7 .72 .75'; gold='.8 .58 .12'
stack='#VRML V2.0 utf8\n'
stack+=box(7.62,-7.5565,9.125,17.8,20.955,1.25,green)
stack+=box(7.62,-8,10.4,12,10,2.7,metal)
stack+=box(7.62,1.198,10.86,8.94,6.5,4.2,metal)
stack+=box(7.62,4.448,10.86,6.8,.15,2.5,black)
stack+=box(7.62,-7.799,16.2,17.8,21.44,1.6,green)
stack+=box(7.62,-12.402,18.225,11,11.6,2.15,metal)
stack+=box(13,-16,18.2,2.5,2.5,1.8,gold)
stack_boxes=boxes;boxes=[]
eth='#VRML V2.0 utf8\n'
eth+=box(10.16,-6.5,9.3,25,28.5,1.6,green)
eth+=box(10.16,1.73,17.85,16.51,15,15.5,metal)
eth+=box(10.16,9.23,17,12,0.15,9,black)
eth+=box(10.16,-13.8,10.85,7,7,1.5,black)
eth+=box(2.44,-16.3,10.8,3.2,2.5,1.4,metal)
(ROOT/'models'/'xiao-wio-indicative.wrl').write_text(stack)
(ROOT/'models'/'w5500-indicative.wrl').write_text(eth)
(ROOT/'models'/'module-geometry.json').write_text(json.dumps({'xiao-wio-indicative':stack_boxes,'w5500-indicative':boxes},indent=2))
board=p.LoadBoard(str(ROOT/'SILOAD REV A.kicad_pcb'))
for fp in board.GetFootprints():
 if fp.GetReference() in ['J1','J3']:
  model=p.FP_3DMODEL()
  fn='xiao-wio-indicative.wrl' if fp.GetReference()=='J1' else 'w5500-indicative.wrl'
  model.m_Filename='${KIPRJMOD}/models/'+fn
  model.m_Scale.x=model.m_Scale.y=model.m_Scale.z=1
  fp.Models().append(model)
p.SaveBoard(str(ROOT/'SILOAD REV A.kicad_pcb'),board)
print('Added indicative module geometry; standard sockets/capacitors use KiCad models.')
