---
name: next-session
description: Hand off to a fresh session and start it. Writes a handoff doc plus a ready-to-run prompt, then opens a new Claude Code session that runs that prompt. Use for /next-session, "start a new session with this", "continue this in a fresh session".
argument-hint: "What should the next session do?"
disable-model-invocation: true
---

# Next session

Goal: the user runs `/next-session <focus>` and ends up with a new session already working on the next step, without copying anything by hand.

## 1. Write the handoff doc

Follow the same rules as the `handoff` skill:
- Summarise only what a fresh agent needs to continue.
- Reference existing artifacts (plans, specs, commits, files) by path instead of copying them.
- Redact secrets, keys and personal data.
- Include a "Suggested skills" section.
- Treat the arguments as the next session's focus.

Save it to the OS temp dir (`echo $TMPDIR`), not the workspace:
`$TMPDIR/<project-folder-name>-handoff-<YYYYMMDD-HHMM>.md`

## 2. Write the prompt

Aim for about 1,500 characters. It must work with no memory of this conversation:

```
<One line: the goal of this session.>

First read the handoff: <absolute path to handoff doc>
Working directory: <absolute cwd>
Plan / spec to follow: <paths, if any>

Start with: <the first concrete step>.
Then: <the next 1–3 steps>.

Constraints: <decisions already made, what to ask the user before doing, e.g. large downloads, commits, deploys>.
Stop and check in with the user when: <milestone or verification point>.
Suggested skills: <names>.
```

Save it next to the handoff doc as `…-prompt.md`. Show it to the user in a fenced block.

## 3. Start the new session

Use the first option that works. Load deferred tools with ToolSearch before calling them.

1. **A Desktop app session starter.** Search ToolSearch for `start_session` and `hand_off_to_session`. If either exists, start a local session in the same working directory with the prompt as its first message, then give the user a link to it: `[title](#<sessionId>)`.
2. **`mcp__ccd_session__spawn_task`** (Desktop app). Create a chip with the prompt, a title such as "Continue: <focus>", and a one-line tldr. Tell the user one click starts it.
3. **Terminal** (CLI, or when the tools above are missing):
   - With terminal tools (`mcp__terminal__open_terminal_tab` + `run_in_terminal`): open a new tab and run
     `cd "<cwd>" && claude "$(cat '<prompt file>')"`
   - Without them, on macOS and only after the user agrees:
     `osascript -e 'tell application "Terminal" to do script "cd \"<cwd>\" && claude \"$(cat \\\"<prompt file>\\\")\""'`
4. **Fallback.** Print that command in a `bash` block so the user can run it.

## Rules

- Don't archive, stop or close the current session unless the user asks.
- Never put secrets in the prompt or the files.
- Finish with a short report: where the handoff and prompt were saved, and how the new session was started (link, chip, or terminal command).
