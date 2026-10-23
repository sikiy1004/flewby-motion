"""FLEW BY — Acrylic Light Display: photorealistic visualization.

Builds the whole scene procedurally (acrylic box, Afzal Orange packages,
physics-based random arrangement, back LED, gray wall, cameras) and renders
the four deliverable views with Cycles.

Run with either the Blender binary or the `bpy` Python module:

    blender -b -P scripts/create_display.py -- [options]
    python scripts/create_display.py [options]          # pip install bpy

Options:
    --preview           low-resolution, low-sample test renders (output/preview/)
    --views a,b,...     subset of: front, angle, detail, wall   (default: all)
    --samples N         override Cycles samples
    --relayout          ignore the cached arrangement and re-run the physics drop
    --no-render         build and save the .blend only

All dimensions are in millimetres in the PARAMETERS section and converted to
metres (Blender Metric, scale 1.0) when the geometry is built.
"""

import hashlib
import json
import math
import os
import random
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

# ============================================================================
# PARAMETERS — everything not fixed by the brief is a variable here.
# ============================================================================

MM = 0.001  # mm -> m

# --- 02. Acrylic box (outer dimensions are fixed by the brief) --------------
# v1: 350 x 100 x 80 (8 packages), v2: 600 x 150 x 120 (28 packages),
# v3: 450 x 330 x 70 (current).
BOX_W = 450.0           # outer width
BOX_H = 330.0           # outer height
BOX_D = 70.0            # outer depth (front face to wall)
ACRYLIC_T = 3.0         # sheet thickness (provisional)
ACRYLIC_EDGE_BEVEL = 0.3  # polished edge radius

# Back structure (provisional): opaque back plate against the wall, an LED
# panel module in front of it, then the display chamber.
BACK_PLATE_T = 3.0
BACK_PLATE_COLOR = (0.80, 0.80, 0.80)  # white opal acrylic, linear RGB
LED_MODULE_T = 8.0      # edge-lit LED panel incl. light guide plate
LED_FACE_INSET = 2.0    # emitting area inset from the chamber walls

# --- 03. Packages ------------------------------------------------------------
# Three kinds of empty package, mixed in equal numbers. size = (width,
# height, depth) in mm with the print upright. Each face of the texture is
# either a quad in the reference photo (pixels, origin top-left; corners
# top-left, top-right, bottom-right, bottom-left as printed), the name of
# another face to copy, or ("fill", face, y0, y1, x0, x1): a plain paper
# colour sampled from that region (fractions) of another face.
PACK_TYPES = [
    dict(key="afzal_orange", label="Afzal Orange 50 g",
         size=(55.0, 85.0, 22.0),          # provisional, not measured
         ref="afzal_reference.png",
         faces={"front": [(167, 42), (577, 80), (577, 821), (170, 866)],
                "left": [(81, 57), (167, 42), (170, 866), (83, 852)],
                "back": "front", "right": "left",
                "top": ("fill", "front", 0.04, 0.09, 0.3, 0.9),
                "bottom": ("fill", "left", 0.55, 0.65, 0.0, 1.0)}),
    dict(key="darkside_cola", label="Darkside Cola 100 g",
         size=(90.0, 107.0, 20.0),         # measured
         ref="darkside_cola_reference.png",
         faces={"front": [(915, 477), (1395, 1007), (520, 1530), (120, 915)],
                "right": [(1395, 1007), (1395, 1094), (540, 1610), (520, 1530)],
                "back": "front", "left": "right",
                # top/bottom are too foreshortened in the photo: plain fill
                "top": ("fill", "right", 0.02, 0.08, 0.2, 0.8),
                "bottom": ("fill", "right", 0.02, 0.08, 0.2, 0.8)}),
    dict(key="alfakher_two_apples", label="Al Fakher Two Apples",
         size=(55.0, 88.0, 22.0),          # cigarette-pack size (88x55x22)
         ref="alfakher_two_apples_reference.png",
         faces={"front": [(887, 592), (1285, 907), (607, 1450), (240, 1065)],
                "right": [(1285, 907), (1282, 997), (635, 1547), (607, 1450)],
                "back": "front", "left": "right",
                "top": ("fill", "right", 0.02, 0.08, 0.2, 0.8),
                "bottom": ("fill", "right", 0.02, 0.08, 0.2, 0.8)}),
]
PACK_SIZES = {t["key"]: t["size"] for t in PACK_TYPES}
PACK_EDGE_BEVEL = 0.6
TEX_PX_PER_MM = 12      # atlas resolution

# --- 04. Random arrangement -------------------------------------------------
SEED = 7
MAX_PACKS = 80          # upper bound; the fill usually stops earlier
CLEARANCE = 1.0         # min gap to every acrylic wall (mm)
PACK_FRICTION = 0.65
PACK_RESTITUTION = 0.05
PLACE_GAP = 0.6         # gap between packages when placing, before settling (mm)
TILT_NEEDS_SUPPORT = 6  # deg; steeper packages must be propped by a neighbour
ROW_FAILS = 40          # consecutive misses before moving to the next row
# Packages are placed by hand, back row first, then settled with physics.
# Orientation families:
#   front_upright  print facing the viewer, standing
#   leaning_back   print facing the viewer, leaning back against the LED wall
#   front_on_side  print facing the viewer, on its long edge, tilted
#   side_view      narrow side facing the viewer
#   flat           lying on its face (edge visible from the front)
#   tumbled        any rotation that fits the chamber
# Rows are spread over the usable depth (one per ~26 mm, back to front),
# followed by fill passes over the whole depth for what is left on top.
ROW_PITCH = 26.0        # mm of depth per row of packages
ROW_WEIGHTS = {
    "back": {"front_upright": 0.25, "leaning_back": 0.20, "front_on_side": 0.30,
             "side_view": 0.10, "tumbled": 0.15},
    "middle": {"front_upright": 0.25, "front_on_side": 0.30, "side_view": 0.15,
               "flat": 0.10, "tumbled": 0.20},
    "front": {"front_upright": 0.25, "front_on_side": 0.40, "side_view": 0.10,
              "flat": 0.10, "tumbled": 0.15},
    "fill": {"flat": 0.20, "front_on_side": 0.35, "front_upright": 0.15,
             "side_view": 0.05, "tumbled": 0.25},
}
FILL_PASSES = 4
LAYOUT_ROUNDS = 6       # place -> settle rounds (toppled packages free room)

