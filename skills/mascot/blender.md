# The Blender route (a true 3D look)

Use Blender when the mascot should look like a real object: clay, soft plastic, a toy with real light and shadow. For the glowing-sticker look, the 2D renderer is faster and closer. Most app-icon mascots that look 3D are 2D with glows.

Run Blender headless with a Python script:

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P scripts/blender_glow.py -- out.png 0.0 0.52 1.0
```

The three numbers are the body colour (R, G, B, from 0 to 1). A render takes about five seconds.

## What worked

- **Metaballs for soft bodies.** Elements melt into one smooth shape. Space them closer than their radius, and shrink them along a tail so it tapers. Convert to a mesh, then ray-cast from the camera to find where the face is.
- **Light from within, not from lamps.** The body's material is an emission shader in its colour (lighter on top, deeper underneath, through a colour ramp on the normal's Z), plus a white emission whose strength comes from Layer Weight → Facing, raised to about 2. That makes the frosted edge. A glossy shader at about 18% gives the shine.
- **Flat disc eyes.** NGON circles facing the camera, with emission materials: white, black and a white shine. Spheres look like marbles.
- **A gold halo from a torus.** Emission, with a colour ramp on the normal's Z (orange underneath, yellow on top) plus gloss. Lay it nearly flat (about −15 degrees on X) so it reads as a halo, not a hoop.
- **The Standard view transform.** The default (AgX/Filmic) washes out saturated colours.
- **A transparent film.** Render the character alone, and add the background and glows afterwards.

## What went wrong first

- **Overexposure.** Area lights at hundreds of watts on a scene 3 units across turn everything white. With emission shading you need almost no light: one key at about 140 W, just for the gloss.
- **A grey, matte body.** That's Principled BSDF lit by lamps. Use emission.
- **A halo standing upright.** A torus rotated about 75 degrees on X faces the camera. Keep it near flat.
- **A tail like a thumb.** Too few metaballs, ending in a thick ball. Add more elements and shrink them to a small tip.
- **The engine name.** It's `BLENDER_EEVEE_NEXT` in Blender 4.2 to 4.x and `BLENDER_EEVEE` in 5. The script tries both.
