# clips

Turn Twitch stream recordings into YouTube Shorts on your Mac. Paste a past
broadcast link into Claude Code. [OpenShorts](https://github.com/mutonby/openshorts)
picks the best moments, crops them to vertical and adds captions. The Shorts go
up on your channel one every 4 hours.

```
/clips up https://www.twitch.tv/videos/1234567890
/clips stats
/clips down
```

## What you need

- A Mac with Apple silicon and 16 GB of memory, and about 20 GB of free disk.
- [Claude Code](https://claude.com/claude-code), in the desktop app or the
  terminal.
- A YouTube channel, and the Google account it belongs to.
- About 30 minutes for the first setup, most of it waiting for downloads.

It costs nothing to run: Gemini's free tier picks the moments, YouTube's API
does the uploads, and Docker Desktop is free for personal use.

## Install

1. Install the skill. In Terminal:

   ```bash
   npx skills add Vansitha/skills --skill clips -g -a claude-code -y
   ```

   No Node.js on your Mac? Ask Claude Code instead: *"Install the clips skill
   from https://github.com/Vansitha/skills/tree/main/skills/clips"*.

2. Start a new Claude Code session and type:

   ```
   /clips setup
   ```

Claude downloads and sets up the rest, one step at a time. It stops for the
few things only you can do:

- type your Mac password when Docker Desktop installs,
- paste a free Gemini key from [Google AI Studio](https://aistudio.google.com/app/apikey)
  (into the terminal, not the chat),
- click through Google Cloud to make a sign-in for your channel (Claude gives
  you each link),
- pick your channel when your browser asks.

When it says *All set*, you're done.

## Using it

| Command | What it does |
|---|---|
| `/clips up <link>` | Clips a Twitch past broadcast (`twitch.tv/videos/…`), or a YouTube or Kick video. Takes about twice the video's length on a recent Mac. To clip part of a long stream, say so: *"/clips up <link>, just 30 minutes from 1:15:00"*. |
| `/clips stats` | Clips made, uploaded and waiting, with each one's file and YouTube link. |
| `/clips down` | Stops everything and quits Docker Desktop. Scheduled Shorts still go live. |
| `/clips auth` | Signs in to YouTube again, when stats says the sign-in expired. |

Your clips are saved in `~/clips/library`, one folder per stream. Settings are
in `~/.config/clips/config.json`:

- `upload_mode`: `schedule` (the default), `private` to review each Short in
  YouTube Studio before it goes public, or `none`.
- `every_hours` and `first_delay_hours`: the gap between Shorts (4) and before
  the first one (3).
- `target_clips`: Shorts per stream, 1 to 15 (10).
- `clip_min_seconds` and `clip_max_seconds`: how long each Short is (45 to 90).
- `youtube`: tags and a description footer for every upload, for example
  `"youtube": {"tags": ["GTA 6", "Shorts"], "description_footer": "…"}`.

## Before you post

- **Only clip your own streams, or streams whose owner said yes.** Every link
  you clip tells OpenShorts you have the rights to it. Reposting someone else's
  stream earns copyright strikes, and YouTube deletes a channel at three.
- **Watch launch-week clips before they go live.** Rockstar takes down story
  spoilers, and the AI can't tell what a spoiler is. Use `upload_mode: private`
  to check each one first.
- **A new channel can upload about 10 videos a day.** Verify your phone number
  at [youtube.com/verify](https://www.youtube.com/verify) to raise the limit.
  Clips over the limit wait and upload later.
- **Gemini's free tier lets Google use what you send it** to improve its
  products. A paid key costs about a cent per 20 minutes of footage.

## How it works

`/clips setup` downloads a tested version of OpenShorts (MIT licence) to
`~/clips/openshorts` and runs it in Docker. `scripts/clips.py` sends it your
links and follows the jobs. For a Twitch stretch, it downloads only that part
of the stream. `scripts/upload.py` posts the finished clips with the YouTube
Data API, signed in through your own Google Cloud project. Your sign-in files
stay in `~/.config/clips/youtube/` on your Mac.

To uninstall: run `/clips down`, then delete `~/clips`, `~/.config/clips` and
`~/.claude/skills/clips`. In Docker Desktop, delete the `openshorts-*` images.
