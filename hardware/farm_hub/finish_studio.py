"""Render additional angles from the completed studio scene."""
import bpy
from pathlib import Path
r=Path(__file__).resolve().parent/'visuals';scene=bpy.context.scene
scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
for filename,camera in [('02-connectors','Connector camera'),('03-detail','Macro camera'),('04-top','Top camera')]:
 scene.camera=bpy.data.objects[camera];dest=r/('SILOAD REV A-'+filename+'.png')
 if dest.exists() and dest.stat().st_size>100000:continue
 scene.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
 print('RENDER_COMPLETE',dest,flush=True)
scene.camera=bpy.data.objects['Hero camera'];bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(r/'SILOAD REV A-studio.blend'))
