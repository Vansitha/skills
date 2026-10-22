# The spec

A JSON file. Every field has a default, so a spec can be as short as a body and a palette.

Units are body units. The body is scaled so it's 2 wide (x from −1 to 1) and centred on (0, 0, 0). x runs right, z runs up, and y runs away from the camera (the front faces −y).

Face coordinates (`eyes.at`, `mouth.at`, decals) are `[x, z]` on the front of the piece they're laid on, measured from that piece's centre. Back decals use the same coordinates as seen from behind; the script mirrors them.

`name` and `about` are free text for people; the script ignores them.

## body

| Field | Default | Meaning |
|---|---|---|
| `shape` | `sphere` | `sphere`, `egg`, `blob`, `capsule`, `cylinder`, `disc`, `box`, `torus`, `cone`, `path` or `file`. |
| `size` | `[1, 0.9, 1]` | Half-sizes. See the table below. |
| `bevel` | `0.04` | The rounding on the edges of a `disc`, `box`, `cylinder` or `path`. Robots and devices take 0.15 to 0.25. |
| `roundness` | `2.0` | For `blob`: 2 is an ellipse, 2.5 to 3 is a marshmallow, and higher is squarer. |
| `taper` | `0` | For `egg`: 0.2 to 0.4 narrows the top; −0.2 to −0.4 narrows the bottom (a strawberry, a drop). |
| `d` | | For `path`: an SVG path with absolute M, L, H, V, C, Q and Z commands, in any coordinates (y down, as in SVG). It's centred and scaled so its width is 2. Use several closed loops for holes. |
| `file` | | For `file`: a `.glb`, `.gltf`, `.obj` or `.fbx`, relative to the spec. It's merged, centred and scaled so its width is 2. It needs a closed mesh with its normals pointing out for a clean outline. |

| Shape | `size` |
|---|---|
| `sphere`, `egg`, `blob`, `capsule`, `box` | `[half-width, half-depth, half-height]`. One number makes all three equal. |
| `cylinder` | `[radius, half-depth, half-height]`. It stands upright, like a cup or a can. |
| `disc` | `[radius, half-thickness]`. It faces the camera, like a coin. |
| `torus` | `[major radius, minor radius]`. It lies flat; `rotate` it to stand it up. |
| `cone` | `[radius, half-height]` comes to a point; `[bottom radius, top radius, half-height]` is cut off flat. |
| `path`, `file` | `[half-width, half-thickness]`. For `file`, only the half-width counts. |

Thick bodies (`disc`, `box`, `path`) have a front, a back and a side, and the side takes `palette.edge`. Every other shape is all fill.

## palette

Colours are `#RRGGBB` hex in sRGB, or the name of another palette entry.

| Name | Default | Used for |
|---|---|---|
| `fill` | `#FFFFFF` | The body, and parts with no colour of their own. |
| `line` | `#111111` | The outline. |
| `edge` | `fill` | The side of a thick body. On a coin it's `line`. |
| `decal` | `line` | Eyes, closed-eye arcs, mouths, rings and strokes. |
| `shine` | `#FFFFFF` | The catchlight in `dot` and `pupil` eyes. |
| `white` | `#FFFFFF` | The white of `pupil` eyes. |
| `blush` | `#FF9AAE` | Cheeks. |
| `accent` | `#FFC93C` | Effects, and anything you name it for. |

Add any names you like (`screen`, `leaf`, `seed`) and refer to them from parts, decals and effects.

## look

| Field | Default | Meaning |
|---|---|---|
| `shading` | `flat` | `flat` is pure colour, a sticker. `toon` adds a darker band away from the light. `soft` is lit and slightly glossy, a toy. |
| `shadow_tint` | `0.82` | Toon: how dark the band is, as the fill colour times this. |
| `band` | `0.5` | Toon: where the band starts, from 0 (no band) to 1 (all band). 0.35 to 0.45 makes a thin crescent of shade. |
| `highlight` | `false` | Flat or toon: a crisp glossy spot where the body faces the light. |
| `highlight_at` | `0.95` | The spot's size: 0.97 is small and 0.9 is large. |
| `highlight_color` | `#FFFFFF` | The spot's colour. |
| `roughness` | `0.45` | Soft: 0.3 is shiny plastic and 0.7 is felt. |
| `outline` | `0.06` | The outline's width in body units. 0.04 is fine, 0.1 is bold (a sticker coin), and 0 turns it off. |
| `border` | none | `{"width": 0.07, "color": "#FFFFFF"}`: a second band outside the outline, like a sticker's cut edge, so a dark outline reads on dark screens. |
| `edge_highlight` | `false` | A crisp highlight that slides along a thick body's side as it turns. |
| `reeding` | none | `{"stripes": 64, "duty": 0.3}`: stripes round a disc's rim, in the fill colour. |
| `light` | `[55, -35, -20]` | The sun's rotation in degrees. The default lights from the upper left, in front. |

