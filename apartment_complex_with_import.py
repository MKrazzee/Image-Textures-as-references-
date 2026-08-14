# Apartment Complex Night Scene + Imported Apartment Model
# Blender 3.x / 4.x
#
# IMPORTANT:
# 1. Download the apartment asset from the GitHub repository you provided.
# 2. Set APARTMENT_ASSET_PATH below to the local .blend or .fbx file.
# 3. Run the entire script once in a fresh Blender file.
#
# The script is intentionally lightweight:
# - no thousands of tiny lights
# - no heavy modifiers
# - simple materials
# - a small number of reusable meshes
#
# If the asset path is left empty, the scene still builds and tells you
# exactly where to put the model.

import bpy
import os
import math
from mathutils import Vector

# ============================================================
# SETTINGS
# ============================================================

APARTMENT_ASSET_PATH = r""   # <-- PUT YOUR LOCAL .BLEND OR .FBX PATH HERE

# Example:
# APARTMENT_ASSET_PATH = r"C:\Users\Musa\Downloads\Final R .blend"

CLEAR_SCENE = True
APARTMENT_SCALE = 1.0

# Number / arrangement of imported apartment instances.
# Keep these modest for performance.
APARTMENT_POSITIONS = [
    (-18, 12, 0),
    (0, 18, 0),
    (18, 12, 0),
    (-22, -5, 0),
    (22, -5, 0),
]

# ============================================================
# HELPERS
# ============================================================

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        # Only remove unused datablocks
        for block in list(datablocks):
            try:
                if block.users == 0:
                    datablocks.remove(block)
            except:
                pass


def mat(name, color, metallic=0.0, roughness=0.7, emission=None, emission_strength=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True

    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness

        if emission:
            # Blender 4.x uses "Emission Color"; older versions use "Emission"
            e = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
            if e:
                e.default_value = (*emission, 1.0)

            es = bsdf.inputs.get("Emission Strength")
            if es:
                es.default_value = emission_strength

    return m


def cube(name, location, scale, material=None, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    if material:
        o.data.materials.append(material)

    if bevel > 0:
        mod = o.modifiers.new("Small bevel", 'BEVEL')
        mod.width = bevel
        mod.segments = 1

    return o


def cyl(name, location, radius, depth, material=None, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        radius=radius,
        depth=depth,
        location=location
    )
    o = bpy.context.object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o


def uv_sphere(name, location, radius, material=None, segments=12, rings=6):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments,
        ring_count=rings,
        radius=radius,
        location=location
    )
    o = bpy.context.object
    o.name = name
    if material:
        o.data.materials.append(material)
    return o


def add_area_light(name, location, energy, color, size=4.0):
    data = bpy.data.lights.new(name=name, type='AREA')
    data.energy = energy
    data.color = color
    data.shape = 'DISK'
    data.size = size

    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    o.location = location
    return o


def add_point_light(name, location, energy, color, radius=0.2):
    data = bpy.data.lights.new(name=name, type='POINT')
    data.energy = energy
    data.color = color
    data.shadow_soft_size = radius

    o = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(o)
    o.location = location
    return o


def add_emissive_bulb(name, location, material, radius=0.06):
    return uv_sphere(name, location, radius, material)


def collection_objects(collection):
    return [o for o in collection.objects]


# ============================================================
# MATERIALS
# ============================================================

road_mat = mat("Road", (0.035, 0.045, 0.055), roughness=0.94)
sidewalk_mat = mat("Sidewalk", (0.20, 0.21, 0.22), roughness=0.9)
curb_mat = mat("Curb", (0.28, 0.29, 0.30), roughness=0.9)
white_mat = mat("Road Marking", (0.75, 0.74, 0.68), roughness=0.8)
building_bg_mat = mat("Background Buildings", (0.075, 0.085, 0.11), roughness=0.9)
roof_mat = mat("Roof", (0.055, 0.06, 0.075), roughness=0.95)
tree_mat = mat("Tree", (0.035, 0.10, 0.055), roughness=1.0)
trunk_mat = mat("Trunk", (0.12, 0.07, 0.04), roughness=1.0)
metal_mat = mat("Dark Metal", (0.08, 0.09, 0.10), metallic=0.5, roughness=0.55)
yellow_emission = mat(
    "Warm Windows",
    (0.12, 0.07, 0.025),
    roughness=0.5,
    emission=(1.0, 0.32, 0.06),
    emission_strength=3.0,
)
bulb_emission = mat(
    "Bulbs",
    (0.18, 0.11, 0.035),
    roughness=0.35,
    emission=(1.0, 0.42, 0.09),
    emission_strength=6.0,
)
red_emission = mat(
    "Tail Lights",
    (0.2, 0.02, 0.01),
    roughness=0.4,
    emission=(1.0, 0.03, 0.01),
    emission_strength=3.0,
)
blue_emission = mat(
    "Cool Sign",
    (0.01, 0.03, 0.08),
    roughness=0.5,
    emission=(0.05, 0.2, 1.0),
    emission_strength=2.0,
)

# ============================================================
# WORLD / RENDER
# ============================================================

scene = bpy.context.scene

scene.render.engine = 'BLENDER_EEVEE_NEXT'

scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 70

scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False

scene.world.color = (0.008, 0.012, 0.028)

# World nodes for dark blue night
world = scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.006, 0.012, 0.035, 1)
    bg.inputs["Strength"].default_value = 0.18

