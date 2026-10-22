---
name: mascot-animation
description: Turns any mascot concept into an animated 3D character with Blender, headless. Works for an animal, a robot, a coin, a food, a plant, a cloud, an object or a logo mark. It builds the character from a short JSON spec: a body (a simple shape, an SVG silhouette made thick, or an imported model), parts that swing from pivots (ears, arms, wings, tails, leaves, antennae), a face laid on the surface, and marks. It gives the character a flat sticker, toon or soft-toy look with a clean outline, and renders a library of reactions as transparent clips: idle, hop, celebrate, bounce, surprised, shake, nod, think, love, wave, peek, spin, sleepy, wake, entrance, exit and more. Sparkles, hearts and z's are optional. The outputs are HEVC with alpha for iOS, WebM for the web, previews, GIFs and stills. Use it whenever someone wants a mascot or character to move, even if they don't mention Blender or 3D. That includes app reactions, a splash or launch animation, an idle loop, a loading character, "make our mascot feel alive", Lottie-like character motion, or turning a 2D mascot or a new character idea into an animated one.
argument-hint: "<the mascot concept: a description, sketch, SVG or model, and where the clips will play>"
---

# Mascot animation

A mascot that moves well reads as one solid little object with a personality. Five things make it, and missing any one of them shows:

- **Colours that stay as designed.** The flat and toon looks are unlit, so no lamp washes them out.
- **Real 3D geometry under a 2D look.** A turn shows the thickness, and a tilt shows the side.
- **One clean outline round every piece,** the same weight everywhere.
- **Faces that are flat decals on the surface.** The eyes blink, widen, glance and swap for happy or closed arcs.
- **Motion with weight:**
  - a crouch before a jump;
  - a squash on landing;
  - ears and arms that swing and settle after it;
  - a small overshoot when it stops.

  Every clip ends on the rest pose, so clips cut together and the last frame works as a still.

`scripts/mascot3d.py` does all of this from a JSON spec, running Blender with no window. One spec renders every reaction. Each fix is one number, and a 1 s clip renders in about 10 seconds at draft size. `scripts/encode.sh` turns the frames into files an app or a page can play.

## Any concept

Every mascot breaks down the same way:

- **a body:** the biggest mass;
- **parts:** whatever sticks out or moves on its own, each swinging from a pivot;
- **a face:** on the body, or on a head part;
- **marks:** stripes, spots, a screen, seeds, a logo shape.

[references/concepts.md](references/concepts.md) walks through breaking any idea down this way. It also covers choosing shapes and deciding what moves, and has recipes for about twenty kinds of mascots, from a cat to a cup to a logo mark. Read it whenever the concept isn't close to one of the examples.

For a static icon or a flat 2D mascot, use the `mascot` skill. This skill can reuse that skill's body path and eye positions to make the same character in 3D.

## What you need

- **Blender 4.2 or later** (tested on 5.2). On macOS it's `/Applications/Blender.app/Contents/MacOS/Blender`; on Linux it's `blender`. Call it `$B` below.
- **ffmpeg** (`brew install ffmpeg`). The iOS output (HEVC with alpha) needs macOS. WebM, previews and GIFs work anywhere.

## Steps

1. **Read the concept and the job.** Break it down with [references/concepts.md](references/concepts.md):
   - the body and its silhouette;
   - the parts, and where each one attaches;
   - the face, and the marks;
   - the one or two features that make it recognisable;
   - its personality, which sets the hop, the squash and how it turns;
   - the colours;
   - where the clips play (an iOS app, the web, or both) and on what backgrounds. Dark backgrounds usually need a `border` or a second colour variant.

   Then list the moments that need a reaction and pick a shot for each (step 4).

   Done when you can fill in a spec. Don't ask what you can decide; choose, and say what you chose.
2. **Write the spec.** Copy the closest example from `examples/` and change it:

   | Example | Shows |
   |---|---|
   | `coin.json` | A flat black-and-white sticker coin with a reeded rim that flips end over end. Has an `ink` variant. |
   | `blob.json` | A soft toon character with round ears, cheeks and a smile, that twirls. |
   | `ghost.json` | A body cut from a 2D SVG path. |
   | `cat.json` | Cone ears and a tail on pivots with jiggle, whiskers and stripes as strokes, and a nose. |
   | `robot.json` | A box body, a screen decal with glowing eyes, arms from the shoulders (the `wave` shot uses one), an antenna, and a white border for dark screens. |
   | `berry.json` | The soft look: an egg body, seed decals, and leaves and a stem as parts. |

   Every field is in [references/spec.md](references/spec.md), and the looks are in [references/look.md](references/look.md). Coordinates are in body units: the body is 2 wide, x runs right, z runs up, and (0, 0) is its centre.

   Done when the spec has a body, a palette, a face, the parts with their pivots, a rest pose and the motion settings.
