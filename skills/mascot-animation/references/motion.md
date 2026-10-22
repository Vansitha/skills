# Motion

## What makes it read as alive

- **Anticipation.** A crouch (a squash and a dip) comes before any jump, lasting 4 to 6 frames at 60 fps.
- **Squash on landing, then a small stretch back,** within about 10 frames. It sells the weight. Keep `squash` small: 0.06 to 0.1.
- **Follow-through.** Ears, tails, arms and leaves keep moving after the body stops, then settle. That's `jiggle` on a part, keyed by `jiggle(f)` at each landing.
- **Overshoot.** When it settles, it goes a little past rest and comes back: 2 to 8 degrees, or 0.03 to 0.08 units.
- **Easing comes free.** Blender's default keys ease in and out, so space the keys out and the motion breathes. Only a constant-speed loop (spin) needs a key on every frame.
- **Faces change on contact.** The happy face lands with the body, and the eyes close as it bows. A blink takes 9 frames, closed at +4.
- **Short, then still.** A reaction says one thing in 0.5 to 1.4 s and stops on the rest pose. Loops repeat the same thing, so keep them small: a bob of 0.05, a sway of 2 degrees.
- **Personality is in the numbers.** A heavy or solid character hops lower and squashes less (0.6 and 0.05). A jelly or a bouncy one hops higher and squashes more (1.0 and 0.12). A calm one turns slowly (`spin_seconds` 1.5).

## The shots

The timings are at 60 fps. Every shot starts at frame 1 on the rest pose and ends on it. Effects only appear with `--effects` or `effects.on`.

| Shot | Frames | Keys |
|---|---|---|
| `idle` | 240, loops | Bobs up 0.05 and sways ±2° on z at 60, 120, 180 and 240. Parts with jiggle sway with it. Blinks at 90, and glances up and right (+0.07, +0.04) from 158 to 196. |
| `hop` | 60 | Crouch at 5, launch at 8, the top at 22 (`hop` high, about half the turn), landing at 36, squash at 39, stretch at 44, settled at 50. Happy from 37, follow-through from 36. Sparkles from 30. |
| `celebrate` | 108 | A small hop (4 to 28), then a big one at 1.3 × `hop` with a double turn (31 to 70), settled at 88. Happy from 26. Sparkles from 44 and impact lines at 70. |
| `bounce` | 60, loops | Happy. Two quick hops of 0.35 × `hop`, at 1 and 31, tilting ±4°. Frame 61 equals frame 1. |
| `dip` | 48 | Sinks 0.16 and bows 22° on x by 10, holds to 30, back by 44. Eyes closed from 7 to 34. |
| `undo` | 54 | Crouch, then one turn the opposite way while hopping 0.75 × `hop`; it lands at 34. |
| `surprised` | 60 | Stretches up 0.38 by 7, lands at 14, wobbles 7, −5, 3, −1.5 and 0°. Eyes 1.32 times larger from 7 to 48. A burst of lines from 6. |
| `shake` | 42 | Turns 24, −22, 16, −10, 4 and 0°, every 5 frames, on the `shake` axis. Squints from 6 to 28. |
| `nod` | 42 | Tips 16, −4, 12, −2 and 0° on x. Happy from 4 to 36. |
| `think` | 132 | Tilts and looks up and to the left by 22, taps three times (40, 56, 72), comes back by 124 and blinks. Dots from 30. |
| `love` | 96 | Happy from 4. A squish and a little rise by 22, then sways 6, −6, 4 and 0° on y. Hearts rise from 10. |
| `wave` | 96 | Happy. A little bounce, then the arm (`motion.wave`) swings up `wave_lift`° by 14, waves ±18° every 9 frames to 75, and comes down by 90. With no arm, it rocks ±10° instead. |
| `peek` | 124 | Rises from below the frame by 18 to sit low, looks left (44 to 70), right (78 to 100), blinks at 108, and ducks out by 124. |
| `spin` | `spin_seconds` × 60, loops | One whole turn on `spin_axis`, keyed on every frame, so the frame after the last equals frame 1. |
| `sleepy` | 216, loops | Tipped back 10°, eyes closed, breathing (squash −0.025 to 0.02) and swaying ±2°. Two z's rise in a seamless loop. |
| `wake` | 48 | Starts as sleepy. Eyes open wide at 10, a crouch, a jump of 0.32 at 20, landing at 30, settled at 38. A burst from 14. |
| `entrance` | 124 | Tumbles up from below the frame through about 1080° on the flip axis, peaks at 34, overshoots at 58 and 66, settles at 74, blinks at 86, glances at 106. Impact lines at 58. |
| `exit` | 48 | Happy. A crouch, then a jump up and out of the top of the frame by 40, turning. It ends off screen, not on rest, so hide the view when it finishes. |
| `check` | stills | Six angles, then each face: open, happy, closed, surprised, squint and glance. |

The flip axis (`motion.flip`) changes the character of every big move:
- `x` is end over end, the way a tossed coin flips;
- `z` is a twirl, a character spinning to show its back;
- `y` is a cartwheel;
- `none` hops without turning.

A body with a blank back looks odd mid-twirl unless it has back decals.

## Your own shots

When none of the shots fits a moment (a tail wag, a cheer with both arms, steam off a cup, a coin toss, a dance), write a Python file and pass it with `--shot-file`. The SHOT argument is then just a name for the log.

The file runs inside the script after the mascot is built, with everything keyed at rest on frame 1. Start from the closest built-in shot: they're all in `scripts/mascot3d.py`, after `# MARK: Shots`.

### The body and face

