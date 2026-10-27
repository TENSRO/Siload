from pathlib import Path
import sys,bpy
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r))
from logo_in_scene import apply_scene_logo
assets=bpy.data.collections['SILOAD detailed assembly'];ink=bpy.data.materials['Warm white silkscreen']
apply_scene_logo(r,assets,ink)
scene=bpy.context.scene;scene.camera=bpy.data.objects['Hero camera'];bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(r/'visuals'/'SILOAD REV A-studio-branded.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in assets.objects:obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(r/'visuals'/'SILOAD REV A-detailed-branded.glb'),export_format='GLB',use_selection=True,export_apply=True)
scene.cycles.samples=32;scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
for filename,name in [('SILOAD REV A-hero-logo.png','Hero camera'),('SILOAD REV A-top-logo.png','Top camera')]:
 scene.camera=bpy.data.objects[name];scene.render.filepath=str(r/'visuals'/filename);bpy.ops.render.render(write_still=True)
 print('RENDER_COMPLETE',filename,flush=True)
scene.camera=bpy.data.objects['Hero camera'];bpy.ops.wm.save_as_mainfile(filepath=str(r/'visuals'/'SILOAD REV A-studio-branded.blend'))
