"""Render both Siload PCBs (Farm Hub 59x36mm + Silo Unit 68x44mm) together in a single studio scene."""
import bpy, math, sys
from pathlib import Path
from mathutils import Vector

quick = '--quick' in sys.argv
ROOT = Path(__file__).resolve().parent
HUB_DIR = ROOT.parent / 'SILOAD REV A'
OUT = ROOT / 'visuals'
MM = 0.001

# Load the Silo Unit studio scene as base
bpy.ops.wm.open_mainfile(filepath=str(OUT / 'SILOAD LOAD CELL REV A-studio-branded.blend'))
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 8 if quick else 20
scene.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for dev_type in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
        try:
            prefs.compute_device_type = dev_type
            prefs.get_devices()
            if any(d.type == dev_type for d in prefs.devices):
                for d in prefs.devices:
                    d.use = True
                scene.cycles.device = 'GPU'
                break
        except Exception:
            pass
except Exception:
    pass

scene.render.resolution_x = 1400 if quick else 2000
scene.render.resolution_y = 875 if quick else 1250
scene.render.resolution_percentage = 100

silo_col = bpy.data.collections.get('SILOAD Silo Unit detailed assembly')
studio_col = bpy.data.collections.get('Studio lighting and cameras')

# Shift Silo Unit (68x44 mm) to the right: x = +38..+106 mm, y = -44..0 mm
for obj in silo_col.objects:
    if obj.parent is None:
        obj.location.x += 38.0 * MM

# Append Farm Hub collection from SILOAD REV A-studio-branded.blend
hub_blend = HUB_DIR / 'visuals' / 'SILOAD REV A-studio-branded.blend'
with bpy.data.libraries.load(str(hub_blend), link=False) as (data_from, data_to):
    data_to.collections = ['SILOAD detailed assembly']

hub_col = data_to.collections[0]
scene.collection.children.link(hub_col)

# Shift Farm Hub (59x36 mm) to the left: x = -35..+24 mm, y = -40..-4 mm
for obj in hub_col.objects:
    if obj.parent is None:
        obj.location.x -= 35.0 * MM
        obj.location.y -= 4.0 * MM

# Create 3D studio nameplates in front of both PCBs
font_path = Path(r'C:\Windows\Fonts\consola.ttf')
font = bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
plate_mat = bpy.data.materials.get('Moulded graphite polymer')
ink_mat = bpy.data.materials.get('Warm white silkscreen')


def add_plate(title, subtitle, cx_mm, cy_mm):
    bpy.ops.mesh.primitive_cube_add(size=1, location=Vector((cx_mm, cy_mm, -4.3)) * MM)
    plate = bpy.context.object
    plate.name = f'Nameplate {title}'
    plate.dimensions = Vector((56.0, 11.5, 1.4)) * MM
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    plate.data.materials.append(plate_mat)
    bevel = plate.modifiers.new('Bevel', 'BEVEL')
    bevel.width = 0.25 * MM
    bevel.segments = 3

    for txt, dy, sz in [(title, 2.0, 3.1), (subtitle, -2.3, 2.0)]:
        curve = bpy.data.curves.new(txt, 'FONT')
        curve.body = txt
        curve.align_x = 'CENTER'
        curve.align_y = 'CENTER'
        curve.size = sz * MM
        curve.extrude = 0.08 * MM
        if font:
            curve.font = font
        tobj = bpy.data.objects.new(f'Label {txt}', curve)
        scene.collection.objects.link(tobj)
        tobj.location = Vector((cx_mm, cy_mm + dy, -3.55)) * MM
        curve.materials.append(ink_mat)


add_plate('FARM HUB (59x36 mm)', 'XIAO S3 + Wio LoRa + W5500 ETH', -5.5, -53.5)
add_plate('SILO UNIT (68x44 mm)', 'XIAO S3 + LoRa + HX711 + CD4052 4x Mux', 72.0, -53.5)


def aim(obj, pt):
    obj.rotation_euler = (Vector(pt) * MM - obj.location).to_track_quat('-Z', 'Y').to_euler()


def camera(name, pos, target, lens=58, ortho=None):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    studio_col.objects.link(obj)
    obj.location = Vector(pos) * MM
    aim(obj, target)
    data.lens = lens
    data.clip_start = 0.0001
    data.clip_end = 10
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho * MM
    return obj


# Adjust lighting to cover both boards evenly
for obj in studio_col.objects:
    if obj.type == 'LIGHT':
        obj.data.energy *= 1.35

combined_cameras = [
    ('SILOAD-COMBINED-hero.png', camera('Combined Hero', (34, -205, 142), (34, -27, 4), lens=47)),
    ('SILOAD-COMBINED-top.png', camera('Combined Top', (34, -28, 220), (34, -28, 0), ortho=166)),
]

for filename, cam in combined_cameras:
    scene.camera = cam
    out_path = OUT / filename
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print('COMBINED_RENDER_COMPLETE', out_path, flush=True)
