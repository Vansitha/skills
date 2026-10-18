"""A 3D mascot lit from within: a starting point for the Blender route (see ../blender.md).

Run: /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P blender_glow.py -- out.png R G B
Builds a soft spirit from metaballs (a round head melting into a curled tail), shades it by emission (its
colour in the middle, a white fresnel glow at the edges, a faint gloss), adds flat disc eyes and a gold halo,
and renders 1024 x 1024 on a transparent background in about five seconds. Put the background behind it with
render.swift (an "image" is not a spec shape yet) or any image editor. Change the metaball list for another
shape.
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
BODY = tuple(float(v) for v in argv[1:4]) + (1.0,)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
for engine in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        scene.render.engine = engine
        break
    except TypeError:
        continue
scene.render.resolution_x = scene.render.resolution_y = 1024
scene.render.film_transparent = True
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
if hasattr(scene, "eevee"):
    scene.eevee.taa_render_samples = 128


def node(tree, kind, **inputs):
    n = tree.nodes.new(kind)
    for key, value in inputs.items():
        n.inputs[key].default_value = value
    return n


def shader(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    tree = mat.node_tree
    tree.nodes.remove(tree.nodes["Principled BSDF"])
    return mat, tree, tree.nodes["Material Output"]


def glow_body(color):
    """Body colour inside, white glow along the edges, a little gloss on top."""
    mat, tree, out = shader("Glow")
    layer = node(tree, "ShaderNodeLayerWeight", Blend=0.62)
    rim = node(tree, "ShaderNodeMath")
    rim.operation = "POWER"
    rim.inputs[1].default_value = 1.9
    tree.links.new(layer.outputs["Facing"], rim.inputs[0])
    gain = node(tree, "ShaderNodeMath")
    gain.operation = "MULTIPLY"
    gain.inputs[1].default_value = 1.15
    tree.links.new(rim.outputs[0], gain.inputs[0])
    core = node(tree, "ShaderNodeEmission", Strength=1.0)
    geo = node(tree, "ShaderNodeNewGeometry")
    sep = node(tree, "ShaderNodeSeparateXYZ")
    tree.links.new(geo.outputs["Normal"], sep.inputs[0])
    span = node(tree, "ShaderNodeMapRange")
    span.inputs["From Min"].default_value = -1.0
    tree.links.new(sep.outputs["Z"], span.inputs["Value"])
    shade = tree.nodes.new("ShaderNodeValToRGB")
    shade.color_ramp.elements[0].position = 0.15
    shade.color_ramp.elements[0].color = tuple(c * 0.78 for c in color[:3]) + (1,)
    shade.color_ramp.elements[1].position = 0.85
    shade.color_ramp.elements[1].color = tuple(c * 0.92 + 0.08 for c in color[:3]) + (1,)
    tree.links.new(span.outputs[0], shade.inputs[0])
    tree.links.new(shade.outputs["Color"], core.inputs["Color"])
    edge = node(tree, "ShaderNodeEmission", Color=(1, 1, 1, 1))
    tree.links.new(gain.outputs[0], edge.inputs["Strength"])
    # A faint gloss: a glossy shader at 18% (a transparent mix would let the background through).
    gloss_amount = node(tree, "ShaderNodeBsdfGlossy", Color=(0.18, 0.18, 0.18, 1), Roughness=0.22)
    add1 = node(tree, "ShaderNodeAddShader")
    add2 = node(tree, "ShaderNodeAddShader")
    tree.links.new(core.outputs[0], add1.inputs[0])
    tree.links.new(edge.outputs[0], add1.inputs[1])
    tree.links.new(add1.outputs[0], add2.inputs[0])
    tree.links.new(gloss_amount.outputs[0], add2.inputs[1])
    tree.links.new(add2.outputs[0], out.inputs["Surface"])
    return mat


def flat_color(name, color):
    mat, tree, out = shader(name)
    e = node(tree, "ShaderNodeEmission", Color=color, Strength=1.0)
    tree.links.new(e.outputs[0], out.inputs["Surface"])
    return mat


def gold():
    """Orange underneath, warm yellow on top, plus a bright gloss."""
    mat, tree, out = shader("Gold")
    geo = node(tree, "ShaderNodeNewGeometry")
    sep = node(tree, "ShaderNodeSeparateXYZ")
    tree.links.new(geo.outputs["Normal"], sep.inputs[0])
    ramp = tree.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.98, 0.52, 0.04, 1)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (1.0, 0.86, 0.22, 1)
    to01 = node(tree, "ShaderNodeMapRange")
    to01.inputs["From Min"].default_value = -1.0
    tree.links.new(sep.outputs["Z"], to01.inputs["Value"])
    tree.links.new(to01.outputs[0], ramp.inputs[0])
    e = node(tree, "ShaderNodeEmission", Strength=1.0)
    tree.links.new(ramp.outputs["Color"], e.inputs["Color"])
    gloss = node(tree, "ShaderNodeBsdfGlossy", Color=(1, 1, 1, 1), Roughness=0.18)
    add = node(tree, "ShaderNodeAddShader")
    tree.links.new(e.outputs[0], add.inputs[0])
    tree.links.new(gloss.outputs[0], add.inputs[1])
    tree.links.new(add.outputs[0], out.inputs["Surface"])
    return mat


# Body: metaballs melt a round head, a soft middle and a tapering, curling tail into one shape.
mball = bpy.data.metaballs.new("Body")
mball.resolution = 0.02
mball.render_resolution = 0.012
mball.threshold = 0.6
body = bpy.data.objects.new("Body", mball)
scene.collection.objects.link(body)
for (x, z, r) in [
    (0.0, 0.35, 1.62),
    (0.0, -0.25, 1.35),
    (0.1, -0.7, 1.05),
    (0.35, -0.98, 0.78),
    (0.62, -1.1, 0.56),
    (0.86, -1.12, 0.4),
    (1.06, -1.05, 0.29),
    (1.2, -0.95, 0.2),
    (1.27, -0.84, 0.13),
]:
    e = mball.elements.new()
    e.co = (x, 0.0, z)
    e.radius = r
    e.stiffness = 2.0
body.scale = (1.0, 0.8, 1.0)
body.data.materials.append(glow_body(BODY))
bpy.context.view_layer.objects.active = body
body.select_set(True)
bpy.ops.object.convert(target="MESH")
body = bpy.context.view_layer.objects.active
bpy.ops.object.shade_smooth()

front = min(v.co.y for v in body.data.vertices) * body.scale.y
top = max(v.co.z for v in body.data.vertices) * body.scale.z


def disc(name, x, z, depth, rx, rz, material, tilt=0.0):
    """A flat oval facing the camera, `depth` in front of the body's front."""
    bpy.ops.mesh.primitive_circle_add(vertices=96, fill_type="NGON", radius=1.0,
                                      location=(x, front - depth, z), rotation=(math.radians(90), math.radians(tilt), 0))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (rx, rz, 1.0)
    obj.data.materials.append(material)
    return obj