# --- Logo: black cut vinyl on the front panel --------------------------------
LOGO_IMAGE = "flewby_logo.png"   # in assets/; skipped if the file is missing
LOGO_WIDTH = 200.0      # mm, height follows the artwork's aspect
LOGO_OFFSET = (0.0, 0.0)  # mm from the centre of the front panel (x right, z up)
LOGO_COLOR = (0.012, 0.012, 0.012)  # black cast vinyl, linear RGB
LOGO_ROUGHNESS = 0.35   # semi-gloss vinyl

# --- 05. Lighting -----------------------------------------------------------
LED_TEMPERATURE_K = 5000.0
LED_POWER_PER_M2 = 65.0  # area-light watts per m² of LED panel (tuned)
LED_EDGE_GLOW = 4.0     # light leaking from the LED panel edge (emission)
AMBIENT_STRENGTH = 0.3  # dim shop ambience (world); 0 = LED only
EXPOSURE = 0.0

# --- 06. Wall / installation ------------------------------------------------
MOUNT_CENTER_Z = 1450.0  # height of the display centre above the floor
WALL_COLOR = (0.27, 0.27, 0.265)   # linear RGB, mid-gray matte
WALL_SIZE = (6000.0, 3200.0)

# --- 08. Rendering ----------------------------------------------------------
RES_X, RES_Y = 1920, 1080
SAMPLES_FINAL = 256
SAMPLES_PREVIEW = 32
PREVIEW_SCALE = 50      # percent

# ============================================================================

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")
OUTPUT = os.path.join(ROOT, "output")
BLEND_DIR = os.path.join(ROOT, "blend")
TEXTURES = os.path.join(ASSETS, "textures")
LAYOUT_CACHE = os.path.join(ASSETS, "layout_cache.json")
BLEND_FILE = os.path.join(BLEND_DIR, "flew_by_acrylic_display.blend")

VIEWS = {
    "front": "01_front_view.png",
    "angle": "02_angle_view.png",
    "detail": "03_detail_view.png",
    "wall": "04_wall_installation.png",
}

# Derived chamber dimensions (display-local frame, metres).
# Local frame: origin at the centre of the outer volume, X = width,
# Y = depth (front at -Y, wall at +Y), Z = up.
HW, HH, HD = BOX_W / 2 * MM, BOX_H / 2 * MM, BOX_D / 2 * MM
T = ACRYLIC_T * MM
IN_X = HW - T                                  # inner half-width
IN_Z = HH - T                                  # inner half-height
FRONT_IN_Y = -HD + T                           # inner face of front panel
BACK_PLATE_Y = HD - BACK_PLATE_T * MM          # front face of back plate
LED_FACE_Y = BACK_PLATE_Y - LED_MODULE_T * MM  # emitting face of LED module


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    opts = {"preview": False, "views": list(VIEWS), "samples": None,
            "relayout": False, "render": True}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--preview":
            opts["preview"] = True
        elif a == "--views":
            i += 1
            opts["views"] = [v.strip() for v in argv[i].split(",") if v.strip()]
        elif a == "--samples":
            i += 1
            opts["samples"] = int(argv[i])
        elif a == "--relayout":
            opts["relayout"] = True
        elif a == "--no-render":
            opts["render"] = False
        i += 1
    return opts


# ----------------------------------------------------------------------------
# Scene setup
# ----------------------------------------------------------------------------

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "FlewBy_AcrylicDisplay"
    us = scene.unit_settings
    us.system = "METRIC"
    us.scale_length = 1.0
    us.length_unit = "MILLIMETERS"
    return scene


def new_collection(name, parent=None):
    coll = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(coll)
    return coll


def link(obj, coll):
    coll.objects.link(obj)
    return obj


