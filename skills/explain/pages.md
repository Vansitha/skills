# Pages

A page beats a diagram when the reader learns by doing. Each control on the page changes the picture. That is the reason to build a page.

## Layout, top to bottom

1. **Title.** The topic in two to five words.
2. **The one-sentence answer**, large.
3. **The picture.** The rung 2 diagram, drawn in SVG or canvas so that its parts can light up.
4. **The walk-through.** Next and Back buttons, plus the arrow keys. Each step lights up one part of the picture and shows one to three STE-80 sentences.
5. **The playground**, only when a value drives the idea. A slider or an input changes the picture live. Example: a slider for the cache size moves the hit rate on a chart.
6. **What-if questions**, when the reader will act on this knowledge. Two or three questions, each answer hidden until a click.
7. **Terms**, when the page uses more than three terms. One plain line for each.

## Rules

- **Every control teaches.** It changes the picture. Cut motion that teaches nothing.
- **One self-contained file.** No build step. Load a library from a CDN only when it saves real work, for example D3 for a graph.
- **Real names and real numbers** from the user's code or data. Label each made-up number as an example.
- **Works for everyone.** Readable on a phone, light and dark themes, and a keyboard can drive the walk-through.
- **STE-80 text.** Run `scripts/ste_check.py` on the HTML file.

## Ship it

- If the environment has a tool that publishes pages or artifacts, use it. Follow its design guidance, which can ask you to load a design skill first.
- Otherwise, save `index.html` in the output folder and open it.

Done when the page loads with no console errors and each control changes the picture. If a browser tool is available, load the page and use each control once.
