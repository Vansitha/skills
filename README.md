# Skills

My skills for Claude Code. Each skill is one folder in `skills/`.

| Skill | What it does |
|---|---|
| [clips](skills/clips) | Clips stream recordings into YouTube Shorts with a local OpenShorts and uploads them. Friends: see its [setup guide](skills/clips/README.md). `/clips setup`, `/clips up <url>`, `/clips stats`, `/clips down`. |
| [explain](skills/explain) | Makes anything easy to understand: plain words, a diagram, an interactive page or a narrated video. |
| [mascot](skills/mascot) | Makes cute, glowing mascot characters and app icons, from a reference image or a description. |
| [next-session](skills/next-session) | Hands the work off to a fresh session and starts it. |
| [ui-art-prompts](skills/ui-art-prompts) | Writes image prompts for art that sits behind an app's interface. |
| [x-builder-voice](skills/x-builder-voice) | Drafts X posts in my builder voice. |

## Install on a Mac

```bash
git clone https://github.com/Vansitha/skills.git ~/Desktop/my_skills
cd ~/Desktop/my_skills
./install.sh
./install.sh others
```

`./install.sh` links each skill into `~/.claude/skills`. It makes links, not copies, so an edit in this repo is live at once. `./install.sh others` installs the skills from other people's repos that `others.txt` lists. `./install.sh status` shows what is installed.

## Install one skill

Anyone can install one skill with the [skills CLI](https://github.com/vercel-labs/skills), without a clone:

```bash
npx skills add Vansitha/skills --skill explain -g
```

## Day to day

- **A new skill:** make `skills/<name>/SKILL.md`, run `./install.sh`, then commit.
- **A changed skill:** edit it here. The link makes the change live.
- **A removed skill:** delete its folder and run `./install.sh`. The installer removes the old link.
- **A skill from someone else:** run `npx skills add <owner/repo> -g`, then `./install.sh snapshot`, then commit `others.txt`.
