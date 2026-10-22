"""Builds any mascot concept from a JSON spec as a 3D character in Blender and renders one shot: model checks, or an
animated reaction as transparent PNG frames.

Run headless:
  blender -b --factory-startup -P mascot3d.py -- SPEC.json SHOT OUT_DIR [options]

  SHOT      check, idle, hop, celebrate, bounce, dip, undo, surprised, shake, nod, think, love, wave, peek, spin,
            sleepy, wake, entrance, exit (see references/motion.md), or any name with --shot-file
  OUT_DIR   where the PNG frames go: f_0001.png ..., plus last.png (the final frame)

Options:
  --size 600 | 1080x2340   pixels; the width always spans camera.frame body units, so a taller frame shows more
                           above and below (default 600)
  --variant NAME           apply spec.variants[NAME] over the spec (a dark-mode version, say)
  --effects                flat effects with the shots: sparkles, bursts, hearts, z's, dots, impact lines
                           (or set "effects": {"on": true} in the spec)
  --frames A-B             render only these frames (for a quick look)
  --step N                 render every Nth frame (for a quick look)
  --samples N              EEVEE samples (default 64; 16 is fine for drafts)
  --shadow                 a soft ground shadow that shrinks as the mascot rises (for previews)
  --rest-up U              raise the resting spot by U units (room for text under it in a tall frame)
  --shot-file FILE.py      run your own shot with the helpers below (see references/motion.md)

The character is a body plus any parts (ears, arms, a tail, a head, a hat), each a simple shape, an SVG silhouette or
an imported model. Parts hang from pivots, so they can swing, wave and follow through. Faces are flat decals laid
onto the body or onto a part. Three looks: flat (an unlit sticker), toon (bands from one sun) and soft (a lit toy).
"""
import copy
import json
import math
import os
import re
import shutil
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

# MARK: Arguments and spec

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
POS, OPT = [], {}
i = 0
while i < len(argv):
    a = argv[i]
    if a.startswith("--"):
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            OPT[a[2:]] = argv[i + 1]
            i += 2
        else:
            OPT[a[2:]] = True
            i += 1
    else:
        POS.append(a)
        i += 1
if len(POS) < 3:
    sys.exit("usage: blender -b --factory-startup -P mascot3d.py -- SPEC.json SHOT OUT_DIR [options]")
SPEC_PATH, SHOT, OUT = POS[0], POS[1], os.path.abspath(POS[2])
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC_PATH))
os.makedirs(OUT, exist_ok=True)

DEFAULTS = {
    "body": {"shape": "sphere", "size": [1.0, 0.9, 1.0], "bevel": 0.04, "roundness": 2.0, "taper": 0.0},
    "palette": {"fill": "#FFFFFF", "line": "#111111", "edge": "fill", "decal": "line", "shine": "#FFFFFF",
                "white": "#FFFFFF", "blush": "#FF9AAE", "accent": "#FFC93C"},
    "look": {"shading": "flat", "outline": 0.06, "shadow_tint": 0.82, "band": 0.5, "highlight": False,
             "highlight_at": 0.95, "highlight_color": "#FFFFFF", "edge_highlight": False, "reeding": None,
             "light": [55, -35, -20], "border": None, "roughness": 0.45},
    "eyes": {"at": [[-0.34, 0.12], [0.34, 0.12]], "size": [0.13, 0.18], "tilt": 0, "style": "dot",
             "shine": {"at": [-0.35, 0.4], "size": 0.32}, "pupil": 0.6, "look": [0.0, 0.0], "on": "body"},
    "mouth": None,
    "cheeks": None,
    "decals": [],
    "parts": [],
    "effects": {"on": False, "color": "accent", "outline": "line", "size": 1.0},
    "rest": [-8, 0, 8],
    "camera": {"lens": 85, "frame": 4.66, "ortho": False},
    "motion": {"fps": 60, "flip": "z", "flips": 1, "hop": 0.9, "squash": 0.08, "shake": "z",
               "spin_axis": "y", "spin_seconds": 1.0, "wave": None, "wave_lift": 145, "jiggle": 1.0},
}


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


with open(SPEC_PATH) as fh:
    raw = json.load(fh)
SPEC = merge(DEFAULTS, raw)
if "eyes" in raw and raw["eyes"] is None:
    SPEC["eyes"] = None
if OPT.get("variant"):
    name = OPT["variant"]
    if name not in SPEC.get("variants", {}):
        sys.exit(f"no variant '{name}' in the spec")
    SPEC = merge(SPEC, SPEC["variants"][name])

SIZE = str(OPT.get("size", "600"))
WIDTH, HEIGHT = (int(v) for v in SIZE.lower().split("x")) if "x" in SIZE.lower() else (int(SIZE), int(SIZE))
MOTION = SPEC["motion"]
FPS = int(OPT.get("fps", MOTION["fps"]))
LOOK = SPEC["look"]
REST = tuple(math.radians(v) for v in SPEC["rest"])
REST_UP = float(OPT.get("rest-up", 0))
EFFECTS = bool(OPT.get("effects")) or bool(SPEC["effects"].get("on"))


# MARK: Colours

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def colour(ref, depth=0):
    """A palette name ("fill", "line", ...) or a hex colour, as linear RGBA for Blender."""
    if isinstance(ref, (list, tuple)):
        return tuple(ref) if len(ref) == 4 else tuple(ref) + (1.0,)
    if not ref.startswith("#"):
        if depth > 5 or ref not in SPEC["palette"]:
            sys.exit(f"unknown colour '{ref}'")
        return colour(SPEC["palette"][ref], depth + 1)
    h = ref.lstrip("#")
    r, g, b = (int(h[k:k + 2], 16) / 255 for k in (0, 2, 4))
    return (srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b), 1.0)


# MARK: Scene

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for engine in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
scene.render.film_transparent = True
scene.render.filter_size = 1.0
scene.view_settings.view_transform = "Standard"   # the default (AgX/Filmic) washes colours out
scene.view_settings.look = "None"
scene.eevee.taa_render_samples = int(OPT.get("samples", 64))
scene.render.fps = FPS
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
if LOOK["shading"] == "soft":
    world = bpy.data.worlds.new("World")       # soft ambient light, so shaded sides aren't black (it isn't seen)
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.62, 0.66, 1)
    scene.world = world


def link(ob):
    scene.collection.objects.link(ob)
    return ob