# ============================================================
# CLEAR
# ============================================================

if CLEAR_SCENE:
    clear_scene()

# ============================================================
# GROUND / ROAD
# ============================================================

cube("Main Road", (0, 0, -0.18), (38, 8.0, 0.18), road_mat)

cube("Left Sidewalk", (0, 10.0, 0), (38, 1.6, 0.12), sidewalk_mat)
cube("Right Sidewalk", (0, -10.0, 0), (38, 1.6, 0.12), sidewalk_mat)

cube("Left Curb", (0, 8.35, 0.05), (38, 0.18, 0.18), curb_mat)
cube("Right Curb", (0, -8.35, 0.05), (38, 0.18, 0.18), curb_mat)

# Road markings
for x in range(-34, 35, 6):
    cube(
        f"Lane Mark {x}",
        (x, 0, 0.01),
        (2.0, 0.07, 0.015),
        white_mat
    )

# Cross street
cube("Cross Street", (0, 24, -0.18), (11, 8, 0.18), road_mat)
cube("Cross Street Mark", (0, 24, 0.01), (2, 0.07, 0.015), white_mat)

# ============================================================
# SIMPLE BACKGROUND BUILDINGS
# ============================================================

def background_building(x, y, sx, sy, h):
    b = cube(
        "Distant Apartment",
        (x, y, h / 2),
        (sx, sy, h / 2),
        building_bg_mat
    )

    # A few large glowing window bands rather than dozens of tiny lights
    rows = min(4, max(2, int(h / 4)))
    for r in range(rows):
        z = 2.2 + r * 4.0
        if z > h - 1:
            continue

        for xx in (-sx * 0.45, 0, sx * 0.45):
            cube(
                "Window Band",
                (x + xx, y - sy - 0.02, z),
                (sx * 0.13, 0.03, 0.65),
                yellow_emission
            )

    return b


background_building(-31, 22, 5, 3, 15)
background_building(31, 22, 5, 3, 18)
background_building(-33, -19, 6, 3, 17)
background_building(33, -19, 6, 3, 14)
background_building(-10, 28, 4, 3, 12)
background_building(10, 28, 4, 3, 13)

# ============================================================
# IMPORT APARTMENT MODEL
# ============================================================

imported_collection_objects = []

def import_blend(filepath):
    before = set(bpy.data.objects)

    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        data_to.objects = data_from.objects

    for obj in data_to.objects:
        if obj is None:
            continue

        bpy.context.collection.objects.link(obj)

    after = set(bpy.data.objects)
    new_objs = list(after - before)

    return [o for o in new_objs if o.type in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}]


def import_fbx(filepath):
    before = set(bpy.data.objects)

    try:
        bpy.ops.import_scene.fbx(
            filepath=filepath,
            use_custom_normals=True,
            use_image_search=True
        )
    except Exception as e:
        print("FBX import failed:", e)
        return []

    after = set(bpy.data.objects)
    return list(after - before)


def import_3ds(filepath):
    before = set(bpy.data.objects)

    try:
        bpy.ops.import_scene.autodesk_3ds(filepath=filepath)
    except Exception as e:
        print("3DS import failed:", e)
        return []

    after = set(bpy.data.objects)
    return list(after - before)


def import_apartment_asset(filepath):
    if not filepath:
        print("\nNo apartment asset path supplied.")
        print("Set APARTMENT_ASSET_PATH near the top of this script.")
        return []

    filepath = os.path.abspath(os.path.expanduser(filepath))

    if not os.path.exists(filepath):
        print("\nApartment asset not found:")
        print(filepath)
        return []

    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".blend":
        return import_blend(filepath)
    elif ext == ".fbx":
        return import_fbx(filepath)
    elif ext == ".3ds":
        return import_3ds(filepath)
    else:
        print("Unsupported apartment file:", ext)
        return []


