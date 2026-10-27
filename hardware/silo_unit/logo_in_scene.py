import bpy, json


def apply_scene_logo(root, collection, ink):
    data = json.loads((root / 'branding' / 'SiLoad-logo.json').read_text())
    for obj in list(bpy.data.objects):
        if obj.name == 'SiLoad brand badge':
            bpy.data.objects.remove(obj, do_unlink=True)
    cx, cy = data['center_pcb_mm']
    scale = data.get('scale', 1.0)
    vertical = data.get('vertical', False)
    curve = bpy.data.curves.new('SiLoad badge vector geometry', 'CURVE')
    curve.dimensions = '2D'
    curve.resolution_u = 1
    curve.fill_mode = 'BOTH'
    curve.extrude = 0.000001
    for poly in data['polygons']:
        for ring in [poly['outer']] + poly['holes']:
            spline = curve.splines.new('POLY')
            spline.points.add(len(ring) - 1)
            for point, (x, y) in zip(spline.points, ring):
                if vertical:
                    bx, by = y * scale, x * scale
                else:
                    bx, by = x * scale, -y * scale
                point.co = (bx * 0.001, by * 0.001, 0, 1)
            spline.use_cyclic_u = True
    obj = bpy.data.objects.new('SiLoad brand badge', curve)
    collection.objects.link(obj)
    obj.location = ((cx - 50) * 0.001, -(cy - 50) * 0.001, 0.001565)
    curve.materials.append(ink)
