"""Blender studio scene built from real CAD meshes and a reconstructed W5500 module."""
import bpy,math,json,sys,random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'visuals';MESHES=OUT/'meshes';MM=.001
sys.path.insert(0,str(ROOT))
from layout_config import XIAO_HEADERS,ETH_HEADERS,MOUNTING_HOLES
DX=XIAO_HEADERS[0]-54.5;DY=62.3-XIAO_HEADERS[1]
EDX=ETH_HEADERS[0]-75.36;EDY=57-ETH_HEADERS[1]
preview='--preview' in sys.argv
quick='--quick' in sys.argv
enclosure='--enclosure' in sys.argv
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.samples=12 if quick else (24 if preview else 48);scene.cycles.use_denoising=True
scene.render.resolution_x=900 if quick else (1000 if preview else 1800);scene.render.resolution_y=675 if quick else (750 if preview else 1350);scene.render.resolution_percentage=100
if enclosure:scene.cycles.samples=24;scene.render.resolution_x=1600;scene.render.resolution_y=1200
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=0
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.9,.93,1,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.10
scene.render.image_settings.color_depth='8';scene.render.film_transparent=False
assets=bpy.data.collections.new('SILOAD detailed assembly');scene.collection.children.link(assets)
studio=bpy.data.collections.new('Studio lighting and cameras');scene.collection.children.link(studio)
def move(obj,collection=assets):
 for c in list(obj.users_collection):c.objects.unlink(obj)
 collection.objects.link(obj);return obj
cache={}
def material(name,color,metallic=0,rough=.35,grain=False):
 if name in cache:return cache[name]
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metallic;p.inputs['Roughness'].default_value=rough
 if grain:
  noise=m.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=6000;noise.inputs['Detail'].default_value=2
  bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.11;bump.inputs['Distance'].default_value=.0000025
  m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 cache[name]=m;return m
green=material('Matte black soldermask',(.006,.008,.011),0,.44,True)
green.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.2
black=material('Moulded graphite polymer',(.012,.015,.019),0,.38,True)
silver=material('Brushed nickel',(.58,.63,.69),.92,.26,True)
gold=material('Gold plated contacts',(.72,.46,.15),.88,.22)
ink=material('Warm white silkscreen',(.87,.91,.88),0,.55)
laser=material('Laser marking charcoal',(.045,.052,.058),.15,.53)
tan=material('Ceramic dielectric',(.30,.19,.08),0,.49)
yellow=material('Header insulator warm yellow',(.83,.55,.025),0,.33)
def cad_material(role,part):
 c=part['color'];r,g,b=c;name=part['name']
 if role=='carrier' and name.endswith('_PCB'):return green
 if role=='carrier' and name.endswith('_pad'):return gold
 if role=='wio' and 'V1.0_PCB' in name:return green
 if role=='xiao' and name=='SOLID' and max(c)-min(c)<.01 and r<.05:return green
 if b>r*2.5 and b>g*2:return material('Blue electrolytic sleeve',(.012,.065,.23),.15,.27)
 if g>r*1.25 and g>b*1.2:return material('LED green lens',(.045,.26,.025),.05,.22)
 if r>.65 and g>.35 and b<.42:return gold
 if max(c)-min(c)<.08 and max(c)>.15:return silver
 if role=='w5500_chip' and max(c)>.3:return silver
 if max(c)<.12:return black
 return material('CAD '+str(tuple(c)),c,0,.4)
def mesh_obj(name,vertices,triangles,mat):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([[v*MM for v in pt] for pt in vertices],[],triangles);mesh.update()
 obj=bpy.data.objects.new(name,mesh);assets.objects.link(obj);obj.data.materials.append(mat)
 for poly in mesh.polygons:poly.use_smooth=True
 return obj
def load(role,transform):
 data=json.loads((MESHES/(role+'.json')).read_text())
 for i,part in enumerate(data['parts']):mesh_obj(role+' | '+part['name']+' '+str(i),[transform(*v) for v in part['vertices']],part['triangles'],cad_material(role,part))
def cube(name,loc,size,mat,bevel=.05):
 bpy.ops.mesh.primitive_cube_add(size=1,location=Vector(loc)*MM);o=move(bpy.context.object);o.name=name;o.dimensions=Vector(size)*MM
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 if bevel:
  mod=o.modifiers.new('Machined edge softness','BEVEL');mod.width=bevel*MM;mod.segments=3
  o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o
def cylinder(name,loc,radius,depth,mat,vertices=48):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius*MM,depth=depth*MM,location=Vector(loc)*MM)
 o=move(bpy.context.object);o.name=name;o.data.materials.append(mat)
 bevel=o.modifiers.new('Edge rounding','BEVEL');bevel.width=.05*MM;bevel.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
