# From any concept to a spec

Any mascot, whether an animal, an object, a food, a shape or a logo, comes apart the same way:

- **a body:** the biggest mass;
- **parts:** whatever sticks out or moves on its own;
- **a face:** on the body, or on a head part;
- **marks:** patterns laid on the surface.

Get those four right and the look and motion follow.

## 1. Read the concept

Write down, in one line each:
- **What it is**, and its silhouette: round, tall, flat, spiky, or a drawn outline.
- **The one or two features that make it recognisable.** A cat is its ears. A robot is its antenna and screen. A strawberry is its seeds and leaves. A coin is its rim. If you drop one of these, it stops being that thing.
- **Its personality:** calm, bouncy, cheeky, sleepy, proud. This sets the motion.
- **Where it lives:** an app, a site, a video, on light or dark. This sets the size, the formats and whether it needs a border.
- **What you have:** a description, a sketch, an SVG or brand mark, a reference image, or a 3D model.

## 2. Break it down

| Piece | Rule | Examples |
|---|---|---|
| **Body** | The biggest single mass, centred. Everything else is placed relative to it. Its width is 2 units. | A cat's round body, a robot's box, a cup's cylinder, a ghost's silhouette. |
| **Parts** | Anything that sticks out, moves on its own, or is a different colour from the body. | Ears, arms, wings, a tail, a stem and leaves, an antenna, a halo, a hat, a snout, a handle. |
| **Face** | Usually on the body. Put it on a part (`"on": "Head"`) when the character has a separate head. | Eyes, mouth, cheeks, a nose (a small disc decal). |
| **Marks** | Flat patterns on the surface: decals. | Stripes, spots, seeds, a screen, a ring, a belly patch, a logo shape, buttons. |

Keep it to what reads at the size it will be shown. At 40 points, five parts and a face is plenty.

## 3. Choose each piece's shape

| Shape | Good for |
|---|---|
| `sphere`, `egg` (`taper` narrows the top; negative narrows the bottom), `blob` (`roundness` 2.3 to 2.8) | Soft round bodies, heads, paws, snouts, berries, fluffy things. |
| `capsule` | Tall bodies, limbs, ears, tails, antennae, stems, fingers. |
| `cylinder` | Cups, cans, batteries, jars, towers. |
| `box` with a large `bevel` | Robots, devices, books, buildings, toasters. |
| `disc` | Coins, badges, buttons, a flat face-on icon. |
| `cone` | Cat ears, horns, beaks, hats, spikes. |
| `torus` | Halos, rings, handles, donuts, planet rings. |
| `path` (an SVG outline made thick) | Anything you can draw: stars, hearts, clouds, flames, drops, leaves, letters, a brand mark. |
| `file` (`.glb`, `.obj`, `.fbx`) | Anything sculpted elsewhere: a detailed head, a character from a 3D tool, an existing brand model. |

To flatten a sphere into a leaf or a wing, use a small y size, for example `"size": [0.32, 0.12, 0.1]`.

## 4. Decide what moves

- **A part swings from its `pivot`,** where it attaches: an arm from its shoulder, an ear or a tail from its root, a leaf from its stem.
- **`jiggle` sets the follow-through,** the swing and settle after every landing:
  - 0 for stiff parts (a hat, a handle);
  - 6 to 10 for ears and leaves;
  - 14 to 20 for floppy ears, tails and antennae.

  It swings on `jiggle_axis`: `y` sways sideways in the picture, `x` nods back and forth.
- **Name a part `ArmR`, `WingL` or `PawR` (or set `motion.wave`)** and the `wave` shot waves it. Wave the arm on the side the rest pose turns towards the camera, or the raised arm hides behind the body.
- **Several parts that move together** (an antenna and its ball) share one `pivot` and the same `jiggle`.
- **Pick the flip axis to suit how it turns:**
  - coins and badges flip end over end (`x`);
  - flat drawn shapes cartwheel (`y`);
  - characters twirl (`z`);
  - heavy or dignified things don't turn (`none`).
- **Set squash and hop from the material:**
  - jelly and dough: squash 0.12 and a high hop;
  - soft toys: 0.08 to 0.1;
  - solid things (robots, coins): 0.05 to 0.06 and a lower hop.

## 5. Choose the look

| Look | When |
|---|---|
| `flat` | Brand marks, stickers, black-and-white mascots, icons: exact colours and a bold outline. |
| `toon` | Characters with colour: one shade band and an optional glossy highlight. |
| `soft` | Toys, food and products: real light, slightly glossy, a thin or no outline. |

