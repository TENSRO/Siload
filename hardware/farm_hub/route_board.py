"""Simple conservative two-layer draft routing; verify output with KiCad DRC."""
from pathlib import Path
import math, heapq
import pcbnew as p
from layout_config import BOARD_WIDTH,BOARD_HEIGHT,SCREW_HEAD_DIAMETER
ROOT=Path(__file__).resolve().parent
PATH=ROOT/'SILOAD REV A.kicad_pcb'
b=p.LoadBoard(str(PATH))
STEP=.1; W=round(BOARD_WIDTH/STEP)+1; H=round(BOARD_HEIGHT/STEP)+1
def to_grid(v): return (round((p.ToMM(v.x)-50)/STEP),round((p.ToMM(v.y)-50)/STEP))
def to_pos(v): return p.VECTOR2I(p.FromMM(50+v[0]*STEP),p.FromMM(50+v[1]*STEP))
def index(x,y): return y*W+x
def disk(grid,x,y,r,value):
 for yy in range(max(0,math.floor(y-r)),min(H,math.ceil(y+r)+1)):
  for xx in range(max(0,math.floor(x-r)),min(W,math.ceil(x+r)+1)):
   if (xx-x)**2+(yy-y)**2<=r*r: grid[index(xx,yy)]=value
pads={}; obstacles=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  pt=to_grid(pad.GetPosition()); size=pad.GetSize()
  radius=max(p.ToMM(size.x),p.ToMM(size.y))/2
  # Circular conservative obstacles for both round and rectangular pads.
  if pad.GetShape()!=p.PAD_SHAPE_CIRCLE: radius*=1.4143
  if fp.GetReference().startswith('H'):radius=max(radius,SCREW_HEAD_DIAMETER/2+.2)
  net=pad.GetNetCode()
  if net: pads.setdefault(net,[]).append((pt,pad.GetPosition()))
  obstacles.append((pt,radius,net))
tracks=[]
def make_grid(net,layer):
 grid=bytearray(W*H)
 for x in range(W):
  for y in [0,1,2,3,4,H-1,H-2,H-3,H-4,H-5]:grid[index(x,y)]=1
 for y in range(H):
  for x in [0,1,2,3,4,W-1,W-2,W-3,W-4,W-5]:grid[index(x,y)]=1
 for (x,y),r,n in obstacles:
  if n!=net:disk(grid,x,y,(r+.5)/STEP,1)
 for pts,n,l in tracks:
  if n!=net and l==layer:
   for x,y in pts:disk(grid,x,y,.6/STEP,1)
 return grid
def astar(start,end,grid):
 directions=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
 initial=(start[0],start[1],-1)
 queue=[(0,0,initial)]; costs={initial:0}; parents={}
 while queue:
  _,cost,state=heapq.heappop(queue)
  if cost!=costs.get(state):continue
  pt=state[:2];old_direction=state[2]
  if pt==end:
   path=[pt]
   while state!=initial:state=parents[state];path.append(state[:2])
   return path[::-1]
  allowed=range(8) if old_direction<0 else [old_direction,(old_direction+1)%8,(old_direction-1)%8]
  for direction in allowed:
   dx,dy=directions[direction];np=(pt[0]+dx,pt[1]+dy)
   if np[0]<0 or np[0]>=W or np[1]<0 or np[1]>=H or grid[index(*np)]:continue
   if dx and dy and (grid[index(pt[0]+dx,pt[1])] or grid[index(pt[0],pt[1]+dy)]):continue
   nc=cost+(14 if dx and dy else 10)+(15 if old_direction>=0 and old_direction!=direction else 0)
   ns=(np[0],np[1],direction)
   if nc<costs.get(ns,10**9):
    costs[ns]=nc;parents[ns]=state
    hx=abs(np[0]-end[0]);hy=abs(np[1]-end[1]);h=14*min(hx,hy)+10*abs(hx-hy)
    heapq.heappush(queue,(nc+h,nc,ns))
 return None
def segment(a,c,net,layer,width):
 if a==c:return
 t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(c);t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNetCode(net);b.Add(t)
def exact_link(a,c):
 # Keep even the sub-grid pad-center connections horizontal/vertical/45 degrees.
 dx=c.x-a.x;dy=c.y-a.y
 diagonal=min(abs(dx),abs(dy))
 middle=p.VECTOR2I(a.x+(diagonal if dx>=0 else -diagonal),a.y+(diagonal if dy>=0 else -diagonal))
 return [a,middle,c]
order=sorted(pads,key=lambda n:(b.FindNet(n).GetNetname().lstrip('/') in ['GND','+3V3'],len(pads[n])))
for net in order:
 nodes=pads[net];tree=[nodes[0]];remaining=nodes[1:]
 while remaining:
  found=None
  pairs=sorted((abs(a[0][0]-c[0][0])+abs(a[0][1]-c[0][1]),i,j) for i,a in enumerate(tree) for j,c in enumerate(remaining))
  grids={layer:make_grid(net,layer) for layer in [p.F_Cu,p.B_Cu]}
  for _,i,j in pairs:
   start,exact_start=tree[i];end,exact_end=remaining[j]
   for layer in [p.F_Cu,p.B_Cu]:
    grid=grids[layer];grid[index(*start)]=0;grid[index(*end)]=0
    path=astar(start,end,grid)
    if path:found=(path,layer);break
   if found:break
  if not found:raise RuntimeError('Unable to route '+b.FindNet(net).GetNetname())
  path,layer=found
  reduced=[path[0]]
  for k in range(1,len(path)-1):
   if (path[k][0]-path[k-1][0],path[k][1]-path[k-1][1])!=(path[k+1][0]-path[k][0],path[k+1][1]-path[k][1]):reduced.append(path[k])
  reduced.append(path[-1])
  coords=exact_link(exact_start,to_pos(reduced[0]))+[to_pos(v) for v in reduced[1:-1]]+exact_link(to_pos(reduced[-1]),exact_end)
  for a,c in zip(coords,coords[1:]):segment(a,c,net,layer,.3)
  tracks.append((path,net,layer));tree.append(remaining.pop(j))
 print('Routed',b.FindNet(net).GetNetname(),flush=True)
b.BuildConnectivity()
p.SaveBoard(str(PATH),b)
print('Saved routed draft.')