def bake(ob):
    """Apply an object's modifiers by replacing its mesh with the evaluated one (works headless, without operators)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    old = ob.data
    ob.data = me
    if old is not None and old.users == 0 and isinstance(old, bpy.types.Mesh):
        bpy.data.meshes.remove(old)


def apply_transform(ob):
    ob.data.transform(ob.matrix_basis)
    ob.matrix_basis = Matrix.Identity(4)


# MARK: Materials

def new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    for n in list(tree.nodes):
        if n.type != "OUTPUT_MATERIAL":
            tree.nodes.remove(n)
    return mat, tree, tree.nodes["Material Output"]


def math_node(tree, op, a=None, b=None):
    n = tree.nodes.new("ShaderNodeMath")
    n.operation = op
    if a is not None:
        n.inputs[0].default_value = a
    if b is not None:
        n.inputs[1].default_value = b
    return n


def light_value(tree):
    """How lit a surface is under the sun, from 0 to 1: white diffuse turned into a number."""
    diffuse = tree.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    torgb = tree.nodes.new("ShaderNodeShaderToRGB")
    tree.links.new(diffuse.outputs[0], torgb.inputs[0])
    return torgb.outputs["Color"]


def step(tree, value_socket, at):
    """A hard cut: 0 below `at`, 1 above."""
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = at
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    tree.links.new(value_socket, ramp.inputs["Fac"])
    sep = tree.nodes.new("ShaderNodeSeparateColor")
    tree.links.new(ramp.outputs["Color"], sep.inputs[0])
    return sep.outputs[0]


def mix(tree, factor, a, b):
    """Mix two colours (sockets or RGBA values) by a factor (socket or number)."""
    m = tree.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    for slot, v in (("A", a), ("B", b)):
        if isinstance(v, tuple):
            m.inputs[slot].default_value = v
        else:
            tree.links.new(v, m.inputs[slot])
    if isinstance(factor, (int, float)):
        m.inputs["Factor"].default_value = factor
    else:
        tree.links.new(factor, m.inputs["Factor"])
    return m.outputs["Result"]


def finish(tree, out, colour_socket_or_value):
    em = tree.nodes.new("ShaderNodeEmission")
    if isinstance(colour_socket_or_value, tuple):
        em.inputs["Color"].default_value = colour_socket_or_value
    else:
        tree.links.new(colour_socket_or_value, em.inputs["Color"])
    tree.links.new(em.outputs[0], out.inputs["Surface"])


def flat(name, rgba, cull=False):
    mat, tree, out = new_material(name)
    finish(tree, out, rgba)
    mat.use_backface_culling = cull
    return mat


def invisible(name):
    """Draws nothing: the base of a border shell, which sits on the body."""
    mat, tree, out = new_material(name)
    tr = tree.nodes.new("ShaderNodeBsdfTransparent")
    tree.links.new(tr.outputs[0], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"
    else:
        mat.blend_method = "BLEND"
    return mat


def shaded(name, rgba, highlight=None):
    """A surface colour in the spec's look: flat (unlit), toon (a darker band away from the sun and an optional
    highlight) or soft (a lit, slightly glossy toy)."""
    shading = LOOK["shading"]
    if shading == "soft":
        mat, tree, out = new_material(name)
        bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = rgba
        bsdf.inputs["Roughness"].default_value = LOOK.get("roughness", 0.45)
        tree.links.new(bsdf.outputs[0], out.inputs["Surface"])
        return mat
    if shading != "toon" and not highlight:
        return flat(name, rgba)
    mat, tree, out = new_material(name)
    lit = light_value(tree)
    result = rgba
    if shading == "toon":
        k = LOOK["shadow_tint"]
        result = mix(tree, step(tree, lit, LOOK["band"]), (rgba[0] * k, rgba[1] * k, rgba[2] * k, 1.0), rgba)
    if highlight:
        result = mix(tree, step(tree, lit, LOOK["highlight_at"]), result, colour(LOOK["highlight_color"]))
    finish(tree, out, result)
    return mat


def edge_material(rgba, stripe_rgba, half_depth):
    """A thick body's side: its colour, with optional reeding (stripes round a disc's rim) and a crisp highlight
    that slides along it as the body turns towards the light."""
    reeding = LOOK.get("reeding")
    if not reeding and not LOOK["edge_highlight"]:
        return shaded("Edge", rgba)
    mat, tree, out = new_material("Edge")
    links = tree.links
    marks = None
    if reeding:
        coord = tree.nodes.new("ShaderNodeTexCoord")
        xyz = tree.nodes.new("ShaderNodeSeparateXYZ")
        links.new(coord.outputs["Object"], xyz.inputs[0])
        angle = math_node(tree, "ARCTAN2")
        links.new(xyz.outputs["Z"], angle.inputs[0])
        links.new(xyz.outputs["X"], angle.inputs[1])
        turns = math_node(tree, "MULTIPLY", b=reeding.get("stripes", 64) / (2 * math.pi))
        links.new(angle.outputs[0], turns.inputs[0])
        frac = math_node(tree, "FRACT")
        links.new(turns.outputs[0], frac.inputs[0])
        stripe = math_node(tree, "LESS_THAN", b=reeding.get("duty", 0.3))
        links.new(frac.outputs[0], stripe.inputs[0])
        band = math_node(tree, "ABSOLUTE")
        links.new(xyz.outputs["Y"], band.inputs[0])
        inband = math_node(tree, "LESS_THAN", b=half_depth * 0.64)     # the flat band, not the rounded corners
        links.new(band.outputs[0], inband.inputs[0])
        marks = math_node(tree, "MULTIPLY")
        links.new(stripe.outputs[0], marks.inputs[0])
        links.new(inband.outputs[0], marks.inputs[1])
        marks = marks.outputs[0]
    if LOOK["edge_highlight"]:
        shine = step(tree, light_value(tree), 0.93)
        if marks is None:
            marks = shine
        else:
            either = math_node(tree, "MAXIMUM")
            links.new(marks, either.inputs[0])
            links.new(shine, either.inputs[1])
            marks = either.outputs[0]
    finish(tree, out, mix(tree, marks, rgba, stripe_rgba))
    return mat


FILL, LINE = colour("fill"), colour("line")
M_LINE = flat("Outline", LINE, cull=True)
M_NONE = invisible("Invisible")


# MARK: Shapes

def lathe(name, radius_at, half_height, rings=48, seg=64):
    """A round shape turned on a lathe around Z: radius_at(z) gives the radius at each height. Rings are spaced by
    angle, not height, so the poles stay round instead of coming to a point."""
    bm = bmesh.new()
    top = bm.verts.new((0, 0, half_height))
    bottom = bm.verts.new((0, 0, -half_height))
    rows = []
    for k in range(1, rings):
        z = half_height * math.cos(math.pi * k / rings)
        r = max(radius_at(z), 1e-4)
        rows.append([bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)) for a in
                     (2 * math.pi * s / seg for s in range(seg))])
    for s in range(seg):
        t = (s + 1) % seg
        bm.faces.new((top, rows[0][t], rows[0][s]))
        bm.faces.new((bottom, rows[-1][s], rows[-1][t]))
    for up, down in zip(rows, rows[1:]):
        for s in range(seg):
            t = (s + 1) % seg
            bm.faces.new((up[s], up[t], down[t], down[s]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return link(bpy.data.objects.new(name, me))


def round_shape(name, shape, size, roundness=2.0, taper=0.0):
    """sphere, egg, blob or capsule. size = half-width, half-depth, half-height."""
    w, d, h = size
    if shape == "capsule":
        straight = max(h - w, 0.0)

        def r(z):
            over = abs(z) - straight
            return w if over <= 0 else math.sqrt(max(w * w - over * over, 0.0))
    else:
        p = roundness if shape == "blob" else 2.0

        def r(z):
            t = min(abs(z) / h, 1.0)
            lean = 1 - taper * (z / h) * 0.5 if shape == "egg" else 1.0
            return w * (1 - t ** p) ** (1 / p) * lean
    ob = lathe(name, r, h)
    ob.scale.y = d / w
    apply_transform(ob)
    return ob


def parse_path(d):
    """Absolute SVG path commands (M L H V C Q Z) into closed loops of cubic segments."""
    tokens = re.findall(r"[MLHVCQZmlhvcqz]|-?\d*\.?\d+(?:[eE]-?\d+)?", d)
    loops, cur, pos, start, cmd, k = [], [], (0.0, 0.0), (0.0, 0.0), None, 0

    def num():
        nonlocal k
        k += 1
        return float(tokens[k - 1])

    def line_to(p):
        # A straight line as a cubic with its handles a third of the way along, so the fill stays clean.
        nonlocal pos
        c1 = (pos[0] + (p[0] - pos[0]) / 3, pos[1] + (p[1] - pos[1]) / 3)
        c2 = (pos[0] + 2 * (p[0] - pos[0]) / 3, pos[1] + 2 * (p[1] - pos[1]) / 3)
        cur.append((pos, c1, c2, p))
        pos = p

    def close():
        nonlocal cur, pos
        if cur:
            if math.dist(pos, start) > 1e-6:
                line_to(start)                 # Z draws the closing edge back to the start
            loops.append(cur)
        cur, pos = [], start

    while k < len(tokens):
        if tokens[k].isalpha():
            cmd = tokens[k]
            k += 1
            if cmd.islower():
                sys.exit("body.d: use absolute path commands (capitals)")
            if cmd == "Z":
                close()
                continue
        if cmd == "M":
            if cur:
                close()
            pos = start = (num(), num())
            cmd = "L"
        elif cmd == "L":
            line_to((num(), num()))
        elif cmd == "H":
            line_to((num(), pos[1]))
        elif cmd == "V":
            line_to((pos[0], num()))
        elif cmd == "C":
            c1, c2, p = (num(), num()), (num(), num()), (num(), num())
            cur.append((pos, c1, c2, p))
            pos = p
        elif cmd == "Q":
            q, p = (num(), num()), (num(), num())
            cur.append((pos, (pos[0] + 2 / 3 * (q[0] - pos[0]), pos[1] + 2 / 3 * (q[1] - pos[1])),
                        (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1])), p))
            pos = p
        else:
            sys.exit(f"body.d: unsupported command {cmd}")
    if cur:
        close()
    return loops


def path_shape(name, d, half_depth, bevel, width=2.0):
    """A 2D silhouette (an SVG path) made into a thick sticker with rounded edges, facing the camera, `width` wide."""
    loops = parse_path(d)
    xs = [p[0] for loop in loops for seg in loop for p in (seg[0], seg[3])]
    ys = [p[1] for loop in loops for seg in loop for p in (seg[0], seg[3])]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    scale = width / (max(xs) - min(xs))

    def to2(p):
        return ((p[0] - cx) * scale, -(p[1] - cy) * scale)
    cu = bpy.data.curves.new(name + "Curve", "CURVE")
    cu.dimensions = "2D"
    cu.fill_mode = "BOTH"
    cu.resolution_u = 24
    cu.extrude = max(half_depth - bevel, 0.001)
    cu.bevel_depth = bevel
    cu.bevel_resolution = 6
    for loop in loops:
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(loop) - 1)
        sp.use_cyclic_u = True
        for n, (p0, c1, c2, p1) in enumerate(loop):
            bp = sp.bezier_points[n]
            bp.co = (*to2(p0), 0)
            bp.handle_right_type = bp.handle_left_type = "FREE"
            bp.handle_right = (*to2(c1), 0)
            bp.handle_left = (*to2(loop[n - 1][2]), 0)
    tmp = link(bpy.data.objects.new(name + "Curve", cu))
    tmp.rotation_euler = (math.pi / 2, 0, 0)    # the sticker's front faces the camera (-Y); it extrudes along Y
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    me.transform(tmp.matrix_basis)
    bpy.data.objects.remove(tmp)
    return link(bpy.data.objects.new(name, me))


def file_shape(name, path, width=2.0):
    path = path if os.path.isabs(path) else os.path.join(SPEC_DIR, path)
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    else:
        sys.exit(f"{name}.file: can't import {ext} (use .glb, .gltf, .obj or .fbx)")
    meshes = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]
    if not meshes:
        sys.exit(f"{name}.file: no meshes in {path}")
    data = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for o in meshes:
        part = o.data.copy()
        part.transform(o.matrix_world)
        bm.from_mesh(part)
    bm.to_mesh(data)
    bm.free()
    for o in set(bpy.data.objects) - before:
        bpy.data.objects.remove(o)
    lo = Vector((min(v.co[k] for v in data.vertices) for k in range(3)))
    hi = Vector((max(v.co[k] for v in data.vertices) for k in range(3)))
    data.transform(Matrix.Scale(width / (hi.x - lo.x), 4) @ Matrix.Translation(-(lo + hi) / 2))
    return link(bpy.data.objects.new(name, data))


def make_shape(name, p, is_body=False):
    """One piece of the character from its spec: body or part."""
    shape, s = p.get("shape", "sphere"), list(p.get("size", [1.0, 0.9, 1.0] if is_body else [0.3]))
    if shape in ("sphere", "egg", "blob", "capsule"):
        s = s + [s[0]] * (3 - len(s)) if len(s) < 3 else s
        if len(p.get("size", [])) == 1:
            s = [s[0]] * 3
        ob = round_shape(name, shape, s, p.get("roundness", 2.0), p.get("taper", 0.0))
    elif shape == "disc":
        bpy.ops.mesh.primitive_cylinder_add(vertices=160, radius=s[0], depth=2 * (s[1] if len(s) > 1 else 0.1),
                                            rotation=(math.pi / 2, 0, 0))
        ob = bpy.context.active_object
        apply_transform(ob)
    elif shape == "box":
        bpy.ops.mesh.primitive_cube_add(size=2)
        ob = bpy.context.active_object
        ob.scale = tuple(s) if len(s) == 3 else (s[0],) * 3
        apply_transform(ob)
    elif shape == "cylinder":
        # Standing up (a cup, a can, a battery): size = radius, half-depth, half-height.
        s = s + [s[0]] * (3 - len(s)) if len(s) < 3 else s
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=s[0], depth=2 * s[2])
        ob = bpy.context.active_object
        ob.scale.y = s[1] / s[0]
        apply_transform(ob)
    elif shape == "torus":
        bpy.ops.mesh.primitive_torus_add(major_radius=s[0], minor_radius=s[1], major_segments=96, minor_segments=24)
        ob = bpy.context.active_object
    elif shape == "cone":
        bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=s[0], radius2=s[1] if len(s) > 2 else 0,
                                        depth=s[-1] * 2)
        ob = bpy.context.active_object
    elif shape == "path":
        ob = path_shape(name, p["d"], s[1] if len(s) > 1 else 0.15, p.get("bevel", 0.06), width=2 * s[0])
    elif shape == "file":
        ob = file_shape(name, p["file"], width=2 * s[0])
    else:
        sys.exit(f"{name}.shape '{shape}' isn't one of sphere, egg, blob, capsule, cylinder, disc, box, torus, cone, "
                 f"path, file")
    ob.name = name
    if shape in ("disc", "box", "cylinder") and p.get("bevel", 0 if shape == "disc" else 0.04) > 0:
        bev = ob.modifiers.new("Bevel", "BEVEL")
        bev.width = p.get("bevel", 0.04)
        bev.segments = 3 if shape == "disc" else 4
        bev.limit_method = "ANGLE"
        bev.material = 1
        bake(ob)
    for poly in ob.data.polygons:
        poly.use_smooth = True
    return ob


# MARK: Body and parts

BODY = SPEC["body"]
body = make_shape("Body", BODY, is_body=True)
FLAT_FRONT = BODY.get("shape", "sphere") in ("disc", "box", "path")     # a thick sticker: a front, back and side
_zs = [v.co.z for v in body.data.vertices]
_ys = [v.co.y for v in body.data.vertices]
HALF_HEIGHT = (max(_zs) - min(_zs)) / 2
DEPTH = (max(_ys) - min(_ys)) / 2
BOTTOM = min(_zs)

EDGE = colour(SPEC["palette"]["edge"])
body.data.materials.append(shaded("Fill", FILL, highlight=LOOK["highlight"]))
body.data.materials.append(edge_material(EDGE, FILL if EDGE != FILL else LINE, DEPTH))
if FLAT_FRONT:
    for poly in body.data.polygons:
        poly.material_index = 0 if abs(poly.normal.y) > 0.9 else 1
elif BODY.get("shape") == "file":
    for poly in body.data.polygons:      # an imported model's own material slots are gone: it's all fill
        poly.material_index = 0

PARTS = {}          # name -> {"ob", "pivot", "rest", "jiggle", "axis", "outline"}
for n, p in enumerate(SPEC.get("parts", [])):
    pname = p.get("name", f"Part{n}")
    ob = make_shape(pname, p)
    ob.data.materials.clear()
    ob.data.materials.append(shaded(f"{pname} colour", colour(p.get("color", "fill")), highlight=LOOK["highlight"]))
    for poly in ob.data.polygons:
        poly.material_index = 0
    at = Vector(p.get("at", [0, 0, 1.2]))
    pivot_at = Vector(p.get("pivot", list(at)))
    # The part hangs from an empty at its pivot (a shoulder, the root of an ear), so turning the empty swings it.
    pivot = link(bpy.data.objects.new(f"{pname} pivot", None))
    pivot.location = pivot_at
    ob.location = at - pivot_at
    ob.rotation_euler = tuple(math.radians(v) for v in p.get("rotate", [0, 0, 0]))
    ob.parent = pivot
    PARTS[pname] = {"ob": ob, "pivot": pivot, "rest": pivot.rotation_euler.copy(), "jiggle": p.get("jiggle", 0),
                    "axis": p.get("jiggle_axis", "y"), "outline": p.get("outline", True), "at": at}
bpy.context.view_layer.update()


# MARK: Features: decals laid onto the body or a part

def surface(target_name):
    """A ray tree of a piece's surface in world space (before outlines), for laying and moving features on it."""
    ob = body if target_name == "body" else PARTS[target_name]["ob"]
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.transform(ob.matrix_world)
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(poly.vertices) for poly in me.polygons])
    bpy.data.meshes.remove(me)
    return ob, tree