white = flat_color("White", (1, 1, 1, 1))
ink = flat_color("Ink", (0.0, 0.0, 0.0, 1))
# Two big cartoon eyes, the right one a little bigger and in front, both glancing right.
for (x, z, s, d) in [(-0.22, 0.42, 1.12, 0.02), (0.23, 0.47, 1.24, 0.05)]:
    disc("Eye", x, z, d, 0.26 * s, 0.33 * s, white, tilt=-12)
    disc("Pupil", x + 0.07 * s, z - 0.02 * s, d + 0.01, 0.19 * s, 0.25 * s, ink, tilt=-12)
    disc("Shine", x - 0.04 * s, z - 0.03 * s, d + 0.02, 0.05 * s, 0.065 * s, white)

# Halo: a gold ring floating flat above the head, tipped a little toward us.
bpy.ops.mesh.primitive_torus_add(major_radius=0.7, minor_radius=0.075, major_segments=128, minor_segments=32,
                                 location=(0.08, 0.0, top + 0.42), rotation=(math.radians(-14), math.radians(-6), 0))
bpy.ops.object.shade_smooth()
bpy.context.active_object.data.materials.append(gold())

# One soft light from the upper left, only for the gloss.
light = bpy.data.lights.new("Key", "AREA")
light.energy = 140
light.size = 5
key = bpy.data.objects.new("Key", light)
key.location = (-3.0, -5.0, 4.5)
key.rotation_euler = (Vector((0, 0, 0)) - key.location).to_track_quat("-Z", "Y").to_euler()
scene.collection.objects.link(key)
world = bpy.data.worlds.new("World")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
scene.world = world

cam_data = bpy.data.cameras.new("Camera")
cam_data.type = "ORTHO"
cam_data.ortho_scale = 4.6
cam = bpy.data.objects.new("Camera", cam_data)
cam.location = (0.1, -12.0, 0.45)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("WROTE", OUT)