3. **Check the model before animating anything.** Render the check shot, tile it and look at the tiles:
   ```bash
   $B -b --factory-startup -P scripts/mascot3d.py -- spec.json check out/check --size 400 --samples 16
   scripts/encode.sh sheet out/check out/check.png --bg "#E5E5E5"
   ```
   The check renders six angles and every face: open, happy, closed, surprised, squint and glance. Read the WARNING lines too: a feature that hangs off its piece's edge is reported. Fix the spec and render the check again. The usual fixes are in [references/look.md](references/look.md).

   Done when it reads as the concept from the front, still holds together at an angle, the parts attach where they should, and every face looks right.
4. **Pick the shots.** All of them start and end on the rest pose. Lengths are at 60 fps.

   | Shot | Length | Use it for |
   |---|---|---|
   | `idle` | 4 s loop | Waiting: empty states, a home screen. A bob, a blink, a glance; parts sway. |
   | `hop` | 1 s | Something good: saved, sent, logged. A crouch, a jump with its turn, happy eyes. |
   | `celebrate` | 1.8 s | A milestone. Two hops and a double turn. |
   | `bounce` | 1 s loop | Excited, cheering. Two quick happy hops a second. |
   | `dip` | 0.8 s | Removed, or a small sad moment. It sinks and bows with its eyes closed. |
   | `undo` | 0.9 s | Undone or restored. One turn backwards. |
   | `surprised` | 1 s | Needs attention. It jumps up stretched, its eyes pop, and it wobbles. |
   | `shake` | 0.7 s | An error, or no. Squinting. |
   | `nod` | 0.7 s | Yes, confirmed. Two nods. |
   | `think` | 2.2 s | Working something out. It tilts, looks up and taps. |
   | `love` | 1.6 s | Thanks, a favourite. A happy squish and sway. |
   | `wave` | 1.6 s | Hello. It lifts and waves an arm, wing or paw; without one it rocks. |
   | `peek` | 2.1 s | Curious, a tip. It rises from the bottom edge, looks both ways, and ducks back. |
   | `spin` | loop | Busy or loading. A seamless turn on `spin_axis`, once every `spin_seconds`. |
   | `sleepy` | 3.6 s loop | Paused or off. Eyes closed, tipped back, breathing. |
   | `wake` | 0.8 s | Back on. Its eyes open wide and it jumps. |
   | `entrance` | 2.1 s | An app opening. It tumbles up from below, settles, blinks and glances. Render it at the screen's size (for example `1080x2340`). |
   | `exit` | 0.8 s | Goodbye, sent away. It jumps up and out of the frame. |

   With `--effects`, or `"effects": {"on": true}` in the spec, the shots add flat effects in the accent colour:
   - sparkles on `hop` and `celebrate`;
   - a burst of lines on `surprised` and `wake`;
   - hearts on `love`;
   - dots on `think`;
   - z's on `sleepy`;
   - impact lines on the landing of `celebrate` and `entrance`.

   For anything else, write a shot file: see [references/motion.md](references/motion.md). It has the helpers, the timing rules and worked examples.
5. **Render.** Draft small and fast first, then render the finals once:
   ```bash
   $B -b --factory-startup -P scripts/mascot3d.py -- spec.json hop out/hop --size 300 --samples 16          # draft
   $B -b --factory-startup -P scripts/mascot3d.py -- spec.json hop out/hop --size 360 --effects             # final
   $B -b --factory-startup -P scripts/mascot3d.py -- spec.json hop out/hop-ink --size 360 --variant ink      # dark mode
   ```
   - **Size.** The frame spans `camera.frame` body units (4.66 by default), so the body fills about 43% of its width and has room to hop. To show the mascot at S points on screen, play the clip in a box `S × frame / 2` points wide (2.33 S), drawn over its surroundings. Render it at that width times the screen scale. For a 40 pt mascot on a 3× phone, 40 × 2.33 × 3 is about 280 px.
   - `--frames 1-20` and `--step 2` make quick partial drafts.
   - `--shadow` adds a soft ground shadow, for previews.
   - `--rest-up 0.45` lifts the resting spot in a tall frame, to leave room for a wordmark under it.
