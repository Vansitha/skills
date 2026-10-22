# The look

Three looks cover most mascots. The flat and toon looks keep the colours exact by drawing everything unlit. The soft look trades a little of that exactness for real light.

## A flat sticker

Use it for a logo-like mascot: a coin, a badge, a brand mark, a black-and-white character.

- `"shading": "flat"`, with a bold outline (0.08 to 0.1) in a dark or contrasting colour.
- A thick body (`disc`, `box`, `path`) with `palette.edge` set to `line`. The side then reads as the sticker's thickness, and shows when the body turns.
- `edge_highlight: true` puts a crisp white band on the side as it catches the light. On a coin, `reeding` adds stripes that turn with it.
- Eyes in `bite` style, with the notch at the lower left (`shine.at: [-0.8, -0.1]`), so the eyes look up and right.
- Rest pose `[-12, 0, 12]`, so the side shows at the lower left.

## A toon character

Use it for a character with colour: an animal, a creature, a robot, a plant.

- `"shading": "toon"`: one darker band (`shadow_tint` 0.75 to 0.85) away from the light, starting at `band` 0.4 to 0.5.
- `highlight: true` with `highlight_at` 0.96 to 0.97: one glossy spot at the upper left.
- A thin outline (0.04 to 0.06) in a deep shade of the fill's hue, not pure black: dark green on green, plum on lilac.
- `dot` eyes with a white shine, cheeks in `blush`, and a small smile.
- A round body (a `blob` with `roundness` 2.3 to 2.8 reads as a marshmallow), with parts made of spheres, capsules and cones.
- Rest pose `[-6, 0, 10]`.

## A soft toy

Use it for food, products and toys: something that should look touchable and a little glossy, like vinyl or plastic.

- `"shading": "soft"`: real light from one sun and a soft ambient fill, with no hard bands. `roughness` is 0.3 to 0.5 for plastic and 0.6 to 0.8 for felt or fabric.
- A thin outline (0.03 to 0.04), or none (0).
- Colours come out a little darker in shade and lighter in the light than the hex, so pick the fill a step brighter than you want it to read.
- Faces and marks stay flat: they're decals, not lit.
- `examples/berry.json` is one.

## Borders for dark screens

A dark outline disappears on a dark background. `"border": {"width": 0.07, "color": "#FFFFFF"}` adds a second band outside the outline, round the body and every part, like the cut edge of a sticker. It reads on any background, and is often enough to skip a dark variant.

- Use white or a cream that matches the app.
- 0.05 is subtle, 0.08 is a bold die-cut sticker.
- Check it on the darkest background it will play on: `encode.sh sheet ... --bg "#1C1C1E"`.

## A 2D design made 3D

When the mascot already exists as a flat drawing, trace its outline as an SVG path. Take it from the `mascot` skill's spec or from an SVG file's `d`, or write it from the reference with M, C and Z. Then use `"shape": "path"`.

- A half-thickness of 0.15 to 0.25, a bevel of 0.06 to 0.1, and an edge colour a step darker than the fill make a puffy sticker.
- Measure the eye positions from the drawing: x from the centre over the half-width, z likewise, with up positive.
- Parts that stick out of the drawing (ears, arms) can stay in the silhouette, or come out as parts so they can move. Parts move better.

## A model from elsewhere

`"shape": "file"` takes a `.glb`, `.gltf`, `.obj` or `.fbx` for the body or any part. Use it for a shape the primitives can't make: a detailed head, a sculpted character, an existing brand model.

- It's merged into one mesh and scaled to the body's width. Export each moving piece as its own file and make it a part.
- It needs a closed mesh with its normals pointing out, or the outline breaks up.
- Its own materials are replaced by the palette colours.

## Fixes

| What you see | Fix |
|---|---|
| The whole body is one dark tone in toon shading | Lights must not cast shadows: the outline shell blocks the sun. The script turns shadows off; if you change the light, keep `use_shadow = False`. |
| Washed-out colours | The view transform isn't Standard (AgX and Filmic desaturate). The script sets Standard; keep it if you edit the scene. |
| The soft look is murky | Raise the fill's brightness, or move `light` more to the front. |
| The outline looks scribbly, or has gaps | The mesh isn't closed, or its normals point in (common with imported models). Close the holes, or recalculate the normals outward, before export. Or thin `outline`. |
| A feature floats beside its piece, with a WARNING | Part of it misses the piece. Move it in, or shrink it. |
| A part floats away from the body, or sinks into it | Move its `at` in or out. Parts should overlap the body a little where they join, and the outline hides the seam. |
| A part swings from the wrong place | Set its `pivot` to where it joins: the shoulder, the root, the base. |
| A raised arm hides behind the body | The rest pose turns that side away. Wave the arm on the near side (`motion.wave`), or lower `wave_lift`. |
| Eyes look small or cross-eyed at rest | The rest pose turns the face. Move the eyes a little towards the turn, or reduce `rest`. |
| A white eye vanishes on a white body | `pupil` eyes need a body that isn't white. Use `dot` or `bite` instead, or tint the fill. |
| A mark covers the eyes | Lower its `lift` below 1 (a screen at 0.3). |
| The side looks flat on a coin | Turn on `edge_highlight` and `reeding`, and make sure `edge` differs from `fill`. |
| The body looks lumpy | A `blob` with a high `roundness` has corners, so bring it towards 2.4. For a `path`, add points where curves meet so the joins are smooth. |
| It's too small in the frame | Lower `camera.frame`, but keep room for the hop: the body plus `hop` plus a margin. |
| Ears or a waving arm leave the frame | Raise `camera.frame` to 5 or 5.5. |
| A negative variant's eyes look the wrong way | Mirror `eyes.shine.at` in the variant. |
| Toon bands are on the wrong side | Change `look.light`. The sun points down its −Z; `[55, -35, -20]` lights from the upper left, in front. |
