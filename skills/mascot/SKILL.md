---
name: mascot
description: Makes cute, polished mascot characters and app icons in the glossy "glowing sticker" style (a soft body lit from within, a frosted edge glow, flat cartoon eyes, a prop like a halo, sparkles, an icon glow). Works from a reference image (measured and traced pixel by pixel) or from a description, renders PNGs on macOS with Core Graphics, and compares side by side until it matches. Use when the user wants a mascot, a cute character, an app icon with a character, moods or variants of a mascot, or says a mascot doesn't look as good as a reference.
argument-hint: "<reference image or description>"
---

# Mascot

A mascot reads as high quality when it has five things: colours that stay saturated, a body close to the background's hue with a pale glow along the inside of its edge, eyes like flat stickers, one bright prop, and a soft shadow and glow that give depth. Most attempts miss on one of these, and adding detail never makes up for it.

This skill draws the mascot from a JSON spec with `scripts/render.swift`. The spec holds every shape and colour, so each fix is one number, and a render takes about a second.

## Steps

1. **Read the brief.** Get a reference image or a description: the shape, the colours, the prop, the mood. Decide the look:
   - **Glowing sticker** (the default): flat shapes and soft glows. Most app-icon mascots are this, even when they look 3D.
   - **True 3D toy** (clay, plastic, real lighting): use Blender. Read [blender.md](blender.md).

   Done when you know the shape, the palette and the look.
2. **Compile the tools** once per session:
   ```bash
   swiftc -O scripts/render.swift -o "$TMPDIR/mascot-render"
   swiftc -O scripts/measure.swift -o "$TMPDIR/mascot-measure"
   ```
3. **Measure the reference** (skip this step without one). Never guess shapes or colours from a reference. Measure them. Read [measuring.md](measuring.md).

   Done when you have:
   - the icon's box in the reference's pixels, which becomes the spec's `space`;
   - the background's top, bottom and under-character colours;
   - the body's fill, glow and edge points every 50 to 100 pixels;
   - each eye's box and its pupil and shine;
   - the prop's geometry;
   - the sparkle positions.
4. **Write the spec.** Copy [examples/drop.json](examples/drop.json) and change it. [spec.md](spec.md) lists every field.
   - With a reference, set `space` to the icon's box and type the measurements in as they are.
   - Without one, use the 0 to 1024 space and the proportions in [style.md](style.md).
   - Draw the body as one SVG path of cubic curves. Keep each joint smooth: the control points either side of a point lie on one line.

   Done when every value comes from a measurement or from style.md.
5. **Render.**
   ```bash
   "$TMPDIR/mascot-render" spec.json out/ [reference.png]
   ```
   This writes four files:
   - `icon.png`, the app icon;
   - `preview.png`, the icon in the iOS shape;
   - `character.png`, the character alone, for use in the app;
   - `compare.png`, the reference beside yours, when you give a reference.
6. **Compare and fix.** Look at `compare.png`, or at `preview.png` without a reference. Find the differences in this order:
   1. the silhouette;
   2. the eyes: size, spacing, tilt and pupil;
   3. the glow: width and brightness;
   4. the shadow;
   5. the colours;
   6. the prop;
   7. the sparkles.

   Fix two or three per round, render again, and look again. The usual misses and their fixes are in [style.md](style.md). Done when what's left is detail the user would not see at Home Screen size, and the user agrees.
7. **Make it yours.** If you traced someone else's art, change one or two distinctive things before it ships: the hue, the prop, the hem, or the eye style. App Review rejects copycat icons, and the artist can have the app taken down. Say this to the user.
8. **Deliver.**
   - Send `preview.png` and `compare.png` to the user.
   - Offer the moods: copy the spec and set `"style": "happy"`, `"sleepy"` or `"closed"` on each eye.
   - Offer an icon set: `icon.png` drops into an `AppIcon.appiconset` as the light icon. Render a darker background for the dark icon.

## Rules

- Measure before you draw, and compare after you draw. Never judge a reference match from memory.
- Change one thing at a time when a look is close, so you know which change helped.
- Keep the spec as the source of truth. Do not edit the PNGs by hand.
- Keep each shape a separate spec entry, so moods and variants are spec edits, not redraws.
