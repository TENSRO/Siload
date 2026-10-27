"""Convert the supplied badge into filled KiCad and render polygons."""
from pathlib import Path
import sys,json,shutil
from layout_config import LOGO_CENTER
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r/'.modeldeps'))
import cv2
import numpy as np
from PIL import Image
source=Path(r'C:\Users\leonb\Downloads\SiLoad_Monochrome_Tech_Badge-removebg-preview.png')
dest=r/'branding';dest.mkdir(exist_ok=True)
shutil.copy2(source,dest/'SiLoad-original.png')
image=np.array(Image.open(source).convert('RGBA'))
mask=((image[:,:,:3].mean(axis=2)>160)&(image[:,:,3]>128)).astype('uint8')*255
ys,xs=np.nonzero(mask);x0,x1=xs.min(),xs.max()+1;y0,y1=ys.min(),ys.max()+1
mask=mask[y0:y1,x0:x1]
contours,hierarchy=cv2.findContours(mask,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
width=20.0;scale=width/mask.shape[1];height=mask.shape[0]*scale
polys=[]
def convert(index):
 pts=cv2.approxPolyDP(contours[index],.45,True).reshape(-1,2)
 return [[round(float(x)*scale-width/2,5),round(float(y)*scale-height/2,5)] for x,y in pts]
for i in range(len(contours)):
 if hierarchy[0,i,3]!=-1:continue
 outer=convert(i)
 if len(outer)<3:continue
 holes=[];child=hierarchy[0,i,2]
 while child!=-1:
  hole=convert(child)
  if len(hole)>2:holes.append(hole)
  child=hierarchy[0,child,0]
 polys.append({'outer':outer,'holes':holes})
data={'width_mm':width,'height_mm':height,'center_pcb_mm':list(LOGO_CENTER),'polygons':polys}
(dest/'SiLoad-logo.json').write_text(json.dumps(data,indent=2))
paths=[]
for poly in polys:
 d=' '.join('M '+' '.join(f'{x+width/2},{y+height/2}' for x,y in ring)+' Z' for ring in [poly['outer']]+poly['holes'])
 paths.append(f'<path d="{d}" fill="white" fill-rule="evenodd"/>')
(dest/'SiLoad-logo.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}mm" height="{height}mm">'+''.join(paths)+'</svg>')
print('Logo',width,'x',round(height,3),'mm;',len(polys),'filled parts')
