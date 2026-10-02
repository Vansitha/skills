---
name: x-builder-voice
description: Draft, rewrite, and sharpen X/Twitter posts in the user's personal builder voice, covering AI agents, product building, engineering lessons, build-in-public observations, and Riv teasers. Use for rough ideas, hook alternatives, individual posts, or requested threads.
---

# X Builder Voice

Write like a person building AI products and thinking through what happens along the way. The recurring point of view is:

> I'm building AI agents, and I'm sharing what I discover when I try to make them actually useful.

Make the reader curious about a real experience, decision, or unresolved problem. Favor experience → observation → insight. Preserve the user's meaning and level of certainty over a punchier claim.

## Voice anchors and evidence

These anchors come from the user's supplied posts and ideas:

- “As a kid, I always wanted my computer to just get what I was doing.” Personal motivation makes the technical subject approachable.
- “Somehow, we’re now at a point where we can actually build that. Well... almost.” Optimism comes with awareness of limitations.
- “There’s a huge gap between a cool agent demo and an agent that’s actually useful.” Practical usefulness is the recurring concern.
- “What works. What breaks. The limitations. The engineering behind it.” The user wants to share the messy parts of building.
- The user builds with AI but says they rarely use it outside coding and technical work. They wonder how useful agents are to people outside tech and are building something to explore that gap.

The childhood-story post received 200+ impressions; the other supplied examples received 20, 42, and 84. This is a small, uncontrolled sample. It suggests trying more personal stories, but does not establish why a post performed better or predict virality. Previous assistant suggestions are draft ideas, not evidence that the user performed those experiments or shipped those features.

Riv is a product name associated with this writing context. Its capabilities, architecture, availability, and release schedule must come from the current brief or confirmed user material. Do not infer them from earlier assistant suggestions. A past tentative Tuesday teaser is not a standing release commitment.

## Voice rules

- **Personal:** Use “I” for the user's experience. Use “we” sparingly for a shared builder habit, without claiming everyone behaves the same way.
- **Builder-first:** Lead with something observed, tried, broken, or questioned. Explain the consequence for the product or the person using it.
- **Conversational:** Use contractions, familiar words, and natural transitions. Fix typos without polishing away the personality. Do not insert mistakes to simulate authenticity.
- **Curious:** Let uncertainty stay visible when it is real: “I'm starting to wonder,” “maybe,” or “I haven't figured this out yet.” Avoid turning every sentence into a hedge.
- **Technically credible:** Keep details that explain the lesson. Translate jargon when the audience includes people outside tech. Do not flatten a specific engineering lesson into vague inspiration.
- **Non-corporate:** Sound like someone sharing work with peers. Avoid pitch-deck language, self-appointed thought leadership, and manufactured authority.
- **Readable:** Use short paragraphs and occasional standalone lines for emphasis. Vary the rhythm; do not place every clause on a separate line.
- **Restrained:** Usually skip hashtags, decorative headings, and lists in the post itself. An occasional 👀 for a teaser or 🤖 for a playful ending can fit; neither is a signature requirement.
- **Natural:** Occasional “honestly,” “well...,” or a fragment can work. Do not repeat verbal tics across every draft. Prefer periods and commas over elaborate punctuation.

The current request and newer user-approved examples override these defaults. Match any supplied draft's casing and energy unless asked to change them.

## Turn a rough idea into a post

1. **Extract the material.** Identify what happened, what the user thinks it means, the concrete detail supporting it, and what remains uncertain. Separate user facts from your own proposed explanations.
2. **Choose one point.** Complete this privately: “The interesting thing here is ___.” If the idea contains several lessons, select the strongest or use a thread only when requested or clearly needed.
3. **Find the tension.** Look for an expectation that met reality, a personal contradiction, a product tradeoff, or a question the work created. Do not manufacture conflict.
4. **Choose a structure.** Use the patterns below as options, not mandatory templates. A useful technical tip can be direct when there is no personal story to tell.
5. **Draft the body and sharpen the hook.** Make the opening point toward something the body actually delivers. Remove setup that merely announces thinking: “I've been thinking about something interesting lately.”
6. **Run a truth and voice pass.** Remove invented experience, overstated conclusions, generic filler, repeated ideas, and sales language. Retain the detail that makes this the user's post.
7. **Check the requested format.** Honor a supplied character budget or thread length. Do not silently expand a short post into a long post. If no format is given, choose the shortest version that preserves the idea; use the conversational longer form when the brief clearly calls for it. Never label a draft as fitting a platform limit without checking it using an appropriate counter.
8. **Deliver the draft.** Default to one recommended, copy-ready post with minimal explanation. Offer alternatives when requested or when they represent meaningfully different angles.

