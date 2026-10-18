# The spec

One JSON file describes the whole icon. Coordinates and lengths are in the spec's `space`. Shapes draw in the order you list them.

```json
{
  "space": { "x": 0, "y": 0, "size": 1024 },
  "background": { ... },
  "shapes": [ ... ],
  "preview": { ... }
}
```

## space

The square that maps to the 1024 × 1024 icon. Use `{ "x": 0, "y": 0, "size": 1024 }` to draw from scratch. When you trace a reference, set it to the icon's box in the reference's pixels, for example `{ "x": 264, "y": 184, "size": 1152 }`, and type measurements in unchanged. The compare image crops the reference to this box.

## background

| Field | Meaning |
|---|---|
| `top`, `bottom` | Hex colours of the vertical gradient. |
| `glows` | Radial glows: `{ "x", "y", "r", "color", "alpha" }`. Use one lighter glow up and to one side, and one darker glow under the character. |
| `sparkles` | `{ "color", "alpha", "dots": [[x, y, radius], ...] }`. Eight to twelve dots, with radius 2 to 6. |

## shapes

**body.** The character's main shape.

| Field | Meaning |
|---|---|
| `path` | SVG path data. M, L, H, V, C, S, Q, T and Z are supported, in upper case and lower case. A is drawn as a straight line. |
| `fill` | Hex colour. Or use `gradient: { "top", "bottom" }` over the shape's box. |
| `shadow` | `{ "color", "alpha", "blur" }`: a soft darker copy behind the body. |
| `glow` | `{ "color", "width", "blur", "extra": [...] }`: a pale band along the inside of the edge. `extra` adds ellipses `{ "x", "y", "rx", "ry", "rotation", "color", "alpha" }` inside the glow layer, to brighten one side. |
| `rim` | `{ "color", "alpha", "width" }`: a fine bright outline. |

**eye.** `x`, `y`, `rx`, `ry` and `tilt` (degrees; negative leans the top to the left).

| Field | Meaning |
|---|---|
| `style` | `open` (the default), `happy` (an upward arc), `sleepy` or `closed` (a soft downward arc). |
| `pupil` | `{ "dx", "dy", "rx", "ry" }`, offset from the eye's centre. |
| `shine` | `{ "dx", "dy", "rx", "ry", "color" }`: the highlight. Put it on the side the eyes look away from. |
| `white`, `ink` | The colours of the eye and the pupil or arc. They default to white and near-black. |

**ring.** A flat ring such as a halo: `x`, `y`, `rx`, `ry`, `rotation`, `width`, `color`, and `highlight` for a lighter stripe along the top.

**ellipse.** `x`, `y`, `rx`, `ry`, `rotation`, `fill`, `alpha`, and `blur` (for blush or soft spots).

**path.** `path`, plus `fill` and/or `stroke` with `width` and `alpha`. Use it for a mouth, arms, a tail or a prop.

## preview

`{ "glow", "rim", "rimAlpha" }`: the outer glow's colour (the background's bottom colour by default), and the light rim inside the iOS shape.
