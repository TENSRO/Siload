"""Blender studio scene for ultra-compact 64x40mm SILOAD LOAD CELL REV A (horizontal HX711 + horizontal CD4052 + 4x Load Cell + DS18B20)."""
import bpy, math, json, sys
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'visuals'
MESHES = OUT / 'meshes'
MM = 0.001
sys.path.insert(0, str(ROOT))
from layout_config import XIAO_HEADERS, HX_CENTER, HX_MCU_POS, HX_BRIDGE_POS, MOUNTING_HOLES, MUX_POS

DX = XIAO_HEADERS[0] - 54.5
DY = 62.3 - XIAO_HEADERS[1]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
quick = '--quick' in sys.argv
scene.render.engine = 'CYCLES'
scene.cycles.samples = 8 if quick else 18
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
                print('Using GPU device:', dev_type)
                break
        except Exception:
            pass
except Exception:
    pass
scene.render.resolution_x = 1200 if quick else 1800
scene.render.resolution_y = 900 if quick else 1350
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.image_settings.color_depth = '8'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = 0
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.9, 0.93, 1, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.10

assets = bpy.data.collections.new('SILOAD Silo Unit detailed assembly')
scene.collection.children.link(assets)
studio = bpy.data.collections.new('Studio lighting and cameras')
scene.collection.children.link(studio)


def move(obj, collection=assets):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


cache = {}


