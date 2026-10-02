---
name: ui-art-prompts
description: Craft image-generation prompts (Midjourney, DALL·E/gpt-image, Ideogram, Stable Diffusion, Firefly) for painterly art assets used inside product UIs — login and auth backdrops, hero sections, empty states, onboarding art, marketing pages. Use this whenever the user wants a prompt for an image, painting, illustration, background, or art asset for their app or site; asks "give me a prompt for…" about any visual; or wants art that UI elements (cards, text, dashboards) will sit on top of — even if they never say the word "prompt".
---

# UI Art Prompts

Generate prompts that produce **art that works as a UI asset**, not just a pretty picture. A painting that wins on its own can fail the moment a login card lands on top of it. The craft in this skill is designing the image *around* the interface that will sit on it.

## Workflow

### 1. Understand the seat before the art

Before writing anything, establish (ask only for what you can't infer from context — if the user's project is in the conversation, read the brand colors and mood from it):

- **Where does it sit?** Full-bleed background, hero panel, side split, empty state, card thumbnail?
- **What sits on top?** A dark card, light text, a dashboard screenshot, nothing? What color is that element?
- **Brand palette and mood** — pull hex values from their codebase/design tokens if available, and translate them into pigment words (e.g. `#E9A94A` → "warm amber, golden ochre").
- **Which generator?** Default to a tool-agnostic main prompt plus per-tool settings if unknown.

### 2. Pick a style deliberately

Read [references/styles.md](references/styles.md) and choose (or offer 2–3) styles that match the product's tone. Each entry has the vocabulary that actually steers generators — movement names, artist-era references, medium words, palette language. Don't freestyle a style description when the library has tested vocabulary for it; do freestyle when the user wants something the library doesn't cover, using the same anatomy.

### 3. Compose the prompt

Every prompt has five jobs, in roughly this order (front-loaded words carry more weight in most generators):

1. **Medium + movement** — "19th-century American luminist landscape oil painting, Hudson River School". Naming a movement or era does more than ten adjectives.
2. **Scene** — concrete subjects with spatial placement ("pines framing the right edge", "calm empty sky occupying the upper half"). Vague scenes produce cluttered images.
3. **The quiet zone** — explicitly reserve the region where UI will sit: low detail, gentle value contrast, no focal points. Say it as composition ("soft hazy sky", "still glassy water", "open field of muted color in the center-left"), not as an instruction ("leave space for text" — generators ignore that or render literal empty boxes).
4. **Palette + light** — 4–6 pigment words tied to the brand, plus a light quality ("gentle diffuse golden-hour light"). Add "muted, faded, aged varnish patina" for backgrounds — saturated art fights UI.
5. **Texture + finish** — "fine visible brushwork, subtle canvas texture". This is what makes it read as a painting instead of a digital render.

End with exclusions folded into the prompt ("no people, no buildings, no text") *and* a separate negative prompt for tools that support one.

### 4. Deliver in the standard format

Always structure the answer like this:

```markdown
**Main prompt:**
> [the full prompt as one flowing paragraph]

**Negative prompt** (for tools that support it):
`photorealistic, modern, vibrant colors, text, watermark, frame, [scene-specific exclusions]`

**Settings:**
- Aspect ratio: [ratio + why — tie it to where the asset sits]
- [Tool-specific flags: e.g. Midjourney `--ar 16:9 --style raw`, DALL·E size]

**Integration notes:**
- [Where the quiet zone is and what UI goes there]
- [Contrast guidance: overlay/scrim strength, whether text needs a shadow]
- [What to regenerate or adjust if the first result fights the UI]
```

The integration notes matter as much as the prompt — the user is going to put this image *under an interface*, and telling them "add a `rgba(26,21,14,.2)` scrim" or "if the sky comes out busy, reroll — that's where your card sits" saves them a failed round-trip.

### 5. Offer variations

Offer one or two alternates when it's cheap to do so: a different style from the library that also fits the brand, or the same style at a different time of day/season. Variations teach the user what the levers are.

## Aspect ratio quick reference

| Asset seat | Ratio | Note |
|---|---|---|
| Full-bleed page background | 16:9 or wider (21:9) | Must survive cropping at odd window sizes — keep focal interest away from edges |
| Hero split panel | 4:5 or 3:4 | Vertical seat; anchor interest in the visible half |
| Empty state / spot illustration | 1:1 or 4:3 | Usually needs to sit on a flat color — specify that ground in the prompt |
| Mobile onboarding | 9:16 | Quiet zone typically bottom third (buttons) |

## Example

**User:** "I need a background for my meditation app's onboarding, something calm and Japanese-feeling, buttons at the bottom."

**Response shape:** Ukiyo-e/Japanese ink-wash entry from the style library → scene with mist-dissolved mountains and a large area of empty paper tone in the lower third (the quiet zone for buttons) → palette pulled from the app's sage/indigo tokens → 9:16 → integration note that the paper-tone region should sit within ±5% lightness of the app background so the transition is seamless.

## What to avoid

- **Kitchen-sink prompts.** Twelve style words cancel each other out. One movement, one medium, one light.
- **"Leave empty space for my login form."** Generators render this literally or ignore it. Describe the emptiness as *part of the scene*.
- **Default saturation.** Every generator over-saturates. Backgrounds need "muted, faded, desaturated antique tones" said explicitly.
- **Forgetting the fallback.** Remind the user to keep a CSS gradient fallback approximating the painting's palette, so the page never flashes empty while the image loads.
