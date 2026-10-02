# Video

A 3Blue1Brown-style explainer: a dark canvas, and shapes that build and change while a voice explains. Build it with Manim Community Edition, the open version of the engine that 3Blue1Brown wrote for his videos.

The order never changes: script, then voice, then animation. The voice sets the clock, and the animation fits the voice.

Work in one output folder. At the end, it holds:

```
<out>/
  script.json     the scenes: id, what to say, what to show
  audio/          one audio file per scene, and durations.json
  explainer.py    the Manim scenes, made from the template
  media/          the renders from Manim
```

`<skill>` below means this skill's folder.

## 1. Script

- 60 to 150 seconds. Four to eight scenes. One idea per scene.
- Spoken STE-80: 15 words per sentence at most, because a listener cannot read a sentence again. About 150 words per minute.
- The picture shows what the voice says, at the same moment.
- Write `script.json`:

```json
[
  {"id": "01-hook", "say": "Every website has a number. Your browser needs that number to find it.", "show": "A browser on the left, a globe on the right, a question mark between them."},
  {"id": "02-ask", "say": "So the browser asks a DNS server for the number.", "show": "An arrow labeled 'example.com?' goes from the browser to a new DNS box."}
]
```

- Check it: `python3 <skill>/scripts/ste_check.py script.json --max-words 15`.

## 2. Voice

```
python3 <skill>/scripts/narrate.py <out>/script.json
```

It writes one audio file per scene into `audio/`, and `audio/durations.json` with the length of each. A second run voices again only the scenes whose words changed.

Voices:

- **macOS `say`** is the default. It is free and works offline. The premium voices sound much better than the standard ones. List the installed voices with `say -v '?'`, and install more in System Settings › Accessibility › Spoken Content › System Voice › Manage Voices. Then pass `--voice "Ava (Premium)"`. `--rate 170` sets the words per minute.
- **ElevenLabs** gives the most human voice. It costs money for each character, so use it only after the user says yes. The script reads the key from `ELEVENLABS_API_KEY` in the environment, so the key stays out of every file. Add `--engine elevenlabs`, and `--voice-id <id>` for a voice other than the default.
- **Any other engine** works too, for example a local neural voice like Kokoro or Piper. It must write one audio file per scene and the same `durations.json`.

## 3. Animation

**Tools.** Check with `manim --version` and `uv --version`. If neither exists, ask the user, then install:

```
brew install cairo pkg-config
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Run Manim through uv, which needs no global install: `uv run --with manim manim ...`. LaTeX is not necessary. Use `Text` and `MarkupText`. Use `MathTex` only when the `latex` command exists.

**Scenes.** Copy `<skill>/scripts/explainer_template.py` to `<out>/explainer.py`. Write one `with self.beat("<id>") as t:` block per scene, in script order. `t` is the length of that scene's narration in seconds. Make the run times in the block add up to about `t`. The template waits out the rest, and it prints a warning when a block runs longer than its narration.

**The 3Blue1Brown look:**

- A dark background and few colors. Each color means one thing for the whole video.
- Build things piece by piece in front of the viewer.
- Change one shape into the next with `Transform` or `ReplacementTransform`, rather than a cut.
- Keep the thing the voice talks about in the center. Fade the rest.
- Short, large text. The voice carries the detail.

## 4. Render and check

Make a fast draft, then the final:

```
cd <out>
uv run --with manim manim -ql explainer.py Explainer
uv run --with manim manim -qh explainer.py Explainer
```

`-ql` gives 480p for drafts and `-qh` gives 1080p. The video goes to `media/videos/explainer/<quality>/Explainer.mp4`.

Check the video before you show it:

- `ffprobe` lists an audio stream, and the video length is close to the sum of the lengths in `durations.json`.
- Take one frame from the middle of each scene with `ffmpeg -ss <seconds> -i Explainer.mp4 -frames:v 1 frame-<n>.png`, and look at it. Fix text that overlaps and anything that goes off the edge.

Then open the video for the user.

Done when the video plays with the voice in sync, and no checked frame has overlapping or clipped text.

## Topics about an interface

When the explainer is about an app or a web page, an HTML animation can show it better than Manim. HyperFrames (hyperframes.heygen.com) renders an HTML page to MP4. Add the narration to that MP4 with ffmpeg.