- Add `look.border` (white or cream) whenever the outline is dark and the mascot will sit on dark screens.
- Make a `variants` entry for a dark mode or a seasonal colourway, rather than a second spec.

## 6. Map moments to shots

| Feeling or moment | Shot |
|---|---|
| Waiting, at rest | `idle` (loop) |
| Done, saved, good | `hop` |
| A milestone, a win | `celebrate` |
| Excited, cheering | `bounce` (loop) |
| Removed, sad, oops | `dip` |
| Undone, restored | `undo` |
| Something needs attention | `surprised` |
| Error, no | `shake` |
| Yes, confirmed | `nod` |
| Thinking, working it out | `think` |
| Thanks, love, favourite | `love` |
| Hello, welcome | `wave`, or `entrance` when opening |
| Curious, hiding, a tip | `peek` |
| Busy, loading | `spin` (loop) |
| Paused, off, night | `sleepy` (loop), then `wake` |
| Goodbye, sent away | `exit` |

When none fits, write a shot file (`references/motion.md`). A shot is a few lines of keys.

## 7. When the spec can't say it

- **A shape that primitives can't make:** draw it as an SVG `path`, or model it in Blender (or any 3D tool), export it as `.glb`, and use `"shape": "file"` for the body or a part.
- **A motion that no shot has:** write a `--shot-file`. The helpers key the body, the parts, the face and the effects.
- **Something the script doesn't do at all:** `scripts/mascot3d.py` is plain Blender Python. Copy it next to the spec and extend it for this mascot. Keep the rules in SKILL.md: unlit or soft materials, the inverted-hull outline, no cast shadows, and every clip ending on the rest pose.

## Recipes

Starting points to adapt. The shapes use the spec's size conventions.

| Concept | Body | Parts | Face and marks | Motion |
|---|---|---|---|---|
| **Coin, badge, token** | `disc` [1, 0.15], edge in line colour, reeding | none, or a ribbon | `bite` eyes, a ring decal | flip `x`, squash 0.08 |
| **Cat** | `blob` 2.3 | cone ears (jiggle 10), a capsule tail (jiggle 16) | dot eyes, a nose disc, a "w" mouth from points, whiskers, stripes | flip `z` |
| **Dog** | `blob` or `egg` | long capsule ears hanging down (jiggle 18), a sphere snout with the nose on it | pupil eyes, a tongue disc on the snout (`"on": "Snout"`) | bouncy: squash 0.1 |
| **Bunny** | `egg` | two tall capsule ears (pivot at the base, jiggle 20), a round tail | dot eyes, a pink nose | hop 1.0 |
| **Bear** | `blob` | sphere ears, a sphere snout | the face on the body, the nose on the snout | squash 0.08 |
| **Bird** | `egg` | flattened-sphere wings (`WingL`/`WingR`, jiggle 12), a cone beak | dot eyes | wave flaps a wing |
| **Robot** | `box` with bevel 0.2 | capsule arms from the shoulders, an antenna and a ball sharing one pivot | a dark screen disc decal (lift 0.3) with glowing eyes | squash 0.06, a border for dark |
| **Fruit (strawberry, apple)** | `egg` (taper for the shape) | flattened-sphere leaves and a stem from one pivot (jiggle 8) | seed discs, dot eyes, cheeks | `soft` look |
| **Plant, seed, sprout** | `egg` or `blob` | a capsule stem, flattened-sphere leaves (jiggle 12) | dot eyes, cheeks | gentle: hop 0.6 |
| **Cloud** | `path` (a bumpy outline) | none | dot eyes | flip `y` (cartwheel), spin `y` |
| **Ghost** | `path` (a wavy hem) | none, or little arms | dot eyes, an "o" mouth | floaty: hop 0.7, squash 0.07 |
| **Star, heart, flame, drop** | `path` | none | dot eyes, cheeks | flip `y`, sparkles on hop |
| **Cup, mug** | `cylinder` | a torus handle at the side (rotate [90, 0, 0]) | the face on the cup; a band decal | a steam shot file, or `love` |
| **Planet** | `sphere` | a torus ring through it, tilted (rotate [15, -18, 0]) | crater discs, dot eyes | flip `none`, spin `z` |
| **Lightbulb** | `egg` (taper −0.3) | a cylinder base | dot eyes | `think` with effects |
| **Letter or logo mark** | `path` from the brand SVG | none | small eyes inside a counter, if it suits | flip `y`, hop |