def material(name, color, metallic=0, rough=0.35, grain=False):
    if name in cache:
        return cache[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = rough
    if grain:
        noise = m.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 6000
        noise.inputs['Detail'].default_value = 2
        bump = m.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.11
        bump.inputs['Distance'].default_value = 0.0000025
        m.node_tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    cache[name] = m
    return m


green = material('Matte black soldermask', (0.006, 0.008, 0.011), 0, 0.44, True)
green.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.2
hx_green = material('HX711 emerald soldermask', (0.008, 0.055, 0.028), 0, 0.40, True)
black = material('Moulded graphite polymer', (0.012, 0.015, 0.019), 0, 0.38, True)
silver = material('Brushed nickel', (0.58, 0.63, 0.69), 0.92, 0.26, True)
gold = material('Gold plated contacts', (0.72, 0.46, 0.15), 0.88, 0.22)
ink = material('Warm white silkscreen', (0.87, 0.91, 0.88), 0, 0.55)
laser = material('Laser marking charcoal', (0.045, 0.052, 0.058), 0.15, 0.53)
tan = material('Ceramic dielectric', (0.30, 0.19, 0.08), 0, 0.49)
yellow = material('Header insulator warm yellow', (0.83, 0.55, 0.025), 0, 0.33)


def cad_material(role, part):
    c = part['color']
    r, g, b = c
    name = part['name']
    if role == 'carrier' and name.endswith('_PCB'):
        return green
    if role == 'carrier' and name.endswith('_pad'):
        return gold
    if role == 'wio' and 'V1.0_PCB' in name:
        return green
    if role == 'xiao' and name == 'SOLID' and max(c) - min(c) < 0.01 and r < 0.05:
        return green
    if b > r * 2.5 and b > g * 2:
        return material('Blue electrolytic sleeve', (0.012, 0.065, 0.23), 0.15, 0.27)
    if r > 0.65 and g > 0.35 and b < 0.42:
        return gold
    if max(c) - min(c) < 0.08 and max(c) > 0.15:
        return silver
    if max(c) < 0.12:
        return black
    return material('CAD ' + str(tuple(c)), c, 0, 0.4)


def mesh_obj(name, vertices, triangles, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([[v * MM for v in pt] for pt in vertices], [], triangles)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    assets.objects.link(obj)
    obj.data.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = True
    return obj


def load(role, transform):
    data = json.loads((MESHES / (role + '.json')).read_text())
    for i, part in enumerate(data['parts']):
        mesh_obj(
            role + ' | ' + part['name'] + ' ' + str(i),
            [transform(*v) for v in part['vertices']],
            part['triangles'],
            cad_material(role, part),
        )


def cube(name, loc, size, mat, bevel=0.05):
    bpy.ops.mesh.primitive_cube_add(size=1, location=Vector(loc) * MM)
    o = move(bpy.context.object)
    o.name = name
    o.dimensions = Vector(size) * MM
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod = o.modifiers.new('Machined edge softness', 'BEVEL')
        mod.width = bevel * MM
        mod.segments = 3
        o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return o


def cylinder(name, loc, radius, depth, mat, vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius * MM, depth=depth * MM, location=Vector(loc) * MM)
    o = move(bpy.context.object)
    o.name = name
    o.data.materials.append(mat)
    bevel = o.modifiers.new('Edge rounding', 'BEVEL')
    bevel.width = 0.05 * MM
    bevel.segments = 3
    o.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return o


font_path = Path(r'C:\Windows\Fonts\consola.ttf')
font = bpy.data.fonts.load(str(font_path)) if font_path.exists() else None


def text(body, loc, size, mat=ink, angle=0, name=None):
    data = bpy.data.curves.new(name or body, 'FONT')
    data.body = body
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.size = size * MM
    data.extrude = 0.001 * MM
    if font:
        data.font = font
    o = bpy.data.objects.new(name or 'Marking | ' + body, data)
    assets.objects.link(o)
    o.location = Vector(loc) * MM
    o.rotation_euler.z = math.radians(angle)
    data.materials.append(mat)
    return o


# Carrier PCB + Seeed XIAO ESP32-S3 + Wio-SX1262 stack
load('carrier', lambda x, y, z: (x - 50, y + 50, z))
load('xiao', lambda x, y, z: (z + 18.231 + DX, x - 21.661 + DY, y + 10.35))
load('wio', lambda x, y, z: (x - 102.282 + DX, y + 100.983 + DY, z + 17.0))

for side, base_x in [('left', 4.5), ('right', 19.74)]:
    x = base_x + DX
    for i in range(7):
        y = -12.3 - i * 2.54 + DY
        cube('XIAO to LoRa stacking header ' + side + str(i), (x, y, 12.62), (2.45, 2.45, 2.54), black, 0.08)
        cube('XIAO to LoRa gold pin ' + side + str(i), (x, y, 13.45), (0.50, 0.50, 11.9), gold, 0.035)

details = json.loads((OUT / 'board-details.json').read_text())
for t in details['text']:
    text(t['text'], [*t['position'], 1.565], t['height'], angle=t['angle'])

if (ROOT / 'branding' / 'SiLoad-logo.json').exists():
    from logo_in_scene import apply_scene_logo

    apply_scene_logo(ROOT, assets, ink)

under_mask = material('Copper relief beneath soldermask', (0.008, 0.01, 0.013), 0, 0.48)
under_mask.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.2
for i, t in enumerate(details['tracks']):
    a = t['a']
    b = t['b']
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = math.hypot(dx, dy)
    if length > 0:
        ex = -dy / length * t['width'] / 2
        ey = dx / length * t['width'] / 2
        mesh_obj(
            'Covered copper ' + str(i),
            [
                [a[0] + ex, a[1] + ey, 1.512],
                [b[0] + ex, b[1] + ey, 1.512],
                [b[0] - ex, b[1] - ey, 1.512],
                [a[0] - ex, a[1] - ey, 1.512],
            ],
            [[0, 1, 2], [0, 2, 3]],
            under_mask,
        )

text('seeed studio', (12.1 + DX, -23.0 + DY, 20.805), 1.0, laser)
text('Wio-SX1262', (12.1 + DX, -24.7 + DY, 20.805), 0.85, laser)
text('868 / 915 MHz', (12.1 + DX, -26.2 + DY, 20.805), 0.55, laser)

# Reconstruct horizontal Heemol HX711 24-bit ADC breakout module (34x21 mm, B0C9QBS2WL) plugged into J3 (4-pin) & J4 (6-pin)
module_top = 11.7
cx = HX_CENTER[0] - 50.0
cy = -(HX_CENTER[1] - 50.0)
cube('HX711 PCB (34x21 mm)', (cx, cy, 10.9), (34.0, 21.0, 1.6), hx_green, 0.12)
# Vertical SOP-16 HX711 IC (U7) in the middle of the green board
cube('HX711 IC U7', (cx - 0.5, cy + 0.8, 12.35), (4.2, 10.0, 1.5), black, 0.06)
for p_i in range(8):
    py_pin = cy + 0.8 - 4.445 + p_i * 1.27
    cube(f'HX711 IC pin L {p_i}', (cx - 3.1, py_pin, 12.0), (1.1, 0.42, 0.5), silver, 0.02)
    cube(f'HX711 IC pin R {p_i}', (cx + 2.1, py_pin, 12.0), (1.1, 0.42, 0.5), silver, 0.02)
text('HX711', (cx - 0.5, cy + 0.8, 13.12), 0.72, ink, 90)
# SOT-23 Q2 + SMD passives on the Heemol HX711 board
cube('HX711 Q2 SOT-23', (cx + 6.5, cy - 6.8, 12.1), (2.9, 1.6, 1.0), black, 0.04)
for sx, sy, is_cap in [
    (-6.0, 5.8, True), (-6.0, -1.8, True), (-4.0, -1.8, False),
    (-1.5, -6.2, True), (2.0, -6.2, True),
    (5.5, -1.5, False), (5.5, 1.0, False),
    (5.2, 4.5, False), (7.5, 4.5, True),
]:
    cube(f'HX711 SMD {sx}_{sy}', (cx + sx, cy + sy, 12.05), (1.6, 2.4, 0.9), tan if is_cap else black, 0.03)
# Two corner mounting hole pads on the 4-pin (JP2/J3) side of the Heemol HX711 PCB
for hy in [cy + 7.2, cy - 7.2]:
    cylinder(f'HX711 mount ring {hy}', (HX_MCU_POS[0] - 50.0, hy, 10.9), 1.6, 1.64, silver, 32)
    cylinder(f'HX711 mount hole {hy}', (HX_MCU_POS[0] - 50.0, hy, 10.9), 1.1, 1.68, black, 32)
# 4-pin J3 header (VCC, SCK, DT, GND) and 6-pin J4 header (B+, B-, A+, A-, E-, E+)
for col_x, start_y, labels in [
    (HX_MCU_POS[0] - 50.0, HX_MCU_POS[1] - 50.0, ['VCC', 'SCK', 'DT', 'GND']),
    (HX_BRIDGE_POS[0] - 50.0, HX_BRIDGE_POS[1] - 50.0, ['B+', 'B-', 'A+', 'A-', 'E-', 'E+']),
]:
    for k, lbl in enumerate(labels):
        py = -(start_y + k * 2.54)
        cube(f'HX711 hdr {col_x}_{k}', (col_x, py, 12.97), (2.4, 2.4, 2.54), black, 0.07)
        cube(f'HX711 pin {col_x}_{k}', (col_x, py, 11.9), (0.64, 0.64, 7.2), gold, 0.04)
        lx = col_x - 2.3 if col_x < cx else col_x + 2.3
        text(lbl, (lx, py, module_top + 0.02), 0.50, ink, 0)

# Reconstruct horizontal U1 (CD4052BE DIP-16 IC plugged into the DIP-16 socket)
ux = (MUX_POS[0] + 8.89) - 50.0
uy = -(MUX_POS[1] - 3.81 - 50.0)
cube('CD4052BE DIP-16 Body', (ux, uy, 6.7), (19.2, 6.4, 3.2), black, 0.08)
for p_i in range(8):
    px = (MUX_POS[0] + p_i * 2.54) - 50.0
    cube(f'CD4052 pin B {p_i}', (px, uy - 3.81, 5.2), (0.5, 0.35, 3.0), silver, 0.02)
    cube(f'CD4052 pin T {p_i}', (px, uy + 3.81, 5.2), (0.5, 0.35, 3.0), silver, 0.02)
text('CD4052BE MUX', (ux, uy, 8.32), 0.78, ink, 0)

# M2.5 mounting hardware
for i, (_, mx, my) in enumerate(MOUNTING_HOLES):
    x = mx - 50
    y = 50 - my
    cylinder('M2.5 hex spacer ' + str(i), (x, y, -2.5), 2.5, 5, gold, 6)
    cylinder('M2.5 screw head ' + str(i), (x, y, 2.2), 2.25, 1.25, silver)
    cylinder('Screw hex socket ' + str(i), (x, y, 2.835), 0.9, 0.018, black, 6)

# Studio floor, softboxes, cameras
floor_mat = material('Studio warm white', (0.82, 0.84, 0.86), 0, 0.75)
bpy.ops.mesh.primitive_plane_add(size=3, location=(0.032, -0.020, -0.00508))
floor = move(bpy.context.object, studio)
floor.name = 'Seamless studio floor'
floor.data.materials.append(floor_mat)


def aim(obj, pt):
    obj.rotation_euler = (Vector(pt) * MM - obj.location).to_track_quat('-Z', 'Y').to_euler()


def area(name, position, power, size, color, shape='DISK', size_y=None):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power / 48
    data.shape = shape
    data.size = size * MM
    data.color = color
    if size_y is not None:
        data.size_y = size_y * MM
    o = bpy.data.objects.new(name, data)
    studio.objects.link(o)
    o.location = Vector(position) * MM
    aim(o, (32, -20, 8))
    return o


area('Key | large softbox', (-40, -50, 120), 22, 100, (1, 0.95, 0.88))
area('Fill | cool broad card', (110, 45, 75), 14, 90, (0.88, 0.94, 1))
area('Rim | vertical strip', (20, 75, 100), 19, 75, (1, 1, 1), 'RECTANGLE', 16)
area('Front polish card', (55, -105, 42), 6, 70, (1, 1, 1))


def camera(name, pos, target, lens=62, ortho=None):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    studio.objects.link(obj)
    obj.location = Vector(pos) * MM
    aim(obj, target)
    data.lens = lens
    data.clip_start = 0.0001
    data.clip_end = 10
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho * MM
    return obj


cameras = [
    ('hero-logo', camera('Hero camera', (108, -122, 98), (34, -22, 8), 56)),
    ('02-connectors', camera('Connector camera', (34, -128, 66), (34, -27, 7), 64)),
    ('03-detail', camera('Macro camera', (84, -84, 85), (37, -23, 11), 80)),
    ('top-logo', camera('Top camera', (34, -22, 160), (34, -22, 0), ortho=84)),
]

scene.camera = cameras[0][1]
bpy.ops.file.pack_all()
blend_path = OUT / 'SILOAD LOAD CELL REV A-studio-branded.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

bpy.ops.object.select_all(action='DESELECT')
for o in assets.objects:
    o.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=str(OUT / 'SILOAD LOAD CELL REV A-detailed-branded.glb'),
    export_format='GLB',
    use_selection=True,
    export_apply=True,
)

for name, cam in (cameras[:1] + cameras[3:] if quick else cameras):
    scene.camera = cam
    scene.render.filepath = str(OUT / f'SILOAD LOAD CELL REV A-{name}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER_COMPLETE', scene.render.filepath, flush=True)

scene.camera = cameras[0][1]
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
