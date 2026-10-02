# Diagrams

A diagram shows the shape of an idea at once. Words can only give it one piece at a time.

## Match the drawing to the shape

| The idea is about | Draw |
|---|---|
| Something that moves through steps or parts | A flow: boxes and arrows, left to right |
| Who talks to whom, and in what order | A sequence diagram: one lane per actor, time goes down |
| Parts inside parts | Nested boxes |
| A choice | A decision tree |
| Modes, and what moves the system between them | A state diagram |
| Options side by side | A comparison table |
| Amounts | A chart: bars to compare, a line for change over time |
| A change | Before and after, side by side, with the change marked |

## Rules

- **One idea per diagram.** At more than about nine boxes, split it into an overview and a zoom-in.
- **A straight main path.** The main path goes straight across or straight down. Side paths branch off it.
- **Boxes are nouns, arrows are verbs.** Label each arrow with what moves along it or what it does.
- **Real names.** Use the names from the user's code or system.
- **One accent.** Mark the one thing to look at with one color or a bold box. Keep the rest quiet.
- **A caption.** One to three STE-80 sentences under the diagram. Say where to start and what to notice.

## Pick the medium

Use the richest medium this environment can show:

1. **An inline visual tool**, if the environment has one (a tool that renders SVG or HTML in the conversation). Follow its own guidance.
2. **An SVG or HTML file** in the output folder, opened for the user (`open` on macOS, `xdg-open` on Linux). If the environment has its own diagramming guidance, such as a diagramming skill, follow it for the drawing mechanics.
3. **Box drawing in a code block**, for a plain terminal and six boxes or fewer:

```
┌─────────┐  request  ┌────────┐  query  ┌──────────┐
│ Browser │ ────────▶ │ Server │ ──────▶ │ Database │
│         │ ◀──────── │        │ ◀────── │          │
└─────────┘   page    └────────┘  rows   └──────────┘
```

Use Mermaid only when the user's viewer renders it, as GitHub and many Markdown apps do.

Done when each arrow has a label, the main path reads without the caption, and the caption says where to start.
