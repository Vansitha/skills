---
name: explain
description: Explainer ladder for making anything easy to understand. Plain words in STE-80 (80% of the way to ASD-STE100), then a diagram, an interactive HTML page, or a narrated 3Blue1Brown-style video. Use when the user asks to explain, break down or walk through something (code, a diff, a system, a concept, a paper or post), says they don't get it, or asks for an explainer, diagram, page or video of an idea.
argument-hint: "[words|diagram|page|video] <what to explain>"
---

# Explain

Models now do more of the work, so people spend more of their time understanding it. Your job is to move one idea into the reader's head with the least effort on their side. Custom, throwaway artifacts are cheap now. Use them when they help.

## The ladder

Each rung is easier to take in than the one before it. Each rung also costs more to make.

| Rung | What it is | Climb to it when |
|---|---|---|
| 1. Words | Plain text in STE-80 | Always. A fact, a definition, a reason. Most asks stop here. |
| 2. Diagram | A picture of the parts and how they connect | The idea has a shape: parts and links, a flow, steps in time, layers, choices, states. |
| 3. Page | An interactive HTML page | The reader learns by doing (change a value, step through a flow), the topic has many parts, or they will keep or share it. |
| 4. Video | A narrated, animated explainer | The idea moves over time, or the user asks for a video. |

Climb only as high as the idea needs. Build rungs 1 and 2 without asking. Build rung 3 when the request clearly fits it, and otherwise offer it in one line at the end. Ask before rung 4 unless the user asked for a video, because it takes minutes and can install tools.

If the user names a rung (`/explain diagram the auth flow`), use that rung.

Every rung carries words: captions, page text, narration. Those words are always STE-80.

## Steps

1. **Answer in one sentence.** Write the whole answer as one sentence an outsider gets. It opens the explanation on every rung. Done when it has 25 words or fewer and no unexplained term.
2. **Ground it.** When the idea is abstract, give one real example before the general rule. Take the example from the reader's world: their code, their product, their last message.
3. **Pick the rung** from the ladder.
4. **Build it.** Words: write them here. Diagram: read [diagrams.md](diagrams.md). Page: read [pages.md](pages.md). Video: read [video.md](video.md).
5. **Check the words.** Read each sentence against STE-80 below. For a page or a narration script, also run `python3 scripts/ste_check.py <file>` from this skill's folder. Done when you have fixed each flag or can defend it.

## STE-80

ASD-STE100 is the controlled English of aircraft maintenance manuals. Its rules make text easy for any reader, including people who read English as a second language. STE-80 goes 80% of the way: it keeps the rules below and drops the strict word list.

- **One topic per paragraph.** The first sentence states the topic. Six sentences at most.
- **Short sentences.** 20 words at most for steps, 25 for descriptions. One instruction per sentence.
- **Active voice.** Name who does what: "The server sends the token," not "The token is sent."
- **Simple tenses.** Present, past and future. The imperative for instructions.
- **One word, one meaning.** Give each thing one name and keep that name to the end. Repeat it rather than vary it.
- **Condition first.** "If the cache is empty, the app calls the server."
- **Keep the small words.** Write "the", "a" and "that". Full sentences, not telegraph style.
- **Three nouns in a row at most.** "Token refresh retry logic" becomes "the logic that tries the token refresh again".
- **One verb, not a phrase.** "Start," not "kick off". "Remove," not "get rid of". "Find," not "figure out".
- **Explain each term once.** Give a short plain meaning the first time, or use plain words instead.
- **Lists** for sequences, and for three or more parallel items.
- **A full stop where a dash would go.** Two ideas get two sentences.
- **Warnings put the command first, then the reason.** "Back up the database first. The migration deletes old rows."

**Strict mode.** The user can ask for full ASD-STE100. Then also use each word only in its most basic meaning. Use no -ing verb forms, and no passive voice in steps.

### Before and after

> **Before:** Under the hood, hitting a URL kicks off a DNS lookup, essentially asking a hierarchy of nameservers to resolve the domain into an IP, which gets cached so subsequent requests can skip the round-trip.
>
> **After:** A browser finds a website by its number, the IP address. A name like example.com is not that number. So the browser asks a DNS server for the number, and the DNS server sends it back. The browser keeps the number for some time. On the next visit, the browser uses the kept number and does not ask again.

## Where files go

Diagram files, pages and videos are throwaway by default. Save them in the session's scratchpad folder when there is one, and otherwise in `$TMPDIR/explain/<topic-slug>/`. Move them into the project only when the user asks. Always give the user the path or the link.