font_path=Path(r'C:\Windows\Fonts\consola.ttf');font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
def text(body,loc,size,mat=ink,angle=0,name=None):
 data=bpy.data.curves.new(name or body,'FONT');data.body=body;data.align_x='CENTER';data.align_y='CENTER';data.size=size*MM;data.extrude=.001*MM
 if font:data.font=font
 o=bpy.data.objects.new(name or 'Marking | '+body,data);assets.objects.link(o);o.location=Vector(loc)*MM;o.rotation_euler.z=math.radians(angle);data.materials.append(mat);return o
def trace(name,pts,width,mat):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=width*MM/2;data.bevel_resolution=2
 s=data.splines.new('POLY');s.points.add(len(pts)-1)
 for p,pt in zip(s.points,pts):p.co=(*[v*MM for v in pt],1)
 o=bpy.data.objects.new(name,data);assets.objects.link(o);data.materials.append(mat);return o

# Real CAD: carrier components, Seeed XIAO and Seeed Wio extension.
load('carrier',lambda x,y,z:(x,y,z))
load('xiao',lambda x,y,z:(z+18.231+DX,x-21.661+DY,y+10.35))
load('wio',lambda x,y,z:(x-102.282+DX,y+100.983+DY,z+17.0))
for side,base_x in [('left',4.5),('right',19.74)]:
 x=base_x+DX
 for i in range(7):
  y=-12.3-i*2.54+DY
  cube('XIAO to LoRa stacking header '+side+str(i),(x,y,12.62),(2.45,2.45,2.54),black,.08)
  cube('XIAO to LoRa gold pin '+side+str(i),(x,y,13.45),(.50,.50,11.9),gold,.035)
  vertices=[];faces=[]
  for k in range(48):
   a=2*math.pi*k/48
   for radius in [.5,.84]:vertices.append([x+radius*math.cos(a),y+radius*math.sin(a),18.61])
  for k in range(48):
   j=(k+1)%48;faces.extend([[2*k,2*k+1,2*j+1],[2*k,2*j+1,2*j]])
  mesh_obj('Wio plated header pad '+side+str(i),vertices,faces,gold)
details=json.loads((OUT/'board-details.json').read_text())
for t in details['text']:text(t['text'],[*t['position'],1.565],t['height'],angle=t['angle'])
if (ROOT/'branding'/'SiLoad-logo.json').exists():
 sys.path.insert(0,str(ROOT))
 from logo_in_scene import apply_scene_logo
 apply_scene_logo(ROOT,assets,ink)
under_mask=material('Copper relief beneath soldermask',(.008,.01,.013),0,.48)
under_mask.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.2
for i,t in enumerate(details['tracks']):
 a=t['a'];b=t['b'];dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
 if length>0:
  ex=-dy/length*t['width']/2;ey=dx/length*t['width']/2
  mesh_obj('Covered copper '+str(i),[[a[0]+ex,a[1]+ey,1.512],[b[0]+ex,b[1]+ey,1.512],[b[0]-ex,b[1]-ey,1.512],[a[0]-ex,a[1]-ey,1.512]],[[0,1,2],[0,2,3]],under_mask)
text('seeed studio',(12.1+DX,-23.0+DY,20.805),1.0,laser)
text('Wio-SX1262',(12.1+DX,-24.7+DY,20.805),.85,laser)
text('868 / 915 MHz',(12.1+DX,-26.2+DY,20.805),.55,laser)

# ARCELI mini module reconstruction: geometry follows product photos, not vendor CAD.
before_ethernet=set(assets.objects)
cx=35.52;module_top=11.7
module_pcb=cube('ARCELI W5500 mini PCB',(cx,-13.5,10.9),(25,28.5,1.6),green,.13)
load('rj45',lambda x,y,z:(x-3.55+cx,y-5.8,z+module_top))
angle=math.radians(45)
load('w5500_chip',lambda x,y,z:(cx+x*math.cos(angle)-y*math.sin(angle),-20.8+x*math.sin(angle)+y*math.cos(angle),z+module_top))
text('WIZnet',(cx,-20,13.208),.85,ink,45)
text('W5500',(cx,-21.2,13.208),.8,ink,45)
text('2147',(cx,-22.2,13.208),.43,ink,45)
for side,x,labels in [('L',25.36,['GND','GND','MOSI','SCLK','CS','INT']),('R',45.68,['GND','3V3','3V3','NC','RST','MISO'])]:
 for i,label in enumerate(labels):
  y=-7-i*2.54
  cube('Male header '+side+str(i),(x,y,12.97),(2.45,2.45,2.54),yellow,.08)
  cube('Gold square pin '+side+str(i),(x,y,11.9),(.64,.64,7.2),gold,.05)
  text(label,(x+(-1.85 if side=='L' else 1.8),y,module_top+.02),.42,ink,90)

