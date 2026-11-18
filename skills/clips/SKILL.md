---
name: clips
description: Runs a local OpenShorts clipping pipeline that turns stream recordings into YouTube Shorts. `/clips setup` installs everything on a new Mac and walks the user through the parts only they can do; `/clips up <url>` starts Docker and OpenShorts, clips a Twitch past broadcast (or YouTube/Kick video), saves the clips and auto-uploads them to YouTube; `/clips stats` shows clips created, uploaded and pending, with each clip's file and YouTube link; `/clips down` shuts everything down; `/clips auth` signs in to YouTube again. Use for /clips.
argument-hint: "setup | up <url> | stats | down | auth"
disable-model-invocation: true
---

# Clips

The user runs `/clips <command>`. Each command is one call to the bundled
script, which does the real work, so run it rather than redoing its steps by
hand:

```bash
python3 "<this skill's base directory>/scripts/clips.py" <command> [args]
```

Show the user what it prints, tidied up as described below. Keep replies short:
the user wants to paste a link and get on with streaming.

Some commands need the user's own typing (a password, a key, a browser
sign-in). Run those "in a terminal the user can type into": a Terminal panel
tab in the desktop app, or otherwise give them the exact command to paste into
Terminal.app and wait for them to say it's done.

## `/clips setup`

For the first run on a Mac, or when another command says it isn't set up. Run
`setup`. It does what needs nobody (downloads OpenShorts at the tested version
into `~/clips/openshorts`, writes its `.env`, saves settings, moves a Google
client file from Downloads into place) and prints a checklist of what's left.
Pass `--openshorts DIR` only if the user wants OpenShorts somewhere else or
already has a checkout.

Take the remaining steps in the order printed, one at a time, and run `setup`
again after each until it prints "All set". One step per message: what to
click, type or paste.

- **Docker Desktop**: run `brew install --cask docker` in a terminal the user
  can type into (it asks for their Mac password, which only they can type).
  Without Homebrew, send them to the download link. Then they open Docker
  Desktop once and accept its terms.
- **Build**: as soon as Docker runs, start `build` in the background (10 to 30
  minutes) and go on with the next steps; don't wait for it.
- **uv**: `brew install uv`, or without Homebrew
  `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- **Gemini key**: run `key` in a terminal the user can type into. The key goes
  straight into OpenShorts' `.env`, never through this chat, so ask them to
  paste it there and not here.
- **Google sign-in client**: read `references/google-setup.md` and walk the
  user through it, part by part. It ends with a file in Downloads, which the
  next `setup` picks up.
- **YouTube sign-in**: run `auth` in a terminal the user can see; it opens
  their browser (part D of the Google guide says what they'll see).

When it prints "All set", tell them they're ready: `/clips up <link>` with a
past broadcast from a channel's Videos tab.

Settings in `~/.config/clips/config.json` the user may want to change:
`upload_mode` (`schedule`, `private` or `none`), `every_hours`,
`first_delay_hours`, `target_clips` (1-15 clips per stream), `clip_min_seconds`
and `clip_max_seconds` (45 and 90 by default), and a `youtube`
section for the uploader (for example `"youtube": {"tags": ["GTA 6", "Shorts"],
"description_footer": "…"}`).

## `/clips up <url>`

Run `up <url>`. It starts Docker Desktop and OpenShorts if needed, sends the
link to OpenShorts, and starts a background worker that waits for the clips,
copies them to the clips folder, and uploads them according to `upload_mode`.
It returns in a minute or two; the clipping takes about twice as long as the
footage, so don't wait for it. Tell the user it started, roughly how long it
will take, and that `/clips stats` shows progress.

- The script submits the link with OpenShorts' rights confirmation set. That is
  only right for the user's own streams or ones they have permission to clip.
  If the link is clearly someone else's channel, say so before running it.
- To clip only part of a long stream ("just 30 minutes", "the bit around
  2 hours in"), add `--from H:MM:SS --minutes N` (minutes default to 30). The
  script downloads only that stretch first, so `up` takes a few minutes longer
  to return; OpenShorts' upload limit allows roughly 40 minutes of 1080p.
- `up` with no URL just starts everything (and resumes waiting uploads).
- If it refuses a Twitch channel page, the user needs the past broadcast link
  from the channel's Videos tab (`twitch.tv/videos/…`).
- If it says the link was already clipped, ask before re-running with `--again`.

## `/clips stats`

Run `stats` and present it like this: the four counts first, as plain lines
(`Clips created`, `Uploaded` with its live/scheduled split, `Pending`,
`Processing`), then a short list per stream with each clip's title, its status
(live, scheduled with the time, private, or pending), its YouTube link, and its
file path. Make the file paths and links clickable. If a stream shows a `!`
line (for example "sign-in expired"), put that first and say what to do.

## `/clips down`

Run `down`. If it exits saying a stream is still being clipped, tell the user
that stopping now throws that stream's progress away, and only run
`down --force` if they say so. Otherwise report what it stopped. Clips already
uploaded or scheduled are on YouTube and aren't affected; clips still waiting
to upload go up at the next `/clips up`.

## `/clips auth`

While the Google app is in Testing mode the YouTube sign-in expires every 7
days, and stats then shows "sign-in expired". Run `auth` in a terminal the user
can see (it opens their browser and waits for them to sign in). After it
succeeds, waiting uploads retry on their own. Publishing the Google app (step 4
of `references/google-setup.md`) stops the weekly expiry.

## Where things are

- Clips: the `library_dir` in the config, one folder per stream
  (`YYYY-MM-DD_<job>/NN_<title>.mp4`). OpenShorts deletes its own copies after
  a few days; these stay.
- YouTube sign-in and upload log: `~/.config/clips/youtube/` (`uploaded.json`
  lists every upload; the other two files are private).
- Worker log, for when something looks stuck: `~/.config/clips/worker.log`.