def box_mesh(name, size, center=(0, 0, 0)):
    """Axis-aligned cuboid mesh, size/center in metres."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0] + center[0],
                       v.co.y * size[1] + center[1],
                       v.co.z * size[2] + center[2]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def add_bevel(obj, width, segments=3):
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.harden_normals = False
    for p in obj.data.polygons:
        p.use_smooth = True
    if hasattr(obj.data, "set_sharp_from_angle"):
        obj.data.set_sharp_from_angle(angle=math.radians(30))
    return mod


# ----------------------------------------------------------------------------
# Materials
# ----------------------------------------------------------------------------

def principled(mat):
    mat.use_nodes = True
    nt = mat.node_tree
    return nt, nt.nodes.get("Principled BSDF"), nt.nodes.get("Material Output")


def set_input(node, names, value):
    for n in (names if isinstance(names, (list, tuple)) else [names]):
        if n in node.inputs:
            node.inputs[n].default_value = value
            return


def mat_acrylic():
    """Clear cast acrylic (PMMA). Shadow rays pass straight through the thin
    flat sheets (physically ~ correct for 3 mm, avoids caustic noise)."""
    mat = bpy.data.materials.new("Acrylic_Clear")
    nt, bsdf, out = principled(mat)
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Roughness"].default_value = 0.03
    bsdf.inputs["IOR"].default_value = 1.49
    set_input(bsdf, ["Transmission Weight", "Transmission"], 1.0)
    set_input(bsdf, ["Coat Weight", "Clearcoat"], 0.0)
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs[0])
    nt.links.new(bsdf.outputs[0], mix.inputs[1])
    nt.links.new(transparent.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def mat_simple(name, color, rough=0.5, metallic=0.0, spec=0.5):
    mat = bpy.data.materials.new(name)
    nt, bsdf, out = principled(mat)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    set_input(bsdf, ["Specular IOR Level", "Specular"], spec)
    return mat


def mat_led_edge():
    """Edge of the LED panel's light-guide plate: part of the same LED unit,
    it leaks a little light sideways (through the clear side panels and
    onto the wall)."""
    mat = bpy.data.materials.new("LED_LightGuide_Edge")
    nt, bsdf, out = principled(mat)
    bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1)
    bb = nt.nodes.new("ShaderNodeBlackbody")
    bb.inputs["Temperature"].default_value = LED_TEMPERATURE_K
    nt.links.new(bb.outputs["Color"], bsdf.inputs["Emission Color"])
    set_input(bsdf, ["Emission Strength"], LED_EDGE_GLOW)
    return mat


def mat_wall():
    mat = bpy.data.materials.new("Wall_GrayMatte")
    nt, bsdf, out = principled(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    # large-scale tonal variation of the paint
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 3.0
    n1.inputs["Detail"].default_value = 4.0
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*[c * 0.93 for c in WALL_COLOR], 1)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (*[c * 1.05 for c in WALL_COLOR], 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    # fine plaster / roller texture
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 900.0
    n2.inputs["Detail"].default_value = 8.0
    n2.inputs["Roughness"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.0005
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.9
    set_input(bsdf, ["Specular IOR Level", "Specular"], 0.25)
    return mat


def mat_package(name, atlas):
    """Printed paperboard: satin-matte varnish over the print."""
    mat = bpy.data.materials.new(name)
    nt, bsdf, out = principled(mat)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = atlas
    tex.interpolation = "Cubic"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.42
    set_input(bsdf, ["Specular IOR Level", "Specular"], 0.45)
    # paper grain
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4000.0
    noise.inputs["Detail"].default_value = 2.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.04
    bump.inputs["Distance"].default_value = 0.0002
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


# ----------------------------------------------------------------------------
# 03. Package texture atlas from the reference photo
# ----------------------------------------------------------------------------

def homography(src, dst):
    """3x3 H with dst ~ H @ src (4 point DLT)."""
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, vt = np.linalg.svd(np.asarray(A, float))
    return vt[-1].reshape(3, 3) / vt[-1, -1]


def warp_quad(img, quad, out_w, out_h, inset=2.5):
    """Rectify a quadrilateral of img (H,W,C top-down) to out_w x out_h."""
    c = np.mean(quad, axis=0)
    q = [tuple(np.asarray(p) + inset * (c - np.asarray(p)) /
               np.linalg.norm(c - np.asarray(p))) for p in quad]
    rect = [(0, 0), (out_w - 1, 0), (out_w - 1, out_h - 1), (0, out_h - 1)]
    H = homography(rect, q)
    ys, xs = np.mgrid[0:out_h, 0:out_w].astype(float)
    pts = np.stack([xs.ravel(), ys.ravel(), np.ones(xs.size)])
    sx, sy, sw = H @ pts
    sx, sy = sx / sw, sy / sw
    h, w = img.shape[:2]
    sx = np.clip(sx, 0, w - 1.001)
    sy = np.clip(sy, 0, h - 1.001)
    x0, y0 = np.floor(sx).astype(int), np.floor(sy).astype(int)
    fx, fy = (sx - x0)[:, None], (sy - y0)[:, None]
    p = (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x0 + 1] * fx * (1 - fy) +
         img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x0 + 1] * fx * fy)
    return p.reshape(out_h, out_w, img.shape[2])


def paper_fill(h, w, color, rng):
    base = np.ones((h, w, 3)) * np.asarray(color)
    grad = np.linspace(1.03, 0.95, h)[:, None, None]
    grain = 1 + rng.normal(0, 0.012, (h, w, 1))
    return np.clip(base * grad * grain, 0, 1)


def atlas_layout(size):
    """Pixel rectangles (x, y, w, h; top-down) of each face in the atlas."""
    s = TEX_PX_PER_MM
    fw, fh, fd = (round(v * s) for v in size)
    pad = 8
    rects = {
        "front": (0, 0, fw, fh),
        "back": (fw + pad, 0, fw, fh),
        "left": (2 * (fw + pad), 0, fd, fh),
        "right": (2 * (fw + pad) + fd + pad, 0, fd, fh),
        "top": (0, fh + pad, fw, fd),
        "bottom": (fw + pad, fh + pad, fw, fd),
    }
    W = 2 * (fw + pad) + 2 * (fd + pad)
    H = fh + pad + fd
    return rects, W, H


def build_atlas(pt):
    """Rectify the reference photo of a package type into a 6-face texture
    atlas (numpy only, so it also runs inside the stock Blender Python)."""
    ref = bpy.data.images.load(os.path.join(ASSETS, pt["ref"]))
    w, h = ref.size
    px = np.empty(w * h * 4, np.float32)
    ref.pixels.foreach_get(px)
    img = px.reshape(h, w, 4)[::-1, :, :3].astype(float)  # top-down
    bpy.data.images.remove(ref)

    rects, AW, AH = atlas_layout(pt["size"])
    atlas = np.zeros((AH, AW, 3))
    rng = np.random.default_rng(SEED)
    tiles = {}

    def put(name, tile):
        x, y, tw, th = rects[name]
        atlas[y:y + th, x:x + tw] = tile
        # bleed edge pixels into the padding to avoid seams with mipmaps
        atlas[y:y + th, x + tw:x + tw + 8] = tile[:, -1:]
        atlas[y + th:y + th + 8, x:x + tw] = tile[-1:, :]
        tiles[name] = tile

    # photographed faces first, then copies and plain fills. Faces that are
    # not in the photo (e.g. the back) reuse the closest visible artwork.
    specs = pt["faces"]
    order = sorted(specs, key=lambda f: (not isinstance(specs[f], list),
                                         isinstance(specs[f], tuple)))
    for name in order:
        spec = specs[name]
        _, _, tw, th = rects[name]
        if isinstance(spec, list):
            put(name, warp_quad(img, spec, tw, th))
        elif isinstance(spec, str):
            put(name, tiles[spec])  # same-sized face (back/front, left/right)
        else:
            _, src, y0, y1, x0, x1 = spec
            t = tiles[src]
            th0, tw0 = t.shape[:2]
            col = np.median(t[int(th0 * y0):int(th0 * y1),
                              int(tw0 * x0):int(tw0 * x1)].reshape(-1, 3), 0)
            put(name, paper_fill(th, tw, col, rng))

    os.makedirs(TEXTURES, exist_ok=True)
    out = bpy.data.images.new(pt["key"] + "_atlas", AW, AH, alpha=False)
    rgba = np.concatenate([atlas, np.ones((AH, AW, 1))], axis=2)[::-1]
    out.pixels.foreach_set(rgba.astype(np.float32).ravel())
    out.filepath_raw = os.path.join(TEXTURES, pt["key"] + "_atlas.png")
    out.file_format = "PNG"
    out.save()
    out.colorspace_settings.name = "sRGB"
    return out


def package_mesh(pt):
    """Package box, print facing -Y, UV-mapped onto its atlas."""
    rects, AW, AH = atlas_layout(pt["size"])
    w, h, d = (v / 2 * MM for v in pt["size"])
    faces = {  # BL, BR, TR, TL as seen from outside, printed upright
        "front": [(-w, -d, -h), (w, -d, -h), (w, -d, h), (-w, -d, h)],
        "back": [(w, d, -h), (-w, d, -h), (-w, d, h), (w, d, h)],
        "left": [(-w, d, -h), (-w, -d, -h), (-w, -d, h), (-w, d, h)],
        "right": [(w, -d, -h), (w, d, -h), (w, d, h), (w, -d, h)],
        "top": [(-w, -d, h), (w, -d, h), (w, d, h), (-w, d, h)],
        "bottom": [(-w, d, -h), (w, d, -h), (w, -d, -h), (-w, -d, -h)],
    }
    bm = bmesh.new()
    verts = {}
    uv = bm.loops.layers.uv.new("UVMap")
    for name, corners in faces.items():
        vs = []
        for c in corners:
            if c not in verts:
                verts[c] = bm.verts.new(c)
            vs.append(verts[c])
        f = bm.faces.new(vs)
        x, y, tw, th = rects[name]
        u0, u1 = (x + 0.5) / AW, (x + tw - 0.5) / AW
        v0, v1 = 1 - (y + th - 0.5) / AH, 1 - (y + 0.5) / AH
        for loop, (u, v) in zip(f.loops, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]):
            loop[uv].uv = (u, v)
    bm.normal_update()
    me = bpy.data.meshes.new(pt["key"])
    bm.to_mesh(me)
    bm.free()
    return me


# ----------------------------------------------------------------------------
# 04. Random arrangement — rigid-body drop, one package at a time
# ----------------------------------------------------------------------------

SIM_SCALE = 10.0  # Bullet is unstable at mm scale; simulate 10x larger


def layout_key():
    keys = dict(SEED=SEED, BOX=(BOX_W, BOX_H, BOX_D, ACRYLIC_T, BACK_PLATE_T,
                LED_MODULE_T), PACK=PACK_SIZES, MAX=MAX_PACKS,
                CLEARANCE=CLEARANCE, ROWS=(ROW_PITCH, ROW_WEIGHTS, FILL_PASSES, LAYOUT_ROUNDS),
                GAP=PLACE_GAP, FAILS=ROW_FAILS, TILT=TILT_NEEDS_SUPPORT,
                PHYS=(PACK_FRICTION, PACK_RESTITUTION), v=21)
    return hashlib.sha1(json.dumps(keys, sort_keys=True).encode()).hexdigest()


def chamber_bounds():
    c = CLEARANCE * MM
    return dict(x0=-IN_X + c, x1=IN_X - c, y0=FRONT_IN_Y + c, y1=LED_FACE_Y - c,
                z0=-IN_Z, z1=IN_Z - c)


def random_orientation(rng, weights, size):
    """Pick an orientation family and jitter it; returns (family, rotation,
    in-plane tilt in degrees). Rotations that do not fit the chamber depth
    and height are re-drawn (in a shallow chamber the long axis can only run
    along the width or the height)."""
    b = chamber_bounds()
    room_y, room_z = b["y1"] - b["y0"], b["z1"] - b["z0"] - 1 * MM
    fam = rng.choices(list(weights), weights=list(weights.values()))[0]
    R = lambda axis, deg: Matrix.Rotation(math.radians(deg), 3, axis)
    j = lambda deg: rng.uniform(-deg, deg)
    flip = lambda: rng.choice([0, 180])  # either main face may face out
    for _ in range(60):
        tilt = 0.0
        if fam == "front_upright":
            tilt = j(14)
            m = R("Z", flip() + j(12)) @ R("Y", tilt) @ R("X", j(7))
        elif fam == "leaning_back":
            # top resting against the LED back wall (stable lean)
            m = R("Z", flip() + j(10)) @ R("Y", j(5)) @ R("X", -rng.uniform(18, 30))
        elif fam == "front_on_side":
            tilt = j(28)
            m = (R("Z", flip() + j(10)) @ R("Y", rng.choice([90, -90]) + tilt)
                 @ R("X", j(6)))
        elif fam == "side_view":
            m = R("Z", rng.choice([90, -90]) + j(16)) @ R("Y", j(12)) @ R("X", j(8))
        elif fam == "flat":
            m = (R("Y", j(16)) @ R("Z", rng.choice([90, -90]) + j(10))
                 @ R("X", rng.choice([90, -90]) + j(10)))
        else:
            m = Euler((rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi),
                       rng.uniform(0, 2 * math.pi)), "XYZ").to_matrix()
        cs = pack_corners(m.to_4x4(), size)
        ey = max(c.y for c in cs) - min(c.y for c in cs)
        ez = max(c.z for c in cs) - min(c.z for c in cs)
        if ey < room_y and ez < room_z:
            return fam, m, tilt
    return None, None, 0.0


def pack_corners(mat4, size):
    w, h, d = (v / 2 * MM for v in size)
    return [mat4 @ Vector((sx * w, sy * d, sz * h))
            for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]


def pack_tree(mat4, size, inflate=0.0):
    """BVH of a package's hull (real metres), optionally inflated."""
    w, h, d = (v / 2 * MM + inflate for v in size)
    verts = [mat4 @ Vector((sx * w, sy * d, sz * h))
             for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
    # cube faces over the corner order (x, y, z) -> index 4x + 2y + z
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
             (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return BVHTree.FromPolygons(verts, faces)


def lowest_free_z(rot, size, x, y, ext, trees, z_floor, z_max, step=1.0 * MM):
    """Lowest centre height at (x, y) where the package does not touch any
    placed package (sweeps upward from the floor, like placing it by hand)."""
    z = z_floor + ext[2] + 0.5 * MM
    while z <= z_max:
        m = Matrix.Translation(Vector((x, y, z))) @ rot.to_4x4()
        t = pack_tree(m, size, 0.6 * MM)
        if not any(t.overlap(o) for o in trees):
            return z
        z += step
    return None


def layout_rows(b):
    """(relative depth, family weights) per row, back to front, then the
    fill passes."""
    n = max(2, int((b["y1"] - b["y0"]) / (ROW_PITCH * MM)))
    rows = []
    for i in range(n):
        rel = 1 - (i + 0.5) / n
        kind = "back" if i == 0 else "front" if i == n - 1 else "middle"
        rows.append((rel, ROW_WEIGHTS[kind]))
    return rows + [(None, ROW_WEIGHTS["fill"])] * FILL_PASSES  # any depth


def place_by_hand(rng, b, rows, existing=()):
    """Bottom-left fill: rows from back to front; each package gets a random
    pose and is put at the left-most spot where it rests on the floor (or,
    failing that, the lowest spot on top of others). The package type is
    always the one used least so far, so the kinds stay in equal numbers.
    `existing` are the (type, pose) of packages already in the chamber."""
    placed = []
    trees = [pack_tree(m, PACK_SIZES[k], PLACE_GAP * MM * 0.5) for k, m in existing]
    counts = {k: 0 for k in PACK_SIZES}
    for k, _ in existing:
        counts[k] += 1
    gap = PLACE_GAP * MM
    room = MAX_PACKS - len(existing)
    for rel_y, weights in rows:
        misses = 0
        while misses < ROW_FAILS and len(placed) < room:
            left_to_right = rng.random() < 0.5
            least = min(counts.values())
            kind = rng.choice(sorted(k for k, n in counts.items() if n == least))
            size = PACK_SIZES[kind]
            fam, rot, tilt = random_orientation(rng, weights, size)
            if rot is None:
                misses += 1
                continue
            cs = pack_corners(rot.to_4x4(), size)
            ext = [max(abs(c[i]) for c in cs) for i in range(3)]
            ylo, yhi = b["y0"] + ext[1] + gap, b["y1"] - ext[1] - gap
            if ylo > yhi:
                misses += 1
                continue
            if rel_y is None:
                y = rng.uniform(ylo, yhi)
            else:
                y = min(max(b["y0"] + rel_y * (b["y1"] - b["y0"])
                            + rng.uniform(-5, 5) * MM, ylo), yhi)
            if fam == "leaning_back":
                y = yhi
            xs = np.arange(b["x0"] + ext[0] + gap, b["x1"] - ext[0] - gap, 2 * MM)
            if not left_to_right:
                xs = xs[::-1]
            zcap = b["z1"] - ext[2] - gap
            best = None
            if abs(tilt) > TILT_NEEDS_SUPPORT:
                # a tilted package only stays tilted when it is propped:
                # floor + a neighbour, or (on top of the pile) two neighbours
                for x in xs[::2]:
                    z = lowest_free_z(rot, size, x, y, ext, trees, b["z0"], zcap,
                                      1.0 * MM)
                    if z is None:
                        continue
                    m = Matrix.Translation(Vector((x, y, z))) @ rot.to_4x4()
                    on_floor = (min(c.z for c in pack_corners(m, size))
                                < b["z0"] + gap + 1.0 * MM)
                    t = pack_tree(m, size, gap + 1.5 * MM)
                    touching = sum(1 for o in trees if t.overlap(o))
                    if touching >= (1 if on_floor else 2):
                        best = (z, x)
                        break
                if best is None:
                    misses += 1
                    continue
            for x in ([] if best else xs):  # first floor-level spot
                z = b["z0"] + ext[2] + gap
                m = Matrix.Translation(Vector((x, y, z))) @ rot.to_4x4()
                t = pack_tree(m, size, gap)
                if not any(t.overlap(o) for o in trees):
                    best = (z, x)
                    break
            if best is None:  # otherwise the lowest stacked spot
                for x in xs[::3]:
                    z = lowest_free_z(rot, size, x, y, ext, trees, b["z0"], zcap,
                                      1.5 * MM)
                    if z is not None and (best is None or z < best[0]):
                        best = (z, x)
            if best is None:
                misses += 1
                continue
            z, x = best
            m = Matrix.Translation(Vector((x, y, z))) @ rot.to_4x4()
            placed.append((kind, fam, m))
            trees.append(pack_tree(m, size, gap * 0.5))
            counts[kind] += 1
            misses = 0
    return placed


def simulate_layout():
    """Hand-pack the chamber, then let gravity take over: every package is a
    dynamic rigid body inside the closed acrylic chamber, so tilted packages
    fall until they lean on, rest on or wedge against their neighbours. The
    stored result is the settled (static) state."""
    rng = random.Random(SEED)
    scene = bpy.context.scene
    S = SIM_SCALE
    b = chamber_bounds()

    coll = new_collection("_physics_tmp")
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.collection = bpy.data.collections.new("_rb")
    rbw.substeps_per_frame = 30
    rbw.solver_iterations = 50
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = 3000
    scene.frame_start, scene.frame_end = 1, 3000

    def add_rb(obj, kind):
        rbw.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.rigidbody.object_add(type=kind)
        obj.select_set(False)
        rb = obj.rigid_body
        rb.collision_shape = "BOX"  # centred on the object origin
        rb.friction = PACK_FRICTION
        rb.restitution = PACK_RESTITUTION
        rb.collision_margin = 0.0003 * S
        if kind == "ACTIVE":
            rb.mass = 0.03
            rb.linear_damping = 0.2
            rb.angular_damping = 0.3
        return rb

    # closed chamber (inner faces at the clearance bounds), thick convex walls
    wt = 0.03
    cx, cy, cz = [(b[k + "0"] + b[k + "1"]) / 2 for k in "xyz"]
    sx, sy, sz = [b[k + "1"] - b[k + "0"] + 2 * wt for k in "xyz"]
    walls = {
        "floor": ((sx, sy, wt), (cx, cy, b["z0"] - wt / 2)),
        "lid": ((sx, sy, wt), (cx, cy, b["z1"] + wt / 2)),
        "left": ((wt, sy, sz), (b["x0"] - wt / 2, cy, cz)),
        "right": ((wt, sy, sz), (b["x1"] + wt / 2, cy, cz)),
        "front": ((sx, wt, sz), (cx, b["y0"] - wt / 2, cz)),
        "back": ((sx, wt, sz), (cx, b["y1"] + wt / 2, cz)),
    }
    for name, (size, ctr) in walls.items():
        o = link(bpy.data.objects.new("_wall_" + name, box_mesh(
            name, [v * S for v in size])), coll)
        o.location = [c * S for c in ctr]
        add_rb(o, "PASSIVE")

    pack_me = {k: box_mesh("_pack_" + k, (w * MM * S, d * MM * S, h * MM * S))
               for k, (w, h, d) in PACK_SIZES.items()}
    packs = []  # (object, type, family)

    def real(o):
        m = o.matrix_world
        return Matrix.Translation(m.translation / S) @ m.to_3x3().normalized().to_4x4()

    def settle():
        settled, prev = False, None
        for f in range(2, 2401):
            scene.frame_set(f)
            if f % 20:
                continue
            cur = [o.matrix_world.copy() for o, *_ in packs]
            if prev is not None and f >= 200:
                if all((c.translation - a.translation).length / S < 0.03 * MM and
                       (c.to_3x3() @ a.to_3x3().transposed()).to_quaternion().angle
                       < math.radians(0.1) for a, c in zip(prev, cur)):
                    settled = True
                    break
            prev = cur
        return settled, f

    # Rounds: place by hand, settle; packages that toppled leave room for
    # the next round, which only runs the fill passes.
    rows = layout_rows(b)
    for rnd in range(LAYOUT_ROUNDS):
        poses = [o.matrix_world.copy() for o, *_ in packs]
        new = place_by_hand(rng, b, rows if rnd == 0 else rows[-FILL_PASSES:],
                            [(k, real(o)) for o, k, _ in packs])
        if not new:
            break
        scene.frame_set(1)
        for (o, *_), m in zip(packs, poses):  # settled poses become the start
            o.matrix_world = m
        for kind, fam, m in new:
            o = link(bpy.data.objects.new("_pack", pack_me[kind]), coll)
            o.matrix_world = Matrix.Translation(m.translation * S) @ m.to_3x3().to_4x4()
            add_rb(o, "ACTIVE")
            packs.append((o, kind, fam))
        rbw.point_cache.frame_end = 3000  # touch -> invalidate the cache
        settled, f = settle()
        print(f"  [layout] round {rnd + 1}: +{len(new)} -> {len(packs)} packages, "
              f"settled={settled} after {f} frames")

    # equal numbers of each kind: drop the most recently placed extras (they
    # sit on top of the pile) and let the rest settle again
    counts = {k: sum(p[1] == k for p in packs) for k in PACK_SIZES}
    target = min(counts.values())
    extra = []
    for p in reversed(packs):
        if counts[p[1]] > target:
            counts[p[1]] -= 1
            extra.append(p)
    if extra:
        poses = [o.matrix_world.copy() for o, *_ in packs]
        scene.frame_set(1)
        for (o, *_), m in zip(packs, poses):
            o.matrix_world = m
        for p in extra:
            packs.remove(p)
            bpy.data.objects.remove(p[0])
        rbw.point_cache.frame_end = 3000
        settled, f = settle()
        print(f"  [layout] removed {len(extra)} to balance the kinds, "
              f"settled={settled} after {f} frames")

    tol = max(CLEARANCE - 0.2, 0) * MM
    result = []
    for o, kind, fam in packs:
        m = real(o)
        cs = pack_corners(m, PACK_SIZES[kind])
        if (all(b["x0"] - tol <= c.x <= b["x1"] + tol for c in cs) and
                all(b["y0"] - tol <= c.y <= b["y1"] + tol for c in cs) and
                all(b["z0"] - 0.3 * MM <= c.z <= b["z1"] + tol for c in cs)):
            result.append({"type": kind, "family": fam,
                           "matrix": [list(r) for r in m]})
        else:
            print(f"  [layout] dropped a {fam} package that left the chamber")
    scene.frame_set(1)
    for o in list(coll.objects):
        bpy.data.objects.remove(o)
    bpy.data.collections.remove(coll)
    bpy.ops.rigidbody.world_remove()
    print(f"  [layout] {len(result)} packages in the display")
    return result


def get_layout(force):
    key = layout_key()
    if not force and os.path.exists(LAYOUT_CACHE):
        with open(LAYOUT_CACHE) as fh:
            data = json.load(fh)
        if data.get("key") == key:
            print(f"  [layout] using cached arrangement ({len(data['packs'])} packages)")
            return data["packs"]
    packs = simulate_layout()
    with open(LAYOUT_CACHE, "w") as fh:
        json.dump({"key": key, "seed": SEED, "units": "m, display-local",
                   "packs": packs}, fh, indent=1)
    return packs


def check_layout(layout):
    """Verify the arrangement: no package pair overlaps (hulls shrunk by
    0.2 mm so resting contact does not count) and every package keeps
    clear of the acrylic and the LED face."""
    packs = [(PACK_SIZES[p["type"]], Matrix(p["matrix"])) for p in layout]
    trees = [pack_tree(m, size, -0.2 * MM) for size, m in packs]
    hits = sum(1 for i in range(len(trees)) for j in range(i + 1, len(trees))
               if trees[i].overlap(trees[j]))
    gap = min(min(c.x + IN_X, IN_X - c.x, c.y - FRONT_IN_Y, LED_FACE_Y - c.y,
                  IN_Z - c.z) for size, m in packs for c in pack_corners(m, size))
    counts = {k: sum(p["type"] == k for p in layout) for k in PACK_SIZES}
    print(f"  [check] {len(packs)} packages {counts}, interpenetrating pairs: "
          f"{hits}, min clearance to acrylic/LED: {gap / MM:.2f} mm")
    return hits, gap


# ----------------------------------------------------------------------------
# 02. Acrylic box + back structure, 05. LED
# ----------------------------------------------------------------------------

def build_display(root_coll, acrylic, pack_mats, layout):
    display = bpy.data.objects.new("FlewBy_Display", None)
    display.empty_display_type = "CUBE"
    display.empty_display_size = HW
    display.location = (0, -HD, MOUNT_CENTER_Z * MM)  # back face on the wall
    link(display, root_coll)

    coll = new_collection("Acrylic_Box", root_coll)
    depth_rest = BOX_D * MM - T  # top/bottom/sides run behind the front panel
    yc = -HD + T + depth_rest / 2
    panels = {
        # front panel covers the full face; the others are solvent-bonded
        # behind it (butt joints), sides sit between top and bottom.
        "Front": ((BOX_W * MM, T, BOX_H * MM), (0, -HD + T / 2, 0)),
        "Top": ((BOX_W * MM, depth_rest, T), (0, yc, HH - T / 2)),
        "Bottom": ((BOX_W * MM, depth_rest, T), (0, yc, -HH + T / 2)),
        "Left": ((T, depth_rest, BOX_H * MM - 2 * T), (-HW + T / 2, yc, 0)),
        "Right": ((T, depth_rest, BOX_H * MM - 2 * T), (HW - T / 2, yc, 0)),
    }
    for name, (size, ctr) in panels.items():
        # 0.02 mm shrink leaves a visible bond line instead of coplanar faces
        size = [s - 0.00002 for s in size]
        o = link(bpy.data.objects.new("Acrylic_" + name, box_mesh(name, size, ctr)), coll)
        o.data.materials.append(acrylic)
        add_bevel(o, ACRYLIC_EDGE_BEVEL * MM, 3)
        o.parent = display

    back = new_collection("Back_Structure", root_coll)
    bp_t = BACK_PLATE_T * MM
    o = link(bpy.data.objects.new("Back_Plate", box_mesh(
        "Back_Plate", (2 * IN_X, bp_t, 2 * IN_Z), (0, HD - bp_t / 2, 0))), back)
    o.data.materials.append(mat_simple("BackPlate_WhiteOpal", BACK_PLATE_COLOR, 0.35))
    o.parent = display

    led_t = LED_MODULE_T * MM
    o = link(bpy.data.objects.new("LED_Panel_Module", box_mesh(
        "LED_Panel_Module", (2 * IN_X, led_t, 2 * IN_Z),
        (0, BACK_PLATE_Y - led_t / 2, 0))), back)
    frame = mat_simple("LED_Frame_Aluminium", (0.75, 0.75, 0.76), 0.35, 1.0)
    guide = mat_simple("LED_LightGuide_Diffuser", (0.85, 0.85, 0.85), 0.25)
    o.data.materials.append(frame)
    o.data.materials.append(guide)
    o.data.materials.append(mat_led_edge())
    for p in o.data.polygons:  # front = diffuser, rim = light-guide edge
        p.material_index = (1 if p.normal.y < -0.9 else
                            0 if p.normal.y > 0.9 else 2)
    add_bevel(o, 0.5 * MM, 2)
    o.parent = display

    # the single LED light: a 5000 K area light on the diffuser face
    ins = LED_FACE_INSET * MM
    led = bpy.data.lights.new("LED_Panel_5000K", "AREA")
    led.shape = "RECTANGLE"
    led.size = 2 * IN_X - 2 * ins
    led.size_y = 2 * IN_Z - 2 * ins
    led.energy = LED_POWER_PER_M2 * led.size * led.size_y
    led.use_temperature = True
    led.temperature = LED_TEMPERATURE_K
    led.color = (1, 1, 1)
    led.spread = math.radians(180)
    lo = link(bpy.data.objects.new("LED_Panel_5000K", led), back)
    lo.parent = display
    lo.location = (0, LED_FACE_Y - 0.05 * MM, 0)
    lo.rotation_euler = (math.radians(-90), 0, 0)  # emit toward -Y (front)
    lo.visible_camera = True
    lo.visible_glossy = True

    # packages
    pc = new_collection("Packages", root_coll)
    meshes = {}
    for pt in PACK_TYPES:
        meshes[pt["key"]] = me = package_mesh(pt)
        me.materials.append(pack_mats[pt["key"]])
    objs = []
    for i, p in enumerate(layout):
        o = link(bpy.data.objects.new(f"{p['type']}_{i + 1:02d}", meshes[p["type"]]), pc)
        o.parent = display
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.matrix_basis = Matrix([p["matrix"][r] for r in range(4)])
        o["layout_family"] = p["family"]
        objs.append(o)
    for o in objs:
        add_bevel(o, PACK_EDGE_BEVEL * MM, 2)
    bpy.context.view_layer.update()
    return display


def build_logo(display, coll):
    """flew by logo as black cut vinyl stuck on the front panel. The artwork
    may be light-on-transparent, dark-on-white or light-on-dark; it is turned
    into a mask, cropped to the artwork and mapped onto a 0.08 mm sheet."""
    path = os.path.join(ASSETS, LOGO_IMAGE)
    if not os.path.exists(path):
        print(f"  [logo] {path} not found, no logo on the front panel")
        return None
    img = bpy.data.images.load(path)
    w, h = img.size
    px = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    px = px.reshape(h, w, 4)[::-1]  # top-down
    lum = px[..., :3] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    alpha = px[..., 3]
    if alpha.min() < 0.5:
        mask = alpha
    else:
        mask = 1 - lum if lum.mean() > 0.5 else lum
    rows, cols = np.nonzero(mask > 0.1)
    pad = 4
    y0, y1 = max(rows.min() - pad, 0), min(rows.max() + pad + 1, h)
    x0, x1 = max(cols.min() - pad, 0), min(cols.max() + pad + 1, w)
    mask = mask[y0:y1, x0:x1]
    mh, mw = mask.shape
    out = bpy.data.images.new("flewby_logo_mask", mw, mh, alpha=False)
    rgba = np.dstack([mask, mask, mask, np.ones_like(mask)])[::-1]
    out.pixels.foreach_set(rgba.astype(np.float32).ravel())
    out.filepath_raw = os.path.join(TEXTURES, "flewby_logo_mask.png")
    out.file_format = "PNG"
    out.save()
    out.colorspace_settings.name = "Non-Color"
    out.pack()

    lw = LOGO_WIDTH * MM
    lh = lw * mh / mw
    cx, cz = LOGO_OFFSET[0] * MM, LOGO_OFFSET[1] * MM
    y = -HD - 0.08 * MM  # on the outside of the front panel
    me = bpy.data.meshes.new("FlewBy_Logo_Vinyl")
    me.from_pydata([(cx - lw / 2, y, cz - lh / 2), (cx + lw / 2, y, cz - lh / 2),
                    (cx + lw / 2, y, cz + lh / 2), (cx - lw / 2, y, cz + lh / 2)],
                   [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for loop, co in zip(me.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[loop.index].uv = co

    mat = bpy.data.materials.new("Vinyl_Black_Cut")
    nt, bsdf, mout = principled(mat)
    bsdf.inputs["Base Color"].default_value = (*LOGO_COLOR, 1)
    bsdf.inputs["Roughness"].default_value = LOGO_ROUGHNESS
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = out
    tex.interpolation = "Cubic"
    tex.extension = "CLIP"
    # cut vinyl has crisp edges: sharpen the (possibly low-res) artwork
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[1].position = 0.6
    nt.links.new(tex.outputs["Color"], ramp.inputs["Fac"])
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(ramp.outputs["Color"], mix.inputs[0])
    nt.links.new(transparent.outputs[0], mix.inputs[1])
    nt.links.new(bsdf.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], mout.inputs["Surface"])
    me.materials.append(mat)

    o = link(bpy.data.objects.new("FlewBy_Logo_Vinyl", me), coll)
    o.parent = display
    print(f"  [logo] {LOGO_WIDTH:.0f} x {lh / MM:.0f} mm black vinyl on the front panel")
    return o


def build_wall(coll):
    w, h = WALL_SIZE[0] * MM, WALL_SIZE[1] * MM
    o = link(bpy.data.objects.new("Wall", box_mesh(
        "Wall", (w, 0.1, h), (0, 0.05, h / 2))), coll)
    o.data.materials.append(mat_wall())
    return o


def build_world(scene):
    world = bpy.data.worlds.new("Shop_Ambient")
    scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes.get("Background")
    # soft ceiling-biased ambience: brighter from above than from below
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1
    mr.inputs["From Max"].default_value = 1
    mr.inputs["To Min"].default_value = 0.35 * AMBIENT_STRENGTH
    mr.inputs["To Max"].default_value = 1.6 * AMBIENT_STRENGTH
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bg.inputs["Strength"])
    bg.inputs["Color"].default_value = (1.0, 0.97, 0.93, 1)  # neutral shop light


# ----------------------------------------------------------------------------
# 08. Cameras
# ----------------------------------------------------------------------------

def look_at(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def make_camera(coll, name, loc, target, lens, fstop=None, focus=None):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36
    data.clip_start = 0.01
    cam = link(bpy.data.objects.new(name, data), coll)
    cam.location = loc
    look_at(cam, target)
    if fstop:
        data.dof.use_dof = True
        data.dof.aperture_fstop = fstop
        data.dof.focus_distance = focus or (Vector(target) - Vector(loc)).length
    return cam


def build_cameras(coll):
    zc = MOUNT_CENTER_Z * MM
    yc = -HD  # display centre (world)
    front_y = -BOX_D * MM
    # framing scales with the box size (width, or height for a 16:9 frame)
    k = max(BOX_W, BOX_H * 1.9) / 350.0
    cams = {}
    # A. front elevation — long lens, square to the face
    cams["front"] = make_camera(coll, "CAM_A_Front", (0, front_y - 1.10 * k, zc),
                                (0, yc, zc), 85)
    # B. 45 degrees, slightly above eye level of the box
    d, el = 0.95 * k, math.radians(14)
    cams["angle"] = make_camera(
        coll, "CAM_B_45deg",
        (-d * math.sin(math.radians(45)) * math.cos(el),
         yc - d * math.cos(math.radians(45)) * math.cos(el), zc + d * math.sin(el)),
        (0.004, yc, zc - 0.004), 70, fstop=8)
    # C. detail — macro on the lower-right corner: acrylic edges and
    # thickness, the print behind the front panel, light through the gaps
    tgt = Vector((HW - 0.045, front_y + 0.010, zc - HH + 0.040))
    # focus on the front panel corner; f/8 keeps the front packages sharp
    cams["detail"] = make_camera(coll, "CAM_C_Detail",
                                 tgt + Vector((0.13, -0.26, 0.085)) * 1.35, tgt, 100, fstop=8)
    # D. wall installation — standing viewer, slightly off-axis
    cams["wall"] = make_camera(coll, "CAM_D_Wall", (-0.42 * k ** 0.5, -1.30 * k ** 0.5, 1.36),
                               (0.04, yc, zc - 0.03), 50, fstop=11)
    return cams


# ----------------------------------------------------------------------------
# Render settings
# ----------------------------------------------------------------------------

def setup_render(scene, preview, samples):
    scene.render.engine = "CYCLES"
    cy = scene.cycles
    cy.device = "CPU"
    cy.samples = samples or (SAMPLES_PREVIEW if preview else SAMPLES_FINAL)
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02 if preview else 0.008
    cy.use_denoising = True
    try:
        cy.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    cy.max_bounces = 16
    cy.diffuse_bounces = 5
    cy.glossy_bounces = 8
    cy.transmission_bounces = 16
    cy.transparent_max_bounces = 16
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.5
    cy.sample_clamp_indirect = 8.0
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = PREVIEW_SCALE if preview else 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.compression = 15
    vs = scene.view_settings
    vs.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast"):
        try:
            vs.look = look
            break
        except TypeError:
            continue
    vs.exposure = EXPOSURE
    scene.display_settings.display_device = "sRGB"


# ----------------------------------------------------------------------------

def main():
    opts = parse_args()
    print("== FLEW BY acrylic display ==")
    print(f"  Blender {bpy.app.version_string}")
    scene = reset_scene()

    print("STEP 3: package texture atlases")
    atlases = {pt["key"]: build_atlas(pt) for pt in PACK_TYPES}
    print("STEP 4: random arrangement")
    layout = get_layout(opts["relayout"])

    print("STEP 2/5: acrylic box, back LED, wall")
    root = new_collection("FlewBy")
    acrylic = mat_acrylic()
    pack_mats = {k: mat_package(k, a) for k, a in atlases.items()}
    display = build_display(root, acrylic, pack_mats, layout)
    build_logo(display, root)
    check_layout(layout)
    env = new_collection("Environment")
    build_wall(env)
    build_world(scene)
    cams = build_cameras(new_collection("Cameras"))
    setup_render(scene, opts["preview"], opts["samples"])
    scene.camera = cams["front"]

    os.makedirs(BLEND_DIR, exist_ok=True)
    for a in atlases.values():
        a.pack()
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE, compress=True)
    print(f"  saved {BLEND_FILE}")

    if not opts["render"]:
        return
    out_dir = os.path.join(OUTPUT, "preview") if opts["preview"] else OUTPUT
    os.makedirs(out_dir, exist_ok=True)
    for v in opts["views"]:
        scene.camera = cams[v]
        scene.render.filepath = os.path.join(out_dir, VIEWS[v])
        print(f"STEP 9: rendering {v} -> {scene.render.filepath}")
        bpy.ops.render.render(write_still=True)
    scene.camera = cams["front"]
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE, compress=True)


if __name__ == "__main__":
    main()
