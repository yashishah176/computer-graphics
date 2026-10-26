import bpy
import bmesh
import math
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 150
scene.render.fps = 24
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Punchy"


def make_material(name, color, roughness=0.5, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def shade_smooth(obj):
    for poly in obj.data.polygons:
        poly.use_smooth = True


red = make_material("Envelope_Red", (0.80, 0.05, 0.08), 0.45)
yellow = make_material("Envelope_Yellow", (0.95, 0.70, 0.05), 0.45)
wicker = make_material("Basket_Wicker", (0.35, 0.18, 0.06), 0.85)
rope = make_material("Rope", (0.55, 0.45, 0.30), 0.9)
metal = make_material("Burner_Metal", (0.30, 0.30, 0.32), 0.3)
flame = make_material("Flame", (1.0, 0.45, 0.05), 0.5, (1.0, 0.40, 0.02), 25.0)
grass = make_material("Grass", (0.12, 0.42, 0.10), 0.95)
hill_mat = make_material("Hill", (0.18, 0.50, 0.15), 0.95)
leaf = make_material("Leaves", (0.05, 0.30, 0.08), 0.9)
bark = make_material("Bark", (0.25, 0.14, 0.06), 0.9)
cloud = make_material("Cloud", (1.0, 1.0, 1.0), 1.0)
path_mat = make_material("Dirt_Path", (0.45, 0.32, 0.18), 1.0)

balloon = bpy.data.objects.new("HotAirBalloon", None)
scene.collection.objects.link(balloon)

bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=16, radius=2.0, location=(0, 0, 0))
envelope = bpy.context.active_object
envelope.name = "Envelope"
bm = bmesh.new()
bm.from_mesh(envelope.data)
for v in bm.verts:
    if v.co.z < 0:
        t = -v.co.z / 2.0
        shrink = 1.0 - 0.72 * t
        v.co.x *= shrink
        v.co.y *= shrink
        v.co.z *= 1.35
    else:
        v.co.z *= 1.10
bottom = [v for v in bm.verts if v.co.z < -2.6]
bmesh.ops.delete(bm, geom=bottom, context="VERTS")
bm.to_mesh(envelope.data)
bm.free()
envelope.data.materials.append(red)
envelope.data.materials.append(yellow)
for poly in envelope.data.polygons:
    c = poly.center
    angle = math.atan2(c.y, c.x)
    gore = int(((angle + math.pi) / (2 * math.pi)) * 16) % 16
    poly.material_index = gore % 2
shade_smooth(envelope)
envelope.modifiers.new("Subsurf", "SUBSURF").levels = 2
envelope.location = (0, 0, 4.2)
envelope.parent = balloon

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.45))
basket = bpy.context.active_object
basket.name = "Basket"
basket.scale = (0.9, 0.9, 0.9)
bpy.ops.object.transform_apply(scale=True)
bm = bmesh.new()
bm.from_mesh(basket.data)
top = [f for f in bm.faces if f.normal.z > 0.9]
inset = bmesh.ops.inset_region(bm, faces=top, thickness=0.08)
bmesh.ops.translate(bm, vec=Vector((0, 0, -0.75)), verts=list({v for f in top for v in f.verts}))
bm.to_mesh(basket.data)
bm.free()
basket.data.materials.append(wicker)
bevel = basket.modifiers.new("Bevel", "BEVEL")
bevel.width = 0.03
bevel.segments = 2
basket.parent = balloon

corners = [(0.4, 0.4), (-0.4, 0.4), (0.4, -0.4), (-0.4, -0.4)]
for i, (x, y) in enumerate(corners):
    start = Vector((x, y, 0.9))
    end = Vector((x * 1.25, y * 1.25, 1.85))
    mid = (start + end) / 2
    length = (end - start).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.025, depth=length, location=mid)
    r = bpy.context.active_object
    r.name = f"Rope_{i + 1}"
    r.rotation_mode = "QUATERNION"
    r.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(end - start)
    r.data.materials.append(rope)
    r.parent = balloon

bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.18, depth=0.25, location=(0, 0, 1.55))
burner = bpy.context.active_object
burner.name = "Burner"
burner.data.materials.append(metal)
burner.parent = balloon

bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.16, radius2=0.0, depth=0.6, location=(0, 0, 1.95))
fire = bpy.context.active_object
fire.name = "Flame"
fire.data.materials.append(flame)
shade_smooth(fire)
fire.parent = balloon

bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(grass)

bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -3.5, 0.01))
path = bpy.context.active_object
path.name = "Dirt_Path"
path.scale = (60, 1.6, 1)
path.data.materials.append(path_mat)

hills = [(-30, 40, 9, 14), (5, 48, 12, 18), (35, 42, 8, 13)]
for i, (x, y, h, r) in enumerate(hills):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=(x, y, 0))
    hill = bpy.context.active_object
    hill.name = f"Hill_{i + 1}"
    hill.scale = (r, r * 0.6, h)
    hill.data.materials.append(hill_mat)
    shade_smooth(hill)

trees = [(-9, 6), (-12, 10), (-7, 13), (10, 7), (13, 11), (8, 15), (-16, 4), (17, 5)]
for i, (x, y) in enumerate(trees):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=0.2, depth=1.2, location=(x, y, 0.6))
    trunk = bpy.context.active_object
    trunk.name = f"Trunk_{i + 1}"
    trunk.data.materials.append(bark)
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=1.1, depth=2.6, location=(x, y, 2.4))
    crown = bpy.context.active_object
    crown.name = f"Tree_{i + 1}"
    crown.data.materials.append(leaf)

cloud_groups = [(-14, 25, 16), (12, 30, 19), (2, 35, 23)]
for gi, (cx, cy, cz) in enumerate(cloud_groups):
    for j, (dx, dz, s) in enumerate([(0, 0, 2.2), (2.0, -0.3, 1.7), (-2.0, -0.4, 1.6), (0.9, 0.9, 1.5)]):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=s, location=(cx + dx, cy, cz + dz))
        puff = bpy.context.active_object
        puff.name = f"Cloud_{gi + 1}_{j + 1}"
        puff.scale.y = 0.7
        puff.data.materials.append(cloud)
        shade_smooth(puff)

world = bpy.data.worlds.new("Sky")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.16, 0.42, 0.95, 1.0)
bg.inputs["Strength"].default_value = 0.9

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 4.0
sun_data.color = (1.0, 0.95, 0.85)
sun = bpy.data.objects.new("Sun", sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(35))

fill_data = bpy.data.lights.new("Fill", type="AREA")
fill_data.energy = 2000
fill_data.size = 10
fill = bpy.data.objects.new("Fill", fill_data)
scene.collection.objects.link(fill)
fill.location = (-12, -14, 10)
fill.rotation_euler = (math.radians(60), 0, math.radians(-40))

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 38
camera = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera.location = (0, -26, 6)
target = bpy.data.objects.new("CameraTarget", None)
scene.collection.objects.link(target)
target.location = (0, 0, 5)
track = camera.constraints.new("TRACK_TO")
track.target = target
track.track_axis = "TRACK_NEGATIVE_Z"
track.up_axis = "UP_Y"

keys = [
    (1, (-10, 0, 0.0), 0),
    (30, (-9, 0, 0.0), 0),
    (70, (-4, 2, 5.0), 4),
    (110, (3, 4, 10.0), -4),
    (150, (10, 6, 14.0), 3),
]
for frame, loc, tilt in keys:
    balloon.location = loc
    balloon.rotation_euler = (math.radians(tilt), 0, 0)
    balloon.keyframe_insert("location", frame=frame)
    balloon.keyframe_insert("rotation_euler", frame=frame)

for frame, loc in [(1, (-6, 0, 3)), (150, (4, 4, 11))]:
    target.location = loc
    target.keyframe_insert("location", frame=frame)

for frame in range(1, 151, 6):
    strength = 35.0 if (frame // 6) % 2 == 0 else 15.0
    if frame < 25:
        strength = 5.0
    bsdf = flame.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Strength"].default_value = strength
    bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=frame)
    fire.scale = (1, 1, 1.3 if strength > 20 else 0.8)
    fire.keyframe_insert("scale", frame=frame)

scene.frame_set(1)