## parts

Everything that isn't the body: ears, arms, wings, a tail, a head, leaves, a stem, an antenna, a halo, a hat, a handle, a snout.

```json
"parts": [
  {"name": "EarL", "shape": "cone", "size": [0.27, 0.24], "at": [-0.52, 0, 0.86], "rotate": [0, -20, 0], "pivot": [-0.48, 0, 0.68], "jiggle": 10},
  {"name": "ArmR", "shape": "capsule", "size": [0.12, 0.12, 0.36], "at": [1.02, 0, -0.16], "pivot": [0.94, 0, 0.18], "jiggle": 8},
  {"name": "Handle", "shape": "torus", "size": [0.34, 0.09], "at": [0.92, 0, 0.02], "rotate": [90, 0, 0]},
  {"name": "Halo", "shape": "torus", "size": [0.55, 0.06], "at": [0, 0.1, 1.35], "rotate": [15, 0, 0], "color": "accent", "jiggle": 4, "jiggle_axis": "x"}
]
```

| Field | Default | Meaning |
|---|---|---|
| `name` | `Part0`, … | How shots, helpers and features refer to it. Name arms, wings and paws `ArmL`, `WingR`, `PawR` and so on, and the `wave` shot finds them. |
| `shape`, `size` | `sphere`, `[0.3]` | Any body shape, with the same sizes. A `path` part takes `d`, and a `file` part takes `file`. Flatten a sphere with a small y size for a leaf, a wing or a flat ear: `[0.32, 0.12, 0.1]`. |
| `at` | `[0, 0, 1.2]` | The part's centre, in body units. A negative y is in front of the body. |
| `rotate` | `[0, 0, 0]` | Degrees about x, y and z. |
| `pivot` | `at` | Where the part attaches and swings from: a shoulder, the root of an ear or a tail, the base of a stem. Parts that move together (an antenna and its ball) share a pivot. |
| `jiggle` | `0` | Degrees of follow-through after every landing and stop. 0 is stiff, 6 to 10 suits ears and leaves, and 14 to 20 suits floppy ears, tails and antennae. Parts with jiggle also sway in `idle`. |
| `jiggle_axis` | `y` | The axis it swings on. `y` sways sideways in the picture, `x` nods back and forth, and `z` twists. |
| `color` | `fill` | A palette name or a hex colour. |
| `outline` | `true` | Thin parts (an antenna's stalk) often look better without one. |
| bevel, roundness, taper | | As for the body. |

Features can be laid on a part instead of the body: give the eyes, mouth, cheeks or a decal `"on": "Head"`. Its `at` is then measured from that part's centre.

## eyes

Set `"eyes": null` for no eyes.

| Field | Default | Meaning |
|---|---|---|
| `at` | `[[-0.34, 0.12], [0.34, 0.12]]` | Each eye's centre. |
| `size` | `[0.13, 0.18]` | The radii: x and z. |
| `on` | `body` | The piece they sit on. |
| `tilt` | `0` | Degrees: leans each eye's top to the right. |
| `mirror_tilt` | `false` | Leans the left eye the other way. |
| `style` | `dot` | See below. |
| `shine.at` | `[-0.35, 0.4]` | Where the shine sits, as fractions of the eye's radii (or the pupil's, for `pupil`). For `bite`, `[-0.8, -0.1]` notches the lower left, so the eye looks up and right. |
| `shine.size` | `0.32` | The shine's radius as a fraction of the eye's width. Set it to 0 for no shine. |
| `shine.color` | `fill` | For `bite`: the notch's colour. |
| `pupil` | `0.6` | For `pupil`: the pupil's size as a fraction of the eye. |
| `look` | `[0, 0]` | For `pupil`: where the pupil sits, from −1 to 1 on each axis. |

The styles are:
- `dot`: a dark eye with a small shine inside.
- `bite`: a dark eye with a notch in the body's colour cut into its edge, like a sticker's catchlight.
- `pupil`: a white eye with a dark pupil and a shine.

Every spec gets three faces automatically:
- `open`: the eyes;
- `happy`: upturned arcs (∩) where the eyes are;
- `closed`: downturned arcs (∪), a little lower.

The shots also widen the eyes (surprised), narrow them (squint), blink them, and move them along the surface (glance).

## mouth, cheeks

Both are optional.

```json
"mouth": {"at": [0, -0.1], "width": 0.2, "shape": "smile", "line": 0.045, "faces": ["open", "happy", "closed"]},
"cheeks": {"at": [[-0.55, -0.08], [0.55, -0.08]], "size": [0.13, 0.075], "color": "blush"}
```