def duplicate_apartment(source_objs, location, scale=1.0):
    if not source_objs:
        return []

    duplicates = []

    # Duplicate linked meshes so memory stays much lower than full copies.
    for src in source_objs:
        try:
            dup = src.copy()
            if src.data:
                dup.data = src.data

            bpy.context.collection.objects.link(dup)

            dup.location += Vector(location)
            dup.scale = (
                src.scale.x * scale,
                src.scale.y * scale,
                src.scale.z * scale
            )

            duplicates.append(dup)
        except Exception as e:
            print("Could not duplicate object:", src.name, e)

    return duplicates


source_objects = import_apartment_asset(APARTMENT_ASSET_PATH)

if source_objects:
    # Find bounding box center so the imported building can be placed cleanly.
    min_v = Vector((999999, 999999, 999999))
    max_v = Vector((-999999, -999999, -999999))

    for obj in source_objects:
        if obj.type != 'MESH':
            continue

        for corner in obj.bound_box:
            world_corner = obj.matrix_world @ Vector(corner)
            min_v.x = min(min_v.x, world_corner.x)
            min_v.y = min(min_v.y, world_corner.y)
            min_v.z = min(min_v.z, world_corner.z)

            max_v.x = max(max_v.x, world_corner.x)
            max_v.y = max(max_v.y, world_corner.y)
            max_v.z = max(max_v.z, world_corner.z)

    center = (min_v + max_v) / 2.0

    # Put source model near first position.
    first_pos = Vector(APARTMENT_POSITIONS[0])

    for obj in source_objects:
        obj.location -= center

    # Move source model
    for obj in source_objects:
        obj.location += first_pos

    # Additional linked duplicates
    for pos in APARTMENT_POSITIONS[1:]:
        duplicate_apartment(source_objects, pos, APARTMENT_SCALE)

    imported_collection_objects = source_objects

    print(f"Imported apartment asset with {len(source_objects)} objects.")
else:
    print("No apartment model imported. Scene will use background buildings.")

# ============================================================
# STREET TREES
# ============================================================

def add_tree(x, y):
    cyl("Tree Trunk", (x, y, 1.4), 0.22, 2.8, trunk_mat, 10)

    uv_sphere("Tree Crown", (x, y, 3.5), 1.45, tree_mat, 10, 6)
    uv_sphere("Tree Crown", (x + 0.7, y, 3.2), 1.0, tree_mat, 10, 6)
    uv_sphere("Tree Crown", (x - 0.7, y, 3.2), 0.9, tree_mat, 10, 6)


for x in (-28, -18, -8, 8, 18, 28):
    add_tree(x, 11.2)
    add_tree(x + 3, -11.2)

# ============================================================
# BENCHES / PLANTERS / BINS
# ============================================================

def add_bench(x, y, rotation=0):
    seat = cube("Bench Seat", (x, y, 0.85), (1.3, 0.35, 0.12), metal_mat, 0.04)

    leg1 = cube("Bench Leg", (x - 0.85, y, 0.45), (0.12, 0.25, 0.35), metal_mat)
    leg2 = cube("Bench Leg", (x + 0.85, y, 0.45), (0.12, 0.25, 0.35), metal_mat)

    back = cube("Bench Back", (x, y + 0.3, 1.2), (1.3, 0.10, 0.55), metal_mat)

    for o in (seat, leg1, leg2, back):
        o.rotation_euler[2] = rotation


def add_bin(x, y):
    cube("Bin", (x, y, 0.55), (0.45, 0.45, 0.55), metal_mat, 0.06)


def add_planter(x, y):
    cube("Planter", (x, y, 0.35), (0.65, 0.65, 0.35), curb_mat, 0.05)
    uv_sphere("Planter Bush", (x, y, 0.95), 0.65, tree_mat, 10, 6)


add_bench(-14, 10.8)
add_bench(14, -10.8, math.radians(180))

add_bin(-5, 10.9)
add_bin(5, -10.9)

add_planter(-2, 10.9)
add_planter(2, -10.9)

# ============================================================
# PARKED CARS - SIMPLE LOW POLY
# ============================================================

car_body_mat = mat("Car Paint", (0.07, 0.08, 0.10), metallic=0.4, roughness=0.5)
window_mat = mat("Car Windows", (0.015, 0.02, 0.03), metallic=0.1, roughness=0.35)


def add_car(x, y, rotation=0):
    body = cube("Parked Car", (x, y, 0.62), (1.65, 0.72, 0.32), car_body_mat, 0.12)
    cabin = cube("Car Cabin", (x - 0.15, y, 1.00), (0.9, 0.62, 0.28), car_body_mat, 0.10)

    wind = cube("Car Windows", (x - 0.15, y - 0.01, 1.02), (0.68, 0.52, 0.17), window_mat)

    tail1 = cube("Tail Light", (x + 1.62, y - 0.48, 0.65), (0.08, 0.07, 0.08), red_emission)
    tail2 = cube("Tail Light", (x + 1.62, y + 0.48, 0.65), (0.08, 0.07, 0.08), red_emission)

    for o in (body, cabin, wind, tail1, tail2):
        o.rotation_euler[2] = rotation


