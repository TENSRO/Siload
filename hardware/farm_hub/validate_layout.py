from pathlib import Path
import json,math
import pcbnew as p
from layout_config import BOARD_WIDTH,BOARD_HEIGHT,MOUNTING_HOLES,SCREW_HEAD_DIAMETER,PORT_FRONT_Y
ROOT=Path(__file__).resolve().parent
b=p.LoadBoard(str(ROOT/'SILOAD REV A.kicad_pcb'))
fps={f.GetReference():f for f in b.GetFootprints()}
def xy(ref):
 point=fps[ref].GetPosition();return p.ToMM(point.x),p.ToMM(point.y)
x,y=xy('J1');x2,y2=xy('J3')
envelopes={'XIAO/Wio':(x-1.28,y-2.921,x+16.52,y+18.519),'W5500':(x2-2.34,y2-7.75,x2+22.66,y2+20.75)}
port_fronts={'USB-C':50-y+4.448,'RJ45_reference':50-y2+9.23}
assert all(abs(front-PORT_FRONT_Y)<.01 for front in port_fronts.values()),port_fronts
x,y=xy('C1');envelopes['C1']=(x-1.25,y-1.25,x+3.75,y+1.25)
x,y=xy('C2');envelopes['C2']=(x-1.5,y-2.5,x+3.5,y+2.5)
clearances={}
for module in ['XIAO/Wio','W5500']:
 for other in ['C1','C2']+(['W5500'] if module=='XIAO/Wio' else []):
  a=envelopes[module];c=envelopes[other]
  dx=max(c[0]-a[2],a[0]-c[2],0);dy=max(c[1]-a[3],a[1]-c[3],0)
  gap=math.hypot(dx,dy)
  assert gap>=2-1e-8,(module,other,gap)
  clearances[module+' to '+other]=round(gap,3)
angles={'horizontal':0,'vertical':0,'diagonal45':0}
for t in b.GetTracks():
 a=t.GetStart();c=t.GetEnd();dx=abs(a.x-c.x);dy=abs(a.y-c.y)
 assert dx==0 or dy==0 or abs(dx-dy)<=2,('Non-45-degree track',a,c)
 angles['vertical' if dx==0 else 'horizontal' if dy==0 else 'diagonal45']+=1
assert angles['diagonal45']>0
mounting_clearances={}
mounting_copper_clearances={}
for ref,x,y in MOUNTING_HOLES:
 assert xy(ref)==(x,y)
 assert 50+SCREW_HEAD_DIAMETER/2<x<50+BOARD_WIDTH-SCREW_HEAD_DIAMETER/2
 assert 50+SCREW_HEAD_DIAMETER/2<y<50+BOARD_HEIGHT-SCREW_HEAD_DIAMETER/2
 for name,a in envelopes.items():
  dx=max(a[0]-x,x-a[2],0);dy=max(a[1]-y,y-a[3],0)
  gap=math.hypot(dx,dy)-SCREW_HEAD_DIAMETER/2
  assert gap>=.75,(ref,name,gap)
  mounting_clearances[ref+' to '+name]=round(gap,3)
 closest=float('inf')
 for track in b.GetTracks():
  a=track.GetStart();c=track.GetEnd()
  ax,ay=p.ToMM(a.x),p.ToMM(a.y);cx,cy=p.ToMM(c.x),p.ToMM(c.y)
  dx,dy=cx-ax,cy-ay;den=dx*dx+dy*dy
  factor=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/den)) if den else 0
  distance=math.hypot(x-ax-factor*dx,y-ay-factor*dy)-SCREW_HEAD_DIAMETER/2-p.ToMM(track.GetWidth())/2
  closest=min(closest,distance)
 assert closest>=.2,(ref,'screw head to track',closest)
 mounting_copper_clearances[ref]=round(closest,3)
assert len([ref for ref in fps if ref.startswith('H')])==4
report={'board_mm':[BOARD_WIDTH,BOARD_HEIGHT],'connector_front_Y_mm':port_fronts,'panel_datum_Y_mm':PORT_FRONT_Y,'mounting_holes':MOUNTING_HOLES,'screw_head_diameter_mm':SCREW_HEAD_DIAMETER,'screw_head_to_body_clearance_mm':mounting_clearances,'screw_head_to_track_clearance_mm':mounting_copper_clearances,'component_body_clearance_mm':clearances,'track_segments':angles,'status':'PASS for CAD and reference module envelopes; physical ARCELI dimensions still unconfirmed'}
(ROOT/'layout-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