- The mouth's `shape` is `smile`, `flat` or `o`. Use `points` instead for your own stroke (a cat's "w", a grin): an anchor, then a control, a control and an anchor for each curve.
- The mouth's `faces` lists the faces it shows in.
- Both take `on` and `color`.

## decals

Marks laid flat on a piece's front, back or both: stripes, spots, seeds, a screen, a nose, a belly patch, a rim ring.

```json
"decals": [
  {"type": "ring", "r": 0.86, "width": 0.046, "side": "both"},
  {"type": "disc", "at": [0, 0.04], "size": [0.62, 0.42], "color": "screen", "lift": 0.3},
  {"type": "disc", "at": [0, -0.02], "size": 0.06, "color": "#FF8FA0", "lift": 2},
  {"type": "stroke", "points": [[-0.3, -0.2], [-0.1, -0.4], [0.1, -0.4], [0.3, -0.2]], "width": 0.05, "side": "back"}
]
```

| Field | Default | Meaning |
|---|---|---|
| `type` | | `ring` (centred, radius `r`), `disc` (an ellipse at `at` with radii `size`), or `stroke` (a cubic path through `points`, like a mouth). |
| `side` | `front` | `front`, `back` or `both`. |
| `on` | `body` | The piece it's laid on. |
| `color` | `decal` | A palette name or a hex colour. |
| `lift` | `1` | The stacking order, by height above the surface. Eyes sit at 1 and their shines at 2, so a screen behind the eyes takes 0.3, and a nose over the mouth takes 2. |

## effects

Flat shapes that pop round the mascot in some shots: sparkles, bursts, hearts, dots, z's and impact lines. They're off unless the spec turns them on or the render passes `--effects`.

| Field | Default | Meaning |
|---|---|---|
| `on` | `false` | Turns them on for every shot. |
| `color` | `accent` | Their fill. |
| `outline` | `line` | Their outline colour, or `null` for none. |
| `size` | `1.0` | Scales them all. |

## rest

The pose every shot starts and ends on, in degrees `[x, y, z]`. A small turn makes the character read as 3D at rest:
- `[-12, 0, 12]` tips it up and to the right, so the side shows at the lower left;
- `[-6, 0, 10]` suits a soft character.

## camera

| Field | Default | Meaning |
|---|---|---|
| `frame` | `4.66` | The frame's width in body units. The body fills 2 / 4.66 (43%), which leaves room to hop and turn. Lower it (3.2) for a tight, still portrait. Raise it for tall ears or a wide wave. |
| `lens` | `85` | The perspective lens in millimetres. A longer lens is flatter. |
| `ortho` | `false` | An orthographic camera: no perspective at all, the flattest sticker look. |

## motion

| Field | Default | Meaning |
|---|---|---|
| `fps` | `60` | Frames per second. The shots are timed for 60; at 30 they run at double speed, so keep 60. |
| `flip` | `z` | The axis the big moves turn on. See below. |
| `flips` | `1` | Whole turns in a hop. |
| `hop` | `0.9` | The jump's height in body units. |
| `squash` | `0.08` | How much it squashes on a crouch or a landing. 0.05 is firm, 0.12 is jelly. |
| `shake` | `z` | The axis of the "no" shake. `z` turns the head; `y` rocks it in the picture's plane, which suits flat bodies. |
| `spin_axis` | `y` | The `spin` shot's axis. `y` turns in the picture's plane, so the face stays towards you. `x` flips a coin end over end, and `z` is a turntable. |
| `spin_seconds` | `1.0` | The time for one turn in `spin`. 0.5 is busy, and 1.5 is calm. |
| `wave` | auto | The part the `wave` shot lifts. Left out, it's the first part named arm, hand, wing, paw or flipper, preferring the side the rest pose turns towards the camera. |
| `wave_lift` | `145` | How far, in degrees, the waving part swings up from where it hangs. |
| `jiggle` | `1.0` | Scales every part's follow-through: 0 stops it all, and 1.5 makes everything floppier. |

The `flip` axes are:
- `x`: end over end, like a tossed coin;
- `z`: a twirl about the vertical, like a character spinning to show its back;
- `y`: a cartwheel in the picture's plane, which suits flat drawn shapes;
- `none`: no turning, it just hops.

## variants

Overrides applied with `--variant NAME`, merged over the spec, for a dark-mode negative or a seasonal colourway:

```json
"variants": {"ink": {"palette": {"fill": "#000000", "line": "#FFFFFF"}, "eyes": {"shine": {"at": [0.8, 0.1], "size": 0.4}}}}
```

Lists (parts, decals) are replaced whole, not merged, so a variant that changes one part repeats the list.