SURFACES = {}


def target(name):
    if name != "body" and name not in PARTS:
        sys.exit(f"a feature is 'on' '{name}', but there's no part with that name")
    if name not in SURFACES:
        SURFACES[name] = surface(name)
    return SURFACES[name]


def origin_of(name):
    return Vector((0, 0, 0)) if name == "body" else PARTS[name]["at"]


def front_y(name, x, z, side=-1):
    """Where the piece's front (or back) surface is at world (x, z), or None if (x, z) misses it."""
    _, tree = target(name)
    hit = tree.ray_cast(Vector((x, side * 50, z)), Vector((0, -side, 0)))
    return hit[0].y if hit[0] is not None else None


decal_materials = {}


def decal_material(ref):
    key = str(ref)
    if key not in decal_materials:
        decal_materials[key] = flat(f"Decal {key}", colour(ref))
    return decal_materials[key]


def ellipse_mesh(name, rx, rz, inner=0.0, rings=6, seg=64):
    """A flat ellipse (or a ring, with `inner` > 0) in the XZ plane, in concentric rows so it can bend onto a curve."""
    bm = bmesh.new()
    rows = []
    fractions = [k / rings for k in range(1, rings + 1)] if inner == 0 else \
        [inner + (1 - inner) * k / rings for k in range(0, rings + 1)]
    for t in fractions:
        rows.append([bm.verts.new((math.cos(a) * rx * t, 0, math.sin(a) * rz * t)) for a in
                     (2 * math.pi * s / seg for s in range(seg))])
    if inner == 0:
        centre = bm.verts.new((0, 0, 0))
        for s in range(seg):
            bm.faces.new((centre, rows[0][s], rows[0][(s + 1) % seg]))
    for a, b in zip(rows, rows[1:]):
        for s in range(seg):
            t = (s + 1) % seg
            bm.faces.new((a[s], a[t], b[t], b[s]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def stroke_mesh(name, points, width):
    """A round-ended line along cubic Bezier segments: points are [x, z] face coordinates, an anchor then (control,
    control, anchor) per segment."""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = width / 2
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    cu.resolution_u = 16
    sp = cu.splines.new("BEZIER")
    anchors = [points[0]] + points[3::3]
    sp.bezier_points.add(len(anchors) - 1)
    to3 = lambda p: Vector((p[0], 0, p[1]))
    for k, bp in enumerate(sp.bezier_points):
        bp.co = to3(anchors[k])
        bp.handle_left_type = bp.handle_right_type = "FREE"
        bp.handle_left = to3(points[3 * k - 1]) if k > 0 else bp.co
        bp.handle_right = to3(points[3 * k + 1]) if 3 * k + 1 < len(points) else bp.co
    tmp = link(bpy.data.objects.new(name, cu))
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    return me


def lay(me, name, x, z, ref, on="body", side=-1, lift=1, tilt=0.0):
    """Lay a flat feature onto a piece's front (side -1) or back (+1), at face coordinates (x, z) from the piece's
    centre: cast it along Y onto the surface, a hair above it (`lift` stacks features: a shine over an eye)."""
    target_ob, _ = target(on)
    centre = origin_of(on)
    ob = link(bpy.data.objects.new(name, me))
    me.materials.append(decal_material(ref))
    ob.location = (centre.x + x, side * 50.0, centre.z + z)
    ob.rotation_euler = (0, math.radians(tilt), 0)
    wrap = ob.modifiers.new("Wrap", "SHRINKWRAP")
    wrap.target = target_ob
    wrap.wrap_method = "PROJECT"
    wrap.use_project_y = True
    wrap.use_positive_direction = side < 0
    wrap.use_negative_direction = side > 0
    wrap.offset = 0.004 * lift
    bake(ob)
    missed = sum(1 for v in ob.data.vertices if abs(v.co.y) < 1.0)     # a hit moves a point ~50 units along Y
    if missed:
        print(f"WARNING: {name} hangs off the edge of '{on}' ({missed} points missed it); move it in or shrink it")
    attach(ob, on)
    return ob


def attach(ob, on):
    """Hang an object from a piece (the body, or a part), keeping where it is."""
    parent = body if on == "body" else PARTS[on]["ob"]
    bpy.context.view_layer.update()
    world = ob.matrix_world.copy()
    ob.parent = parent
    ob.matrix_parent_inverse = parent.matrix_world.inverted()
    ob.matrix_world = world


def group(name, x, z, members, on):
    """An empty at a feature's centre on its piece, that the feature's pieces hang from, so it can blink, widen or
    glance as one."""
    centre = origin_of(on)
    g = link(bpy.data.objects.new(name, None))
    fy = front_y(on, centre.x + x, centre.z + z)
    g.location = (centre.x + x, fy if fy is not None else -DEPTH, centre.z + z)
    bpy.context.view_layer.update()
    for m in members:
        world = m.matrix_world.copy()
        m.parent = g
        m.matrix_parent_inverse = g.matrix_world.inverted()
        m.matrix_world = world
    attach(g, on)
    return g


def arc(x, z, w, h, up=True):
    """A closed eye as a cubic arc: up (∩) is happy, down (∪) is asleep."""
    s = 1 if up else -1
    return [[x - w, z - s * h * 0.35], [x - w * 0.55, z + s * h * 0.95], [x + w * 0.55, z + s * h * 0.95],
            [x + w, z - s * h * 0.35]]


EYES, FACES = [], {"open": [], "happy": [], "closed": []}
E = SPEC["eyes"]
if E:
    on = E.get("on", "body")
    rx, rz = E["size"]
    for n, (x, z) in enumerate(E["at"]):
        pieces = []
        style = E["style"]
        sh = E.get("shine") or {}
        sx, sz = sh.get("at", [-0.35, 0.4])
        ss = sh.get("size", 0.32)
        tilt = -E["tilt"] if E.get("mirror_tilt") and x < 0 else E["tilt"]
        if style == "pupil":
            pieces.append(lay(ellipse_mesh(f"Eye{n}", rx, rz), f"Eye{n}", x, z, "white", on, tilt=tilt))
            lx, lz = E.get("look", [0, 0])
            pr = min(rx, rz) * E.get("pupil", 0.6)
            px, pz = x + lx * (rx - pr), z + lz * (rz - pr)
            pieces.append(lay(ellipse_mesh(f"Pupil{n}", pr, pr), f"Pupil{n}", px, pz, "decal", on, lift=2))
            if ss:
                pieces.append(lay(ellipse_mesh(f"Shine{n}", pr * ss, pr * ss), f"Shine{n}", px + sx * pr,
                                  pz + sz * pr, "shine", on, lift=3))
        else:
            pieces.append(lay(ellipse_mesh(f"Eye{n}", rx, rz), f"Eye{n}", x, z, "decal", on, tilt=tilt))
            if ss:
                # "dot": a small shine inside the eye. "bite": a larger notch in the body's colour that cuts the eye's
                # edge, like a sticker's catchlight.
                ref = "shine" if style == "dot" else sh.get("color", "fill")
                pieces.append(lay(ellipse_mesh(f"Shine{n}", rx * ss, rx * ss), f"Shine{n}", x + sx * rx,
                                  z + sz * rz, ref, on, lift=2))
        eye_group = group(f"EyeGroup{n}", x, z, pieces, on)
        EYES.append({"group": eye_group, "x": x, "z": z, "on": on, "base": eye_group.location.copy()})
        FACES["open"] += pieces
        width = max(rx * 0.48, 0.035)
        FACES["happy"].append(lay(stroke_mesh(f"Happy{n}", arc(x, z, rx * 0.95, rz * 0.55, True), width * 0.9),
                                  f"Happy{n}", 0, 0, "decal", on))
        FACES["closed"].append(lay(stroke_mesh(f"Closed{n}", arc(x, z - rz * 0.25, rx * 0.95, rz * 0.45, False),
                                               width * 0.9), f"Closed{n}", 0, 0, "decal", on))

MOUTH = SPEC.get("mouth")
if MOUTH:
    on = MOUTH.get("on", "body")
    mx, mz = MOUTH.get("at", [0, -0.2])
    mw = MOUTH.get("width", 0.18)
    line = MOUTH.get("line", 0.045)
    kind = MOUTH.get("shape", "smile")
    ref = MOUTH.get("color", "decal")
    if "points" in MOUTH:
        mouth = lay(stroke_mesh("Mouth", MOUTH["points"], line), "Mouth", 0, 0, ref, on)
    elif kind == "o":
        mouth = lay(ellipse_mesh("Mouth", mw * 0.4, mw * 0.5), "Mouth", mx, mz, ref, on)
    elif kind == "flat":
        mouth = lay(stroke_mesh("Mouth", [[mx - mw / 2, mz], [mx - mw / 6, mz], [mx + mw / 6, mz], [mx + mw / 2, mz]],
                                line), "Mouth", 0, 0, ref, on)
    else:
        mouth = lay(stroke_mesh("Mouth", arc(mx, mz, mw / 2, mw * 0.45, False), line), "Mouth", 0, 0, ref, on)
    for f in MOUTH.get("faces", ["open", "happy", "closed"]):
        FACES.setdefault(f, []).append(mouth)

if SPEC.get("cheeks"):
    C = SPEC["cheeks"]
    crx, crz = C.get("size", [0.12, 0.07])
    for n, (x, z) in enumerate(C["at"]):
        lay(ellipse_mesh(f"Cheek{n}", crx, crz), f"Cheek{n}", x, z, C.get("color", "blush"), C.get("on", "body"),
            lift=0.5)

for n, d in enumerate(SPEC.get("decals", [])):
    on = d.get("on", "body")
    for side in {"front": [-1], "back": [1], "both": [-1, 1]}[d.get("side", "front")]:
        mirror = -1 if side > 0 else 1      # seen from behind, x runs the other way
        if d["type"] == "ring":
            r, w = d["r"], d["width"]
            me = ellipse_mesh(f"Ring{n}", r + w / 2, r + w / 2, inner=(r - w / 2) / (r + w / 2), rings=2, seg=160)
            lay(me, f"Ring{n}", 0, 0, d.get("color", "decal"), on, side=side)
        elif d["type"] == "disc":
            x, z = d["at"]
            dr = d["size"] if isinstance(d["size"], list) else (d["size"], d["size"])
            lay(ellipse_mesh(f"Disc{n}", dr[0], dr[1]), f"Disc{n}", x * mirror, z, d.get("color", "decal"), on,
                side=side, lift=d.get("lift", 1))
        elif d["type"] == "stroke":
            pts = [[p[0] * mirror, p[1]] for p in d["points"]]
            lay(stroke_mesh(f"Stroke{n}", pts, d.get("width", 0.05)), f"Stroke{n}", 0, 0, d.get("color", "decal"),
                on, side=side, lift=d.get("lift", 1))


# MARK: Outline and border

def add_outline(ob):
    """The inverted hull: a slightly bigger, inside-out copy drawn in the line colour, seen only from outside."""
    count = len(ob.data.materials)
    for _ in range(count):
        ob.data.materials.append(M_LINE)
    hull = ob.modifiers.new("Outline", "SOLIDIFY")
    hull.thickness, hull.offset = LOOK["outline"], 1.0
    hull.use_flip_normals, hull.use_rim = True, False
    hull.material_offset = count


def add_border(ob, border):
    """A second, wider hull in another colour outside the outline: a sticker's cut edge, so a dark outline still
    reads on a dark background."""
    copy_ob = link(bpy.data.objects.new(ob.name + " border", ob.data.copy()))
    copy_ob.data.materials.clear()
    copy_ob.data.materials.append(M_NONE)
    copy_ob.data.materials.append(flat(ob.name + " border colour", colour(border.get("color", "#FFFFFF")), cull=True))
    for poly in copy_ob.data.polygons:
        poly.material_index = 0
    hull = copy_ob.modifiers.new("Border", "SOLIDIFY")
    hull.thickness, hull.offset = LOOK["outline"] + border.get("width", 0.06), 1.0
    hull.use_flip_normals, hull.use_rim = True, False
    hull.material_offset = 1
    copy_ob.parent = ob.parent
    copy_ob.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
    copy_ob.matrix_basis = ob.matrix_basis.copy()
    if ob is not body:
        copy_ob.parent = ob
        copy_ob.matrix_parent_inverse = Matrix.Identity(4)
        copy_ob.matrix_basis = Matrix.Identity(4)
    return copy_ob


if LOOK["outline"] > 0:
    add_outline(body)
    for part in PARTS.values():
        if part["outline"]:
            add_outline(part["ob"])
if LOOK.get("border"):
    border_body = add_border(body, LOOK["border"])
    for part in PARTS.values():
        add_border(part["ob"], LOOK["border"])


# MARK: Rig, light and camera

rig = link(bpy.data.objects.new("Rig", None))        # moves and squashes, without turning
body.parent = rig
bpy.context.view_layer.update()
for ob in list(scene.objects):
    if ob.parent is None and ob not in (rig, body) and ob.type in ("MESH", "EMPTY"):
        world = ob.matrix_world.copy()
        ob.parent = body
        ob.matrix_parent_inverse = body.matrix_world.inverted()
        ob.matrix_world = world

sun = bpy.data.lights.new("Sun", "SUN")
sun.energy = math.pi if LOOK["shading"] != "soft" else 2.6   # white diffuse peaks at 1.0, so toon cuts read as angles
sun.use_shadow = False          # the outline's shell would shade everything inside it; a sticker casts no shadows
sun_ob = link(bpy.data.objects.new("Sun", sun))
sun_ob.rotation_euler = tuple(math.radians(v) for v in LOOK["light"])

CAM = SPEC["camera"]
FRAME_W = CAM["frame"]
HALF_W = FRAME_W / 2
HALF_H = HALF_W * HEIGHT / WIDTH
cam_data = bpy.data.cameras.new("Camera")
cam_data.sensor_fit = "HORIZONTAL"
if CAM.get("ortho"):
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = FRAME_W
    distance = 20
else:
    cam_data.lens = CAM["lens"]
    distance = HALF_W * CAM["lens"] / 18          # 36 mm sensor: the width at the mascot spans FRAME_W
cam = link(bpy.data.objects.new("Camera", cam_data))
cam.location = (0, -distance, 0)
cam.rotation_euler = (math.pi / 2, 0, 0)
cam_data.clip_end = distance * 4
scene.camera = cam

if OPT.get("shadow"):
    me = ellipse_mesh("Shadow", 0.85, 0.85)
    mat, tree, out = new_material("Shadow")
    tr = tree.nodes.new("ShaderNodeBsdfTransparent")
    em = tree.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = LINE
    mx_ = tree.nodes.new("ShaderNodeMixShader")
    mx_.inputs["Fac"].default_value = 0.22
    tree.links.new(tr.outputs[0], mx_.inputs[1])
    tree.links.new(em.outputs[0], mx_.inputs[2])
    tree.links.new(mx_.outputs[0], out.inputs["Surface"])
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "BLENDED"        # smooth alpha; the default dithering speckles
    else:
        mat.blend_method = "BLEND"
    me.materials.append(mat)
    shadow = link(bpy.data.objects.new("Shadow", me))
    shadow.location = (0, DEPTH + 0.4, BOTTOM - 0.18)
    shadow.scale = (1, 1, 0.12)
    for axis in (0, 2):     # shrinks as the rig rises
        fc = shadow.driver_add("scale", axis)
        var = fc.driver.variables.new()
        var.name, var.type = "z", "TRANSFORMS"
        var.targets[0].id = rig
        var.targets[0].transform_type = "LOC_Z"
        fc.driver.type = "SCRIPTED"
        fc.driver.expression = "0.95 - 0.35*z" if axis == 0 else "(0.95 - 0.35*z)*0.12"


# MARK: Animation helpers (also available to --shot-file)

SQUASH_DEPTH = not FLAT_FRONT


def pose(frame, up=None, turn=None, squash=None, side=None):
    """Key the mascot at a frame. up: height above its resting spot; turn: (x, y, z) degrees added to the rest pose;
    squash: + flattens (landing, crouching), - stretches (launching); side: sideways shift."""
    if up is not None or side is not None or squash is not None:
        sq = squash or 0.0
        rig.location = ((side or 0.0), 0, REST_UP + (up or 0.0) - sq * HALF_HEIGHT)
        rig.keyframe_insert("location", frame=frame)
    if squash is not None:
        rig.scale = (1 + squash, 1 + squash if SQUASH_DEPTH else 1, 1 - squash)
        rig.keyframe_insert("scale", frame=frame)
    if turn is not None:
        body.rotation_euler = tuple(r + math.radians(t) for r, t in zip(REST, turn))
        body.keyframe_insert("rotation_euler", frame=frame)


def flip_turn(degrees, axis=None):
    """A turn of `degrees` about the spec's flip axis (x: end over end, like a coin; y: a cartwheel; z: a twirl)."""
    axis = axis or MOTION["flip"]
    if axis == "none":
        return (0, 0, 0)
    return {"x": (-degrees, 0, 0), "y": (0, degrees, 0), "z": (0, 0, degrees)}[axis]


def face(frame, name):
    """Switch the face at a frame: open, happy, closed, or any face named in the spec."""
    shown = set(FACES.get(name, []))
    for objs in FACES.values():
        for ob in objs:
            ob.hide_render = ob not in shown
            ob.keyframe_insert("hide_render", frame=frame)


def eyes(frame, wide=1.0, tall=1.0, look=(0.0, 0.0)):
    """Key the open eyes: scale (surprised 1.3, squint tall 0.55) and glance (look, in body units). A glance slides
    each eye along its piece's surface, so on a round body it doesn't sink in."""
    for e in EYES:
        g = e["group"]
        centre = origin_of(e["on"])
        x, z = e["x"] + look[0], e["z"] + look[1]
        fy = front_y(e["on"], centre.x + x, centre.z + z)
        g.scale = (wide, 1, tall)
        g.location = (e["base"].x + look[0], e["base"].y + ((fy - front_y(e["on"], centre.x + e["x"], centre.z + e["z"]))
                                                             if fy is not None else 0), e["base"].z + look[1])
        g.keyframe_insert("scale", frame=frame)
        g.keyframe_insert("location", frame=frame)


def blink(frame):
    eyes(frame)
    for e in EYES:
        g = e["group"]
        g.scale = (1, 1, 0.08)
        g.keyframe_insert("scale", frame=frame + 4)
    eyes(frame + 9)


def part_pose(name, frame, turn=None, at=None, scale=None):
    """Key a part (by name) at a frame: turn about its pivot (x, y, z degrees from its rest), move it, or scale it."""
    if name not in PARTS:
        sys.exit(f"no part named '{name}'")
    p = PARTS[name]
    pv = p["pivot"]
    if turn is not None:
        pv.rotation_euler = tuple(r + math.radians(t) for r, t in zip(p["rest"], turn))
        pv.keyframe_insert("rotation_euler", frame=frame)
    if at is not None:
        pv.location = Vector(at)
        pv.keyframe_insert("location", frame=frame)
    if scale is not None:
        pv.scale = scale if isinstance(scale, (list, tuple)) else (scale,) * 3
        pv.keyframe_insert("scale", frame=frame)


def jiggle(frame, amount=1.0):
    """Follow-through: every part with a `jiggle` swings and settles after a jolt at `frame` (a landing, a stop)."""
    k = amount * MOTION.get("jiggle", 1.0)
    for name, p in PARTS.items():
        deg = p["jiggle"] * k
        if not deg:
            continue
        axis = "xyz".index(p["axis"])
        for df, f in ((0, 0), (4, 1), (9, -0.55), (14, 0.25), (19, -0.08), (24, 0)):
            t = [0, 0, 0]
            t[axis] = deg * f
            part_pose(name, frame + df, turn=t)


def every_frame(first, last, fn):
    """Key on every frame, from two before to two after: Blender eases between keys, so a constant-speed loop (a spin)
    needs a key on each frame to stay even across its seam."""
    for f in range(first - 2, last + 3):
        fn(f)


def render(first, last):
    if OPT.get("frames"):
        a, b = (int(v) for v in str(OPT["frames"]).split("-"))
        first, last = max(first, a), min(last, b)
    scene.frame_start, scene.frame_end = first, last
    scene.frame_step = int(OPT.get("step", 1))
    scene.render.filepath = os.path.join(OUT, "f_")
    bpy.ops.render.render(animation=True)
    final = last - (last - first) % scene.frame_step
    src = os.path.join(OUT, f"f_{final:04d}.png")
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(OUT, "last.png"))
    print(f"RENDERED {SHOT}: frames {first}-{last} at {FPS} fps ({(last - first + 1) / FPS:.2f} s) into {OUT}")


def still(name, frame=1):
    scene.frame_set(frame)
    scene.render.filepath = os.path.join(OUT, f"{name}.png")
    bpy.ops.render.render(write_still=True)


# MARK: Effects: flat shapes around the mascot that pop, rise and fade (sparkles, bursts, hearts, z's, dots)

FX = SPEC["effects"]
FX_SIZE = FX.get("size", 1.0)
FX_FILL = flat("Effect", colour(FX.get("color", "accent")))
FX_EDGE = flat("Effect edge", colour(FX["outline"])) if FX.get("outline") else None
FRONT = -(DEPTH + 0.6)          # effects float in front of the body


def fan_mesh(name, points):
    """A flat shape in the XZ plane from its outline, fanned from its centre (stars, hearts)."""
    bm = bmesh.new()
    centre = bm.verts.new((0, 0, 0))
    ring = [bm.verts.new((x, 0, z)) for x, z in points]
    for k in range(len(ring)):
        bm.faces.new((centre, ring[k], ring[(k + 1) % len(ring)]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def star_points(r):
    return [((r if k % 2 == 0 else r * 0.36) * math.sin(k * math.pi / 4),
             (r if k % 2 == 0 else r * 0.36) * math.cos(k * math.pi / 4)) for k in range(8)]


def heart_points(r):
    pts = []
    for k in range(48):
        t = 2 * math.pi * k / 48
        x = 16 * math.sin(t) ** 3
        z = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * r / 16, (z + 2) * r / 16))
    return pts


def capsule_points(length, width):
    pts = []
    for k in range(12):
        a = math.pi * k / 11
        pts.append((width / 2 * math.cos(a), length / 2 + width / 2 * math.sin(a)))
    for k in range(12):
        a = math.pi + math.pi * k / 11
        pts.append((width / 2 * math.cos(a), -length / 2 + width / 2 * math.sin(a)))
    return pts


def effect(name, me_fill, me_edge, at, rot=0.0):
    """One effect sprite, facing the camera, at world (x, z), hidden (scale 0) until animated."""
    root = link(bpy.data.objects.new(name, None))
    root.location = (at[0], FRONT, at[1])
    root.rotation_euler = (0, math.radians(rot), 0)
    fill = link(bpy.data.objects.new(name + " fill", me_fill))
    me_fill.materials.append(FX_FILL)
    fill.parent = root
    if FX_EDGE is not None and me_edge is not None:
        edge = link(bpy.data.objects.new(name + " edge", me_edge))
        me_edge.materials.append(FX_EDGE)
        edge.parent = root
        edge.location = (0, 0.01, 0)
    root.scale = (0, 0, 0)
    root.keyframe_insert("scale", frame=1)
    return root


def sprite(kind, name, at, size, rot=0.0):
    s = size * FX_SIZE
    if kind == "star":
        return effect(name, fan_mesh(name, star_points(s)), fan_mesh(name + "e", star_points(s * 1.32)), at, rot)
    if kind == "heart":
        return effect(name, fan_mesh(name, heart_points(s)), fan_mesh(name + "e", heart_points(s * 1.22)), at, rot)
    if kind == "line":
        return effect(name, fan_mesh(name, capsule_points(s, s * 0.32)),
                      fan_mesh(name + "e", capsule_points(s * 1.12, s * 0.32 + 0.05)), at, rot)
    if kind == "dot":
        return effect(name, ellipse_mesh(name, s, s, rings=2), ellipse_mesh(name + "e", s + 0.03, s + 0.03, rings=2),
                      at, rot)
    if kind == "z":
        cu = bpy.data.curves.new(name, "FONT")
        cu.body = "z"
        cu.size = s * 2.2
        cu.align_x, cu.align_y = "CENTER", "CENTER"
        cu.offset = 0
        tmp = link(bpy.data.objects.new(name + "tmp", cu))
        tmp.rotation_euler = (math.pi / 2, 0, 0)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
        me.transform(tmp.matrix_basis)
        cu.offset = 0.03
        dg = bpy.context.evaluated_depsgraph_get()
        me_e = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
        me_e.transform(tmp.matrix_basis)
        bpy.data.objects.remove(tmp)
        return effect(name, me, me_e, at, rot)
    sys.exit(f"unknown effect '{kind}'")


def pop(ob, frame, hold=10, peak=1.0):
    """Scale an effect up with a little overshoot, hold it, and shrink it away."""
    for f, s in ((frame - 1, 0), (frame + 4, peak * 1.25), (frame + 7, peak), (frame + 7 + hold, peak),
                 (frame + 13 + hold, 0)):
        ob.scale = (s, s, s)
        ob.keyframe_insert("scale", frame=f)


def drift(ob, frame, dx, dz, length):
    start = ob.location.copy()
    ob.keyframe_insert("location", frame=frame)
    ob.location = (start.x + dx, start.y, start.z + dz)
    ob.keyframe_insert("location", frame=frame + length)


def sparkles(frame, count=4, radius=None):
    """Stars popping around the mascot, one after another (something good)."""
    if not EFFECTS:
        return
    radius = radius or HALF_HEIGHT * 1.45
    for k in range(count):
        a = math.radians(-70 + 140 * k / max(count - 1, 1) + (12 if k % 2 else -12))
        at = (math.sin(a) * radius * 1.15, math.cos(a) * radius * 0.85 + REST_UP)
        pop(sprite("star", f"Sparkle{frame}_{k}", at, 0.13 + 0.06 * ((k + 1) % 3)), frame + 3 * k, hold=12)


def burst(frame, count=3):
    """Short lines bursting out above the head (surprise, alarm)."""
    if not EFFECTS:
        return
    for k in range(count):
        deg = (k - (count - 1) / 2) * 32
        a = math.radians(deg)
        r = HALF_HEIGHT + 0.42
        ob = sprite("line", f"Burst{frame}_{k}", (math.sin(a) * r * 1.1, math.cos(a) * r + REST_UP), 0.26, rot=deg)
        pop(ob, frame + k, hold=16)


def hearts(frame, count=3):
    """Hearts rising and fading (love, thanks)."""
    if not EFFECTS:
        return
    for k in range(count):
        x = (-0.7, 0.75, 0.05)[k % 3] * HALF_HEIGHT
        ob = sprite("heart", f"Heart{frame}_{k}", (x, HALF_HEIGHT * 0.9 + REST_UP), 0.16 + 0.04 * (k % 2))
        pop(ob, frame + 8 * k, hold=26)
        drift(ob, frame + 8 * k, 0.1 * (1 if x > 0 else -1), 0.7, 40)


def impact(frame):
    """Short lines either side of the base as it lands hard."""
    if not EFFECTS:
        return
    for k, side in enumerate((-1, 1)):
        for j, tilt in enumerate((-25, 0, 25)):
            a = math.radians(90 + tilt) * side
            x = side * (1.25 + 0.12 * abs(j - 1))
            ob = sprite("line", f"Impact{frame}_{k}{j}", (x, BOTTOM + 0.15 + 0.22 * (1 - j) + REST_UP), 0.2,
                        rot=90 * side + tilt * side)
            pop(ob, frame, hold=4)


def thinking_dots(frame):
    """Three dots appearing one by one above and to the right (thinking)."""
    if not EFFECTS:
        return
    for k in range(3):
        ob = sprite("dot", f"Dot{frame}_{k}", (0.75 + 0.3 * k, HALF_HEIGHT + 0.3 + 0.18 * k + REST_UP), 0.06 + 0.02 * k)
        pop(ob, frame + 10 * k, hold=70 - 10 * k)


def zs_loop(period):
    """Two z's drifting up and to the right, half a period apart, looping seamlessly (asleep)."""
    if not EFFECTS:
        return
    for k in range(2):
        ob = sprite("z", f"Z{k}", (0.8, HALF_HEIGHT + 0.1 + REST_UP), 0.12 + 0.05 * k)
        base = ob.location.copy()
        phase = (k * period) // 2
        wrap = period - phase + 1 if phase else None
        frames = set(range(1, period + 2, 6)) | {period + 1}
        if wrap:
            frames |= {wrap - 1, wrap}
        for f in sorted(frames):
            # How far through its rise this z is; it restarts (at zero size, so unseen) when it reaches the top.
            t = ((f - 1 + phase) % period) / period
            ob.location = (base.x + 0.35 * t, base.y, base.z + 0.8 * t)
            s = math.sin(math.pi * t)
            ob.scale = (s, s, s)
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("scale", frame=f)


# MARK: Shots

def start_pose():
    pose(1, up=0, turn=(0, 0, 0), squash=0)
    face(1, "open")
    if EYES:
        eyes(1)
    for name in PARTS:
        part_pose(name, 1, turn=(0, 0, 0))


start_pose()
HOP = MOTION["hop"]
SQ = MOTION["squash"]
TURN = 360 * MOTION.get("flips", 1) if MOTION["flip"] != "none" else 0


def wave_part():
    """The part the wave shot lifts: motion.wave, or else an arm, hand, wing, paw or flipper, preferring the one on the
    side the rest pose turns towards the camera, so the raised arm isn't hidden behind the body."""
    named = MOTION.get("wave")
    if named:
        return named
    found = [n for n in PARTS if any(w in n.lower() for w in ("arm", "hand", "wing", "paw", "flipper"))]
    if not found:
        return None
    near = [n for n in found if PARTS[n]["at"].x * SPEC["rest"][2] < 0]
    return (near or found)[0]


if OPT.get("shot-file"):
    with open(OPT["shot-file"]) as fh:
        exec(compile(fh.read(), OPT["shot-file"], "exec"), globals())

elif SHOT == "check":
    # The model from six angles, then each face, as stills: look at these before animating anything.
    for n, (rx, rz) in enumerate([(0, 0), (-15, 25), (-35, 50), (-90 if FLAT_FRONT else -20, 0), (0, 90), (0, 180)]):
        body.rotation_euler = (REST[0] + math.radians(rx), REST[1], REST[2] + math.radians(rz))
        body.keyframe_insert("rotation_euler", frame=1)
        still(f"angle_{n}")
    body.rotation_euler = REST
    body.keyframe_insert("rotation_euler", frame=1)
    for name in FACES:
        face(1, name)
        still(f"face_{name}")
    face(1, "open")
    if EYES:
        eyes(1, 1.3, 1.3)
        still("face_surprised")
        eyes(1, 1.0, 0.55)
        still("face_squint")
        eyes(1, look=(0.08, 0.05))
        still("face_glance")
    print(f"RENDERED check into {OUT}")

elif SHOT == "idle":
    # A 4 s loop: a gentle bob and sway, a blink, a glance up and to the right and back. Ends where it starts.
    for f, z, sway in ((1, 0, 0), (60, 0.05, 2), (120, 0, 0), (180, 0.05, -2), (240, 0, 0)):
        pose(f, up=z, turn=(0, 0, sway))
    for name, p in PARTS.items():
        if p["jiggle"]:
            axis = "xyz".index(p["axis"])
            for f, k in ((1, 0), (60, 0.3), (120, 0), (180, -0.3), (240, 0)):
                t = [0, 0, 0]
                t[axis] = p["jiggle"] * k
                part_pose(name, f, turn=t)
    if EYES:
        blink(90)
        eyes(150)
        eyes(158, look=(0.07, 0.04))
        eyes(196, look=(0.07, 0.04))
        eyes(206)
    render(1, 240)

elif SHOT == "hop":
    # Something good: a crouch, a jump (with a turn if the spec has one), a squashy landing, happy eyes. 1 s.
    pose(5, up=0, squash=SQ)
    pose(8, up=0, squash=-SQ * 0.6)
    pose(22, up=HOP, turn=tuple(t * 0.53 for t in flip_turn(TURN)), squash=-SQ * 0.3)
    pose(36, up=0, turn=flip_turn(TURN), squash=0)
    pose(39, up=0, squash=SQ * 1.25)
    pose(44, up=0, squash=-SQ * 0.35)
    pose(50, up=0, squash=0)
    face(37, "happy")
    jiggle(36)
    sparkles(30)
    render(1, 60)

elif SHOT == "celebrate":
    # A big moment: a small hop, then a big one with a double turn, happy, with sparkles. 1.8 s.
    big = flip_turn(720) if MOTION["flip"] != "none" else (0, 0, 720)
    pose(4, up=0, squash=SQ)
    pose(7, up=0, squash=-SQ * 0.5)
    pose(18, up=HOP * 0.45, squash=0)
    pose(28, up=0, squash=SQ * 1.1)
    pose(31, up=0, squash=-SQ * 0.7)
    pose(50, up=HOP * 1.3, turn=tuple(t * 0.55 for t in big), squash=-SQ * 0.3)
    pose(70, up=0, turn=big, squash=0)
    pose(73, up=0, squash=SQ * 1.4)
    pose(80, up=0, squash=-SQ * 0.4)
    pose(88, up=0, squash=0)
    face(26, "happy")
    jiggle(28, 0.6)
    jiggle(70)
    sparkles(44, count=5)
    impact(70)
    render(1, 108)

elif SHOT == "bounce":
    # Excited: two quick hops per second, happy, as a seamless 1 s loop.
    face(1, "happy")
    for base in (1, 31):
        pose(base, up=0, squash=0)
        pose(base + 4, up=0, squash=SQ)
        pose(base + 7, up=0, squash=-SQ * 0.5)
        pose(base + 16, up=HOP * 0.35, squash=0, turn=(0, 0, 4 if base == 1 else -4))
        pose(base + 26, up=0, squash=SQ * 0.6, turn=(0, 0, 0))
    pose(61, up=0, squash=0)
    jiggle(27, 0.5)
    render(1, 60)

elif SHOT == "dip":
    # Something removed or sad: it sinks and bows, eyes closed, then comes back up. 0.8 s.
    pose(10, up=-0.16, turn=(22, 0, 0))
    pose(30, up=-0.16, turn=(22, 0, 0))
    pose(44, up=0, turn=(0, 0, 0))
    face(7, "closed")
    face(34, "open")
    jiggle(10, 0.5)
    render(1, 48)

elif SHOT == "undo":
    # Undone: one turn back the other way with a hop, landing where it was. 0.9 s.
    back = tuple(-t for t in flip_turn(360)) if MOTION["flip"] != "none" else (0, 0, -360)
    pose(5, up=0, squash=SQ)
    pose(8, up=0, squash=-SQ * 0.5)
    pose(22, up=HOP * 0.75, turn=tuple(t * 0.55 for t in back), squash=0)
    pose(34, up=0, turn=back)
    pose(37, up=0, squash=SQ)
    pose(44, up=0, squash=0)
    jiggle(34)
    render(1, 54)

elif SHOT == "surprised":
    # Needs attention: a stretch upwards, eyes pop, a startled wobble, then calm. 1 s.
    pose(3, up=0, squash=SQ * 0.6)
    pose(7, up=0.38, squash=-SQ * 1.2)
    pose(14, up=0, squash=SQ * 0.8)
    pose(19, up=0, squash=0)
    for f, deg in ((14, 0), (17, 7), (21, -5), (25, 3), (29, -1.5), (33, 0)):
        pose(f, turn=(0, 0, deg) if MOTION["shake"] != "y" else (0, deg, 0))
    if EYES:
        eyes(3)
        eyes(7, 1.32, 1.32)
        eyes(48, 1.32, 1.32)
        eyes(56)
    jiggle(14)
    burst(6)
    render(1, 60)

elif SHOT == "shake":
    # Something went wrong: a small "no", eyes squinting. 0.7 s.
    for f, deg in ((1, 0), (5, 24), (10, -22), (15, 16), (20, -10), (25, 4), (30, 0)):
        pose(f, turn=(0, deg, 0) if MOTION["shake"] == "y" else (0, 0, deg * 0.8))
    if EYES:
        eyes(3)
        eyes(6, 1.0, 0.55)
        eyes(28, 1.0, 0.55)
        eyes(34)
    jiggle(30, 0.5)
    render(1, 42)

elif SHOT == "nod":
    # Yes, or done: two nods forward. 0.7 s.
    for f, deg in ((1, 0), (7, 16), (14, -4), (21, 12), (28, -2), (34, 0)):
        pose(f, turn=(deg, 0, 0))
    face(4, "happy")
    face(36, "open")
    jiggle(14, 0.4)
    render(1, 42)

elif SHOT == "think":
    # Thinking: it tilts, looks up and to the left, taps a little, and comes back. 2.2 s.
    pose(10, turn=(0, 0, 0))
    pose(22, up=0.04, turn=(-6, -8, -10))
    pose(110, up=0.04, turn=(-6, -8, -10))
    pose(124, up=0, turn=(0, 0, 0))
    for f in (40, 56, 72):
        pose(f, up=0.04, squash=0.0)
        pose(f + 4, up=0.04, squash=SQ * 0.35)
        pose(f + 8, up=0.04, squash=0.0)
    if EYES:
        eyes(10)
        eyes(20, look=(-0.08, 0.07))
        eyes(108, look=(-0.08, 0.07))
        eyes(120)
        blink(124)
    thinking_dots(30)
    render(1, 132)

elif SHOT == "love":
    # Love or thanks: a happy squish and sway, with hearts rising. 1.6 s.
    face(4, "happy")
    pose(6, squash=SQ)
    pose(14, squash=-SQ * 0.5, up=0.08)
    pose(22, squash=0, up=0)
    for f, deg in ((22, 0), (36, 6), (52, -6), (68, 4), (82, 0)):
        pose(f, turn=(0, deg, 0))
    pose(96, squash=0)
    jiggle(22, 0.6)
    hearts(10)
    render(1, 96)

elif SHOT == "wave":
    # Hello: with an arm (or wing or paw) it lifts and waves it; without one, it rocks side to side happily. 1.6 s.
    arm = wave_part()
    face(6, "happy")
    pose(4, squash=SQ * 0.5)
    pose(10, up=0.08, squash=-SQ * 0.3)
    pose(18, up=0, squash=0)
    if arm:
        side = 1 if PARTS[arm]["at"].x >= 0 else -1
        part_pose(arm, 6, turn=(0, 0, 0))
        lift = MOTION.get("wave_lift", 145)
        part_pose(arm, 14, turn=(0, -lift * side, 0))
        for k, f in enumerate(range(20, 76, 9)):
            part_pose(arm, f, turn=(0, (-lift + (18 if k % 2 == 0 else -18)) * side, 0))
        part_pose(arm, 80, turn=(0, -lift * side, 0))
        part_pose(arm, 90, turn=(0, 0, 0))
    else:
        for f, deg in ((18, 0), (28, 10), (40, -10), (52, 8), (64, -6), (76, 0)):
            pose(f, turn=(0, deg, 0))
    face(88, "open")
    render(1, 96)

elif SHOT == "peek":
    # Curious: rises from the bottom edge, looks left and right, ducks back down. 2 s.
    low = -(HALF_H + HALF_HEIGHT * 1.2 + REST_UP)
    pose(1, up=low, squash=0)
    pose(18, up=-0.2, squash=-SQ * 0.4)
    pose(26, up=-0.3, squash=SQ * 0.3)
    pose(32, up=-0.28, squash=0)
    if EYES:
        eyes(36)
        eyes(44, look=(-0.08, 0))
        eyes(70, look=(-0.08, 0))
        eyes(78, look=(0.08, 0))
        eyes(100, look=(0.08, 0))
        eyes(106)
        blink(108)
    pose(112, up=-0.28)
    pose(124, up=low)
    render(1, 124)

elif SHOT == "spin":
    # Busy or loading: a full turn every spin_seconds about spin_axis (y keeps the face towards you), a seamless loop.
    frames = max(int(round(MOTION.get("spin_seconds", 1.0) * FPS)), 8)
    whole = flip_turn(360, MOTION.get("spin_axis", "y"))
    every_frame(1, frames, lambda f: pose(f, turn=tuple(t * (f - 1) / frames for t in whole)))
    render(1, frames)

elif SHOT == "sleepy":
    # Paused or idle for long: tipped back, eyes closed, breathing slowly, z's rising. A 3.6 s loop.
    face(1, "closed")
    for f, sq, sway in ((1, 0, 0), (54, -0.025, 2), (108, 0.02, 0), (162, -0.025, -2), (216, 0, 0)):
        pose(f, up=0, turn=(-10, 0, sway), squash=sq)
    zs_loop(216)
    render(1, 216)

elif SHOT == "wake":
    # Waking up: eyes open wide, a jump, back to rest. 0.8 s. Starts where sleepy is.
    face(1, "closed")
    pose(1, up=0, turn=(-10, 0, 0), squash=0)
    face(10, "open")
    if EYES:
        eyes(10, 1.3, 1.3)
        eyes(40)
    pose(12, up=0, squash=SQ)
    pose(20, up=0.32, turn=(0, 0, 0), squash=-SQ * 0.4)
    pose(30, up=0, squash=SQ)
    pose(38, up=0, squash=0)
    jiggle(30)
    burst(14)
    render(1, 48)

elif SHOT == "entrance":
    # Hello on opening: tumbles up from below the frame, settles with a soft overshoot, blinks, glances. 2 s.
    whole = flip_turn(1080) if MOTION["flip"] != "none" else (0, 0, 720)
    lead = tuple(t * (900 / 1080) for t in whole)
    pose(1, up=-(HALF_H + HALF_HEIGHT * 1.6 + REST_UP), turn=tuple(-t * 0.08 for t in whole), squash=0)
    pose(34, up=0.55, turn=lead)
    pose(58, up=-0.08, turn=tuple(t + o for t, o in zip(whole, flip_turn(-8))), squash=0.03)
    pose(66, up=0.03, turn=tuple(t + o for t, o in zip(whole, flip_turn(3))), squash=-0.01)
    pose(74, up=0, turn=whole, squash=0)
    jiggle(58)
    impact(58)
    if EYES:
        blink(86)
        eyes(100)
        eyes(106, look=(0.07, 0.04))
    render(1, 124)

elif SHOT == "exit":
    # Goodbye: a crouch and a jump up and out of the top of the frame, turning. 0.8 s.
    pose(4, up=0, squash=SQ)
    pose(9, up=0, squash=SQ * 1.3)
    pose(13, up=0.1, squash=-SQ * 1.2)
    pose(40, up=HALF_H + HALF_HEIGHT * 1.6 + 0.5, turn=tuple(t * 0.75 for t in flip_turn(TURN or 360)), squash=-SQ * 0.4)
    face(6, "happy")
    render(1, 48)

else:
    sys.exit(f"unknown shot '{SHOT}'; use check, idle, hop, celebrate, bounce, dip, undo, surprised, shake, nod, "
             f"think, love, wave, peek, spin, sleepy, wake, entrance, exit, or --shot-file")