If a missing detail would materially change the story, ask one focused question. Otherwise draft from the available facts. For an engineering idea without a supplied experience, frame it as a question, hypothesis, or general explanation instead of inventing a first-person anecdote. Use placeholders only when the user wants a template.

## Hook patterns

Choose the pattern that fits the material. These are adaptable shapes, not opening lines to repeat mechanically.

| Pattern | Shape or example | When it fits |
| --- | --- | --- |
| Personal contradiction | “I build AI almost every day. But I barely use it outside work.” | Two true parts of the user's experience create tension. |
| Original motivation | “As a kid, I always wanted my computer to just get what I was doing.” | The origin story explains the present work. Do not invent childhood memories. |
| Expectation meets reality | “I thought [change] would help. Then [observed result].” | The user supplied an actual experiment or failure. |
| Concrete debugging surprise | “[Symptom] sent me looking at [suspect]. The issue was [confirmed cause].” | There is a verified cause, not just a guess. |
| Product question | “We keep talking about AI agents. I'm starting to wonder who we're building them for.” | The body develops a specific observation behind the question. |
| Changed mind | “I used to think [belief]. Building [thing] has made me less sure.” | The user actually held the belief and has a reason to reconsider it. |
| Small decision, real consequence | “The awkward part was deciding [specific choice].” | An overlooked design decision reveals a larger lesson. |

For “change the hook,” preserve the body and thesis unless a small continuity edit is necessary. Provide three to five distinct openings and identify a favorite in one sentence. Avoid five superficial rewordings of the same opening.

## Post structures

### Personal observation

Personal fact → tension → what it makes the user question → provisional takeaway.

Best for the gap between building with AI and using it in daily life. Let the post explore the question without pretending to know how all nontechnical people use AI.

### Engineering lesson

Concrete symptom → investigation or attempted fix → what the evidence showed → practical implication or remaining limitation.

Include enough detail for another builder to understand the lesson. Do not invent debugging time, tool counts, cost savings, root causes, or before/after results. If the diagnosis is uncertain, say so.

### Contrarian observation

Observed practice or prior belief → specific friction → bounded alternative → tradeoff.

Earn disagreement with a reason. Scope claims to the experience: “In this workflow...” or “What I keep running into...” An opinion can be clear without declaring an entire industry wrong.

### Build-in-public update

What the user worked on → one interesting decision or failure → what changed or what they will try next.

Give readers something beyond “still building.” Small unresolved problems are valid material. Do not turn each update into a victory or lesson if the user is still investigating.

### Technical tip

Concrete problem → technique or tool → why it helps → relevant limitation.

Use a personal opening only if the user actually tried it. Check changing product details against current primary documentation when making factual claims about commands, models, prices, or capabilities; if verification is unavailable, flag the uncertainty outside the draft rather than confidently repeating it.

### Riv teaser

Recognizable problem → why the user cares → a small, confirmed glimpse → optional next step.

Let the post offer an observation even without the teaser. Mention Riv when requested or when the audience has context; a problem-setting post can leave it unnamed. Use dates only when currently confirmed, preserving tentative language. Save “available now,” demos, links, and feature promises for confirmed releases. Do not attach a product plug to every engineering post.

### Requested thread

Opening thesis or story → distinct supporting steps → useful closing observation.

Each post should advance the argument. Avoid repeating the hook in every installment or adding an empty “follow for more” conclusion. Use numbering if it helps the requested format.

## Anti-patterns and repairs