# Small passives and crystal around the Ethernet controller.
cube('25 MHz crystal metal can',(27.8,-23.3,12.45),(3.2,2.5,1.4),silver,.18)
text('25.000',(27.8,-23.3,13.16),.48,laser,90)
random.seed(12)
for i,(x,y,rotation) in enumerate([(28,-17,0),(28,-19,0),(30,-25.2,90),(32,-26.4,0),(40,-26,0),(42.7,-22.5,90),(42.7,-24.5,90),(42.6,-19,90),(30,-14.9,0),(32.3,-14.5,0),(38.8,-14.7,0),(40.8,-15.6,90)]):
 mat=tan if i%3 else black
 body=cube('0402 passive '+str(i),(x,y,12.04),(1.0,.5,.6),mat,.025);body.rotation_euler.z=math.radians(rotation)
 for sign in [-1,1]:
  dx=sign*.43*math.cos(math.radians(rotation));dy=sign*.43*math.sin(math.radians(rotation))
  cap=cube('Passive plated end '+str(i),(x+dx,y+dy,12.04),(.18,.52,.62),silver,.018);cap.rotation_euler.z=math.radians(rotation)
text('W5500  SPI ETHERNET',(cx,-26.9,module_top+.015),.55)
text('LINK',(28.2,-15.1,module_top+.015),.5,ink,90)
text('ACT',(42.7,-15.1,module_top+.015),.5,ink,90)
for obj in set(assets.objects)-before_ethernet:obj.location+=Vector((EDX,EDY,0))*MM

# Visual mounting hardware in its own collection, so it can be hidden for CAD use.
hardware=[]
for i,(_,mx,my) in enumerate(MOUNTING_HOLES):
 x=mx-50;y=50-my
 spacer=cylinder('M2.5 hex spacer '+str(i),(x,y,-2.5),2.5,5,gold,6);hardware.append(spacer)
 screw=cylinder('M2.5 screw head '+str(i),(x,y,2.2),2.25,1.25,silver);hardware.append(screw)
 # Dark socket recess and a small bevel make the screw readable at product scale.
 socket=cylinder('Screw hex socket '+str(i),(x,y,2.835),.9,.018,black,6);hardware.append(socket)

# White cyclorama, broad softboxes, long highlight on the metal connector.
floor_mat=material('Studio warm white',(.82,.84,.86),0,.75)
bpy.ops.mesh.primitive_plane_add(size=3,location=(.025,-.018,-.00508));floor=move(bpy.context.object,studio);floor.name='Seamless studio floor';floor.data.materials.append(floor_mat)
def aim(obj,pt):obj.rotation_euler=(Vector(pt)*MM-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,position,power,size,color,shape='DISK',size_y=None):
 data=bpy.data.lights.new(name,'AREA');data.energy=power/48;data.shape=shape;data.size=size*MM;data.color=color
 if size_y is not None:data.size_y=size_y*MM
 o=bpy.data.objects.new(name,data);studio.objects.link(o);o.location=Vector(position)*MM;aim(o,(27,-18,8));return o
area('Key | large softbox',(-40,-45,115),20,95,(1,.95,.88))
area('Fill | cool broad card',(100,40,70),13,85,(.88,.94,1))
area('Rim | vertical strip',(15,70,95),18,70,(1,1,1),'RECTANGLE',15)
area('Front polish card',(55,-100,40),5,65,(1,1,1))
def camera(name,pos,target,lens=65,ortho=None):
 data=bpy.data.cameras.new(name);obj=bpy.data.objects.new(name,data);studio.objects.link(obj);obj.location=Vector(pos)*MM;aim(obj,target);data.lens=lens;data.clip_start=.0001;data.clip_end=10
 if ortho:data.type='ORTHO';data.ortho_scale=ortho*MM
 return obj
cameras=[
 ('01-hero',camera('Hero camera',(95,-110,88),(29.5,-16.5,8),56)),
 ('02-connectors',camera('Connector camera',(82,95,65),(29.5,-13,9),68)),
 ('03-detail',camera('Macro camera',(70,-72,83),(25,-19,14),85)),
 ('04-top',camera('Top camera',(29.5,-16.5,150),(29.5,-16.5,0),ortho=77)),
]
scene.camera=cameras[0][1]
scene.camera=cameras[0][1]
bpy.ops.file.pack_all()
blend_path=OUT/('SILOAD REV A-enclosure.blend' if enclosure else 'SILOAD REV A-studio.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
if not preview:
 bpy.ops.object.select_all(action='DESELECT')
 for o in assets.objects:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(OUT/('SILOAD REV A-enclosure.glb' if enclosure else 'SILOAD REV A-detailed.glb')),export_format='GLB',use_selection=True,export_apply=True)
selected_cameras=cameras[:1] if preview else ([cameras[0],cameras[1],cameras[3]] if enclosure else cameras)
for name,cam in selected_cameras:
 scene.camera=cam;scene.render.filepath=str(OUT/('preview-black.png' if preview else 'SILOAD REV A-'+('enclosure-' if enclosure else '')+name+'.png'))
 bpy.ops.render.render(write_still=True)
 print('RENDER_COMPLETE',scene.render.filepath,flush=True)
scene.camera=cameras[0][1];bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
