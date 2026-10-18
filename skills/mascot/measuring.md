# Measuring a reference

Read the pixels; don't eyeball them. The measure tool prints colours and edges in the image's own pixels (x right, y down).

```bash
"$TMPDIR/mascot-measure" size   ref.png
"$TMPDIR/mascot-measure" sample ref.png 400,300 840,1250 ...
"$TMPDIR/mascot-measure" row    ref.png 700 [x0 x1]
"$TMPDIR/mascot-measure" col    ref.png 860 [y0 y1]
```

`row` and `col` print each edge as `position:colour` (the colour just past the edge). A run of white or black between two edges is an eye's white or a pupil. A pale tint is the body's glow, and the background colour on both sides marks the body's outline.

## Order

1. **The icon's box.** Run `row` across the middle and `col` down the middle. The first and last jumps from the page's colour are the icon's edges. This box is the spec's `space`.
2. **The background.** Sample near the top, the middle sides, the bottom corners, and just under the character. These give `top`, `bottom` and the darker glow under the character.
3. **The body.**
   - Sample its middle for `fill`, then sample just inside its edge at the top, both sides and the bottom for the glow colour.
   - Run `row` every 50 to 100 pixels from top to bottom, and `col` across the hem.
   - Write down each left and right edge, the top, and the low points and notches of a wavy hem.
4. **The eyes.**
   - Run `row` and `col` through each eye.
   - The white spans give each eye's box and the pupil spans give the pupil. The shine is the white island inside or beside the pupil.
   - The tilt comes from how the centre of each span shifts from row to row. A shift right going down means the top leans left: a negative `tilt`.
5. **The prop.** For a ring, the `col` spans at two x positions give its top and bottom bands. From them come the centre, `ry`, the band `width`, and the rotation, from the slope between the two centres.
6. **The sparkles.** A small jump on a quiet row or column is a dot. Note x, y and size.

## Turning points into a path

- Start at the widest point on one side and go around.
- Use one cubic curve per span between measured points.
- Put each curve's control points about a third of the way along it, on the tangent.
- Check against the measurements: a cubic's midpoint is (P0 + 3·C1 + 3·C2 + P3) / 8.
- Smooth joints matter. A kink where two curves meet shows up as a flat ledge.