| Avoid | Repair |
| --- | --- |
| “Everyone is building agents. Almost nobody is designing them.” | Narrow the claim to a concrete design problem the user has encountered. |
| “AI is changing everything.” | Start with the particular change, contradiction, or failure. |
| “10 tools you NEED to know 🤯” | Name the problem and explain the useful detail without inflated urgency. |
| “This changes everything,” “game-changing,” “unlock,” “revolutionize,” “supercharge” | State what the change actually lets someone do. |
| “Been cooking. Something huge is coming.” as the whole substance | Give the reader the problem or discovery behind the teaser. |
| Automatic “Thoughts?” or “Agree?” endings | End on the insight or ask a specific question the user actually wants answered. |
| “It's not about X. It's about Y.” in every draft | Explain the relationship or tradeoff directly. |
| Invented “spent 3 hours debugging” stories | Use supplied details, ask for the story, or write a hypothesis. |
| Universal conclusions from one trial | Describe what happened in that setup and what remains unknown. |
| Reusing the successful childhood hook everywhere | Reuse the personal specificity, not the biography. |

Do not promise impressions or virality. When performance data is supplied, use it to suggest experiments with angle, specificity, or structure. Distinguish observations from causal explanations and avoid claims about the platform's algorithm without evidence.

## Examples

These are voice illustrations, not additional facts about the user. The first two adapt supplied material. The others are hypothetical and require confirmation before being used as first-person accounts. Do not copy any example's facts into an unrelated draft.

### 1. Personal observation — grounded in the supplied idea

> I build with AI almost every day.
>
> Outside of coding and technical work, I barely reach for it.
>
> That feels strange, considering how much time I spend thinking about agents.
>
> It makes me wonder what would make AI useful enough for someone outside tech to use regularly.
>
> I've been building something to explore that gap. Still figuring a lot of it out.

### 2. Personal motivation — adapted from the user's original post

> As a kid, I always wanted my computer to just get what I was doing.
>
> Know when I'm stuck. Help me figure things out. Maybe do some of it for me.
>
> Building agents has made that feel possible. It's also shown me how much sits between a cool demo and something I'd actually rely on.
>
> I want to share more of that part here. What works, what breaks, and the weird engineering problems in between.

### 3. Engineering lesson — hypothetical

Use only if the user confirms the incident and result:

> My agent kept choosing the wrong tool for one task.
>
> I had two tool descriptions that sounded almost identical. Rewriting them made the distinction clearer, and that case started passing.
>
> I still need to check the other cases. But now I have a better place to look when tool selection goes wrong.

### 4. Contrarian product observation — hypothetical

Use only if the user confirms this is their view and experiment:

> I keep coming back to chat for my agent's UI because it's flexible.
>
> But a blank input asks the user to figure out what's possible before they've seen anything work.
>
> I'm trying a more guided starting point. The tricky part is keeping it useful when someone wants to do something I didn't anticipate.

### 5. Build-in-public failure — hypothetical

Use only if the user supplied or confirms this test:

> I watched someone try the flow I'd been building.
>
> They paused at a step I thought was obvious. I knew what the agent was waiting for because I'd written it. They had no way to know.
>
> I'm changing that screen before adding anything else.

### 6. Riv teaser — conditional example

Use only if the user confirms this positioning and wants to name Riv:

> I keep wondering how to make an agent useful to someone who doesn't know what an agent is.
>
> That's one of the questions I'm exploring with Riv.
>
> I want to start with a problem someone already has and make the next step feel obvious. Still working out what that should look like 👀

## Final quality check

Before delivering, check:

- Is there one clear observation, and does the opening lead into it honestly?
- Could this come from the user who wrote the voice anchors, rather than any AI marketing account?
- Are personal experiences, technical claims, product details, and dates supported?
- Does the draft preserve uncertainty without becoming vague?
- Is the useful detail still there after tightening?
- Does the ending earn its place, including any question or teaser?
- Does it follow the requested length and format?

When the user revises a draft, treat the edit as voice evidence for the current work. Distinguish a recurring preference from a one-off choice. Update this skill only when asked, and never treat a request to write a post as permission to publish it.
