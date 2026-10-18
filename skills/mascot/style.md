# Style: what makes it look high quality

## The recipe

These values are relative to the body's width W, in spec units. Without a reference, start here.

| Part | Starting value |
|---|---|
| Body width W | 55% to 60% of the icon. Leave room above for the prop. |
| Body fill | The background's middle colour, a little lighter. The body should almost disappear into the background without its glow. |
| Glow | A very light tint of the body's hue, for example `CFF4FF` on blue or `D4FFF1` on mint. Width about 0.11 W, blur about 0.025 W. Add one `extra` ellipse on the lit side, upper left. |
| Rim | 2 to 3 units, the glow colour, alpha 0.9. |
| Shadow | A darker, more saturated version of the background, alpha 0.75, blur about 0.05 W. |
| Background | A vertical gradient from a little lighter at the top to a little darker at the bottom. Add a lighter glow upper left and a darker glow under the character. |
| Eyes | Each white about 0.13 W wide and 0.19 W tall. The two whites just touch (overlap of 5% or less). Tilt ±5 to 10 degrees. |
| Pupils | About 60% of the white's size, set toward the way the eyes look. Leave a thick white rim on the other side. |
| Shine | An oval about 0.025 W × 0.05 W, on the pupil's edge away from where it looks. |
| Prop | One bright accent colour (gold `FFC618` with a `FFDA5E` stripe). Make a halo about 0.55 W across and thin, rising a little to one side. |
| Sparkles | 8 to 12 small dots in white with a little of the hue, alpha 0.85, kept away from the character. |

## Misses and fixes

These all came up while matching a real reference. Check for them on every round.

| You see | Cause | Fix |
|---|---|---|
| The body looks pale, grey or washed out | It's lit like a 3D object, or the fill is too light | Fill with the background's own hue. Light comes from the glow, not from lighting. |
| It looks like a plastic toy, not an illustration | 3D lighting and spherical eyes | Use flat shapes and flat sticker eyes (this renderer). Use Blender only for a real 3D look. |
| The eyes look generic | They're marbles: shaded spheres | Use flat white ovals, flat black pupils and one crisp shine. |
| The eyes are too close | The whites overlap a lot | Make the whites just touch. |
| The eyes lean the wrong way | The tilt sign | Negative leans the top left. Measure the tilt from the row centres. |
| The body is pointy, or tapers at the bottom | A teardrop or tail where the reference has a hem | Trace the hem's low points and notches, and give it a flat bottom with soft lobes. |
| The glow is too thin, so the body looks flat | Width or brightness too low | Raise `width` toward 0.11 W and use a lighter glow colour. |
| The glow is too heavy, a thick pale band | Width or blur too high, or `extra` too strong | Bring `width` and `blur` down. Keep `extra` alpha at 0.5 or less. |
| The character floats | No shadow, or no darker glow under it | Add `shadow`, and a darker background glow under the character. |
| There's a small flat ledge on the outline | A kink between two curves | Line up the control points either side of that point. |
| The blush looks grey | Pink blended with a cool or green body | Use a stronger pink (`FF4F86`, alpha 0.6). |
| The happy eyes run together | The arcs are too wide | The renderer draws them at about 70% of the eye's width. Space the eyes a little more. |
| The halo stands upright (3D) | The ring's axis faces the camera | Keep `ry` small (about 0.22 × `rx`) and the rotation between −10 and 10 degrees. |

## Moods

Copy the spec and change only the eyes, plus an optional prop:

- **happy:** `"style": "happy"`. Add a mouth path if the reference has one.
- **sleepy:** `"style": "sleepy"`. Add a small "z" as a path or a sparkle.
- **watching:** an open eye with the pupils' `dx` pushed to one side.
- **surprised:** an open eye with a smaller pupil, centred, and a slightly bigger white.

## Originality

A traced copy of someone else's character is fine for exploring, but not for shipping. Before it goes public, change at least two of these: the hue, the prop, the silhouette's signature detail (the hem, the ears, the tail), or the eye style.
