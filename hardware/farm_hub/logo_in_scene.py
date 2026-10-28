import bpy,json
def apply_scene_logo(root,collection,ink):
 data=json.loads((root/'branding'/'SiLoad-logo.json').read_text())
 font=None
 for obj in list(bpy.data.objects):
  if obj.type=='FONT' and obj.data.body in ['SILOAD REV A','Farm hub','REV A']:
   font=obj.data.font;bpy.data.objects.remove(obj,do_unlink=True)
 for obj in list(bpy.data.objects):
  if obj.name=='SiLoad brand badge':bpy.data.objects.remove(obj,do_unlink=True)
 cx,cy=data['center_pcb_mm'];curve=bpy.data.curves.new('SiLoad badge vector geometry','CURVE');curve.dimensions='2D';curve.resolution_u=1;curve.fill_mode='BOTH';curve.extrude=.000001
 for poly in data['polygons']:
  for ring in [poly['outer']]+poly['holes']:
   spline=curve.splines.new('POLY');spline.points.add(len(ring)-1)
   for point,(x,y) in zip(spline.points,ring):point.co=(x*.001,-y*.001,0,1)
   spline.use_cyclic_u=True
 obj=bpy.data.objects.new('SiLoad brand badge',curve);collection.objects.link(obj);obj.location=((cx-50)*.001,-(cy-50)*.001,.001565);curve.materials.append(ink)
 rev=bpy.data.curves.new('Revision A','FONT');rev.body='REV A';rev.align_x='CENTER';rev.align_y='CENTER';rev.size=.0008
 if font:rev.font=font
 obj=bpy.data.objects.new('Revision A',rev);collection.objects.link(obj);obj.location=((cx-50)*.001,-.0351,.001565);rev.materials.append(ink)