6. **Encode.**
   ```bash
   scripts/encode.sh out/hop dist/hop ios web preview still --bg "#FFFFFF"
   ```
   - `ios` is a `.mov` (HEVC with alpha). It prints an AVFoundation check across the clip. "alpha kept" with corner alpha 0 and the most opaque pixel about 255 is right. "LOST" means the transparency is gone.
   - `web` is a `.webm` (VP9 with alpha).
   - `preview` is an `.mp4` on the background colour, for showing people.
   - `still` is the last frame as a PNG, for Reduce Motion and posters.
   - `gif` exists, but its edges are jagged, so use it only for docs and chats.
7. **Look at it.** Tile the frames and watch the preview:
   ```bash
   scripts/encode.sh sheet out/hop out/hop-sheet.png --count 12
   ```
   Judge in this order:
   1. the silhouette and the outline;
   2. the faces;
   3. the timing: does it anticipate, land with weight, and settle without drifting?
   4. the parts: do they follow through and come to rest?
   5. the loop seams.

   Fix the spec or the shot, and render again.
8. **Ship it.** [references/shipping.md](references/shipping.md) has:
   - a SwiftUI player that keeps the alpha and waits until the clip is ready and on screen before it plays;
   - a web `<video>` that serves HEVC to Safari and WebM to everyone else;
   - the rules: one mascot at a time, never block input, haptics on the landing frame, and stills under Reduce Motion.
9. **Deliver.** Send the user the preview MP4s and the frame sheets. List the files and their sizes, and say which shot goes with which moment.

## When the spec can't say it

- **A shape no primitive makes:** draw it as an SVG `path`. Or model it in any 3D tool, export a `.glb`, and use `"shape": "file"`, for the body or for a part.
- **A motion no shot has:** write a `--shot-file`. The helpers key the body, any part, the face and the effects. See [references/motion.md](references/motion.md).
- **Something the script doesn't do at all:** `scripts/mascot3d.py` is plain Blender Python. Copy it next to the spec and extend it for this mascot, keeping the rules below.

## Rules

- **Keep it unlit, or softly lit.**
  - In the flat and toon looks, every colour is emission and the view transform is Standard. The one sun light only feeds the toon bands and highlights.
  - The soft look is lit, with a soft ambient fill.
  - No light ever casts shadows: the outline shell round the character would shade everything inside it.
- **Draw the outline as an inverted hull.** It's a slightly bigger, inside-out copy of each piece, with backface culling. An imported model needs a closed mesh with its normals pointing out, or the outline breaks into scribbles.
- **Hang every part from its pivot,** where it attaches: an arm from its shoulder, an ear from its root. The waves, the jiggle and the idle sway then look anatomical.
- **Lay features inside the silhouette.** Eyes, mouths and marks are projected onto their piece. A point that misses is reported as a WARNING and floats in the air.
- **Mirror the catchlights in a negative variant.** When fill and line swap, a notch cut into a dark eye becomes a dark pupil in a light eye, and it looks the other way. Mirror the shine's position in the variant (see `examples/coin.json`).
- **Keep clips short, and end on rest.**
  - Reactions run 0.5 to 1.4 s; loops run 1 to 4 s.
  - A loop's last frame equals its first.
  - A constant-speed loop (spin) needs a key on every frame, because Blender eases between keys.
- **Swap faces on contact.** The happy face lands with the body, and the eyes close as it bows.
- **Keep words out of the renders.** Put names and wordmarks in the app's own type, over or under the clip.
- **Draft small, and render finals once.** 300 px and 16 samples look the same for judging motion, and take a quarter of the time.

## Files

- `scripts/mascot3d.py`: builds the mascot and renders a shot (Blender).
- `scripts/encode.sh`: encodes frames for iOS, the web, previews, GIFs and stills, and tiles frame sheets.
- `scripts/alphacheck.swift`: checks that a `.mov` kept its alpha in AVFoundation (`encode.sh` runs it).
- `examples/`: `coin.json`, `blob.json`, `ghost.json`, `cat.json`, `robot.json` and `berry.json`.
- `references/`:
  - `concepts.md`: from any concept to a spec, with recipes.
  - `spec.md`: every field.
  - `look.md`: the three looks, borders, and fixes.
  - `motion.md`: the shots, the timing, the helpers, and custom shots.
  - `shipping.md`: playing clips in apps and on the web.