| Helper | What it does |
|---|---|
| `pose(f, up=, turn=(x, y, z), squash=, side=)` | Keys the mascot at frame f. `up` is the height above the rest spot. `turn` is degrees added to the rest pose. `squash` flattens when positive and stretches when negative. `side` is a sideways shift. Leave out what doesn't change. |
| `flip_turn(degrees, axis=None)` | A turn tuple on the spec's flip axis (or the given one), for `turn=`. |
| `face(f, "open" / "happy" / "closed")` | Switches the face from frame f. |
| `eyes(f, wide=1, tall=1, look=(dx, dz))` | Keys the open eyes' scale and glance. A glance slides along the surface. |
| `blink(f)` | Closes the eyes at f + 4 and opens them at f + 9. |

### Parts

| Helper | What it does |
|---|---|
| `part_pose(name, f, turn=(x, y, z), at=, scale=)` | Keys a part at frame f. `turn` is degrees about its pivot, from its rest. `at` moves the pivot, and `scale` scales it. |
| `jiggle(f, amount=1)` | Follow-through: every part with a `jiggle` swings and settles over 24 frames from f. Call it on each landing or sudden stop. |
| `wave_part()` | The part the wave shot would lift. |

To swing a part up, turn it on y: −degrees for a part on the right (x > 0), +degrees for one on the left.

### Effects

These do nothing unless effects are on, so a shot can always call them.

| Helper | What it does |
|---|---|
| `sparkles(f, count=4)` | Stars pop round the mascot one after another. |
| `burst(f, count=3)` | Short lines burst out above the head. |
| `hearts(f, count=3)` | Hearts rise and fade. |
| `impact(f)` | Lines either side of the base, for a hard landing. |
| `thinking_dots(f)` | Three dots appear above and to the right. |
| `zs_loop(period)` | Two z's rising, looping seamlessly over `period` frames. |

For your own effect, call these directly; they work whether or not effects are on:
- `sprite(kind, name, (x, z), size, rot=0)` makes a hidden sprite. `kind` is `star`, `heart`, `line`, `dot` or `z`.
- `pop(sprite, f, hold=10)` scales it in with an overshoot, holds it, and shrinks it away.
- `drift(sprite, f, dx, dz, frames)` moves it.

Effects stay where they're made and don't follow the mascot, so place them away from where it will be.

### Rendering

| Helper | What it does |
|---|---|
| `every_frame(first, last, fn)` | Calls `fn(f)` on every frame, plus two either side, for constant speed. |
| `render(first, last)` | Renders the frames, and writes `last.png`. |
| `still(name, frame=1)` | Renders one PNG. |

### Values you can read

- `HOP`, `SQ` and `TURN`: the spec's hop height, squash, and degrees of turn in a hop.
- `MOTION`, `SPEC`: the whole spec, after the variant is merged.
- `HALF_HEIGHT`: half the body's height.
- `HALF_H`: half the frame's height, in body units.
- `REST`, `REST_UP`, `FPS`.
- `PARTS[name]`: each part's `ob`, `pivot` and `at`.
- `EYES`, `FACES`, `body` (it turns) and `rig` (it moves and squashes).

### Example: a cheer

```python
# Cheer: both arms shoot up as it hops, and come down as it lands. 1.2 s.
pose(5, squash=SQ)
pose(8, squash=-SQ * 0.6)
pose(22, up=HOP * 0.8, squash=-SQ * 0.3)
pose(36, up=0, squash=0)
pose(39, squash=SQ * 1.2)
pose(46, squash=0)
for arm, side in (("ArmL", -1), ("ArmR", 1)):
    part_pose(arm, 6, turn=(0, 0, 0))
    part_pose(arm, 14, turn=(0, -150 * side, 0))
    part_pose(arm, 34, turn=(0, -150 * side, 0))
    part_pose(arm, 44, turn=(0, 0, 0))
face(10, "happy")
jiggle(36)
sparkles(20)
render(1, 72)
```

### Example: steam off a cup

Set `"effects": {"color": "#FFFFFF"}` in the spec, so the wisps are white.

```python
# Fresh: three wisps of steam rise off the top while it sways, eyes happy. 1.5 s.
face(6, "happy")
for k, x in enumerate((-0.3, 0.0, 0.3)):
    wisp = sprite("line", f"Steam{k}", (x, HALF_HEIGHT + 0.3 + REST_UP), 0.22)
    pop(wisp, 8 + 10 * k, hold=24)
    drift(wisp, 8 + 10 * k, 0.05 * (k - 1), 0.5, 36)
for f, deg in ((10, 0), (30, 4), (50, -4), (70, 0)):
    pose(f, turn=(0, deg, 0))
face(80, "open")
render(1, 90)
```

### Example: a tail wag

```python
# Happy to see you: a quick wag, a little bounce, and happy eyes. 1 s.
face(4, "happy")
for f, deg in ((4, 0), (10, 28), (16, -24), (22, 26), (28, -20), (34, 14), (40, 0)):
    part_pose("Tail", f, turn=(0, deg, 0))
pose(6, squash=SQ * 0.5)
pose(14, up=0.08, squash=-SQ * 0.3)
pose(22, up=0, squash=0)
face(50, "open")
render(1, 60)
```

### Keep in mind

- Key the rest pose again where a move ends. Without it, the next key interpolates from wherever the last one was.
- Overlapping moves are fine: `pose` and `part_pose` key only what you give them.
- Leave about 10 frames of stillness at the end of a reaction. An app may hold the last frame, and the eye reads that pause as the landing.
- For a loop, make the last key equal the first, and render to one frame before it. A 30-frame spin renders 1 to 30, because frame 31 would equal frame 1.
- Draft a new shot with `--step 3` and a small `--size`, and tile the frames with `encode.sh sheet`.