add_car(-11, -5.9)
add_car(10, 5.9, math.radians(180))
add_car(27, -5.9)

# ============================================================
# STREET LAMPS
# ============================================================

lamp_positions = [
    (-28, 8.8),
    (-14, -8.8),
    (0, 8.8),
    (14, -8.8),
    (28, 8.8),
]


def add_street_lamp(x, y):
    pole = cyl("Lamp Pole", (x, y, 3.0), 0.09, 6.0, metal_mat, 10)

    arm = cube("Lamp Arm", (x + 0.45, y, 5.65), (0.45, 0.07, 0.07), metal_mat)
    bulb = add_emissive_bulb("Lamp Bulb", (x + 0.83, y, 5.52), bulb_emission, 0.11)

    add_point_light(
        "Lamp Light",
        (x + 0.83, y, 5.35),
        65,
        (1.0, 0.28, 0.08),
        0.5
    )


for p in lamp_positions:
    add_street_lamp(*p)

# ============================================================
# HANGING LIGHT STRING
# ============================================================

# This uses only a few bulbs.
for x in range(-24, 25, 4):
    bulb = add_emissive_bulb(
        "Hanging Bulb",
        (x, 7.4, 4.8 + 0.20 * math.sin(x)),
        bulb_emission,
        0.075
    )

    add_point_light(
        "Hanging Bulb Light",
        bulb.location,
        18,
        (1.0, 0.30, 0.07),
        0.18
    )

# ============================================================
# EXTRA RESIDENTIAL DETAILS
# ============================================================

# Mailbox clusters
for x in (-20, 20):
    cube("Mailbox Base", (x, 9.7, 0.75), (0.65, 0.35, 0.75), metal_mat, 0.05)
    for z in (0.5, 1.0):
        cube("Mailbox Door", (x + 0.67, 9.7, z), (0.05, 0.28, 0.18), metal_mat)

# Small utility boxes
for x in (-7, 7):
    cube("Utility Box", (x, -9.6, 0.7), (0.45, 0.35, 0.7), metal_mat, 0.04)

# Fences on ends of sidewalks
for y in (-13.0, 13.0):
    for x in range(-30, 31, 4):
        cyl("Fence Post", (x, y, 0.7), 0.05, 1.4, metal_mat, 8)
    cube("Fence Rail", (0, y, 1.1), (30, 0.05, 0.05), metal_mat)

# ============================================================
# SIMPLE SIGN
# ============================================================

sign_post = cyl("Sign Post", (0, 9.6, 1.5), 0.06, 3.0, metal_mat, 8)
sign = cube("Apartment Sign", (0, 9.6, 3.0), (1.3, 0.08, 0.55), blue_emission, 0.04)

# ============================================================
# CAMERA
# ============================================================

cam_data = bpy.data.cameras.new("Main Camera")
cam = bpy.data.objects.new("Main Camera", cam_data)
bpy.context.collection.objects.link(cam)

cam.location = (-28, -25, 7.5)
cam.rotation_euler = (math.radians(72), 0, math.radians(-43))

scene.camera = cam

# Camera target
target = Vector((0, 5, 2.4))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
cam.data.lens = 34

# ============================================================
# MOON / SKY LIGHT
# ============================================================

add_area_light(
    "Soft Moon Fill",
    (0, 0, 18),
    350,
    (0.18, 0.25, 0.65),
    size=20
)

# ============================================================
# COLOR MANAGEMENT
# ============================================================

try:
    scene.view_settings.look = 'AgX - Medium High Contrast'
except:
    pass

# ============================================================
# SAVE
# ============================================================

save_path = os.path.join(
    os.path.expanduser("~"),
    "Desktop",
    "Apartment_Complex_Night_Imported.blend"
)

try:
    bpy.ops.wm.save_as_mainfile(filepath=save_path)
    print("\nSaved scene to:")
    print(save_path)
except Exception as e:
    print("\nCould not auto-save:", e)

print("\n==============================================")
print("APARTMENT COMPLEX SCENE COMPLETE")
print("==============================================")
if source_objects:
    print("Imported apartment model successfully.")
else:
    print("Apartment model was NOT imported.")
    print("Set APARTMENT_ASSET_PATH and run again.")
print("Objects kept intentionally lightweight.")
print("==============================================")
