#!/usr/bin/env bash
# Installs the skills in this repo for Claude Code, and the skills from other
# people's repos that others.txt lists.
#
#   ./install.sh            link each skill in skills/ into ~/.claude/skills
#   ./install.sh status     show each skill and whether it is installed
#   ./install.sh others     install the missing skills that others.txt lists (needs npx)
#   ./install.sh snapshot   update others.txt from the skills installed with `npx skills`
#
# The install makes links, not copies, so an edit in this repo is live at once.
# Set CLAUDE_SKILLS_DIR to install into a different folder.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
OTHERS="$REPO/others.txt"
LOCK="$HOME/.agents/.skill-lock.json"

link_all() {
  mkdir -p "$TARGET"
  local dir name dest changed=0
  for dir in "$REPO"/skills/*/; do
    dir="${dir%/}"
    name="$(basename "$dir")"
    dest="$TARGET/$name"
    [ -f "$dir/SKILL.md" ] || { echo "skipped $name: it has no SKILL.md"; continue; }
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$dir" ]; then
      continue
    elif [ -L "$dest" ] && [ ! -e "$dest" ]; then
      ln -sfn "$dir" "$dest"
      echo "linked  $name (replaced a broken link)"
    elif [ -e "$dest" ] || [ -L "$dest" ]; then
      echo "skipped $name: $dest is already there. Move it away, then run this again."
      continue
    else
      ln -s "$dir" "$dest"
      echo "linked  $name"
    fi
    changed=1
  done
  # a link into this repo whose skill folder is gone
  for dest in "$TARGET"/*; do
    if [ -L "$dest" ] && [ ! -e "$dest" ]; then
      case "$(readlink "$dest")" in
        "$REPO"/skills/*) rm "$dest"; echo "removed $(basename "$dest"): it is no longer in skills/"; changed=1 ;;
      esac
    fi
  done
  [ "$changed" = 1 ] || echo "all skills in skills/ are linked"
}

status() {
  local dir name dest source skills skill
  echo "This repo -> $TARGET"
  for dir in "$REPO"/skills/*/; do
    dir="${dir%/}"
    name="$(basename "$dir")"
    dest="$TARGET/$name"
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$dir" ]; then
      echo "  ok       $name"
    elif [ -e "$dest" ] || [ -L "$dest" ]; then
      echo "  clash    $name: another skill has this name"
    else
      echo "  missing  $name: run ./install.sh"
    fi
  done
  echo "Other repos (others.txt)"
  while read -r source skills; do
    for skill in $skills; do
      if [ -e "$TARGET/$skill" ]; then echo "  ok       $skill ($source)"; else echo "  missing  $skill ($source): run ./install.sh others"; fi
    done
  done < <(grep -vE '^\s*(#|$)' "$OTHERS")
}

install_others() {
  local source skills skill flags
  command -v npx >/dev/null || { echo "npx is missing. Install Node.js first."; exit 1; }
  while read -r source skills; do
    flags=""
    for skill in $skills; do
      [ -e "$TARGET/$skill" ] || flags="$flags --skill $skill"
    done
    [ -n "$flags" ] || continue
    echo "installing from $source:${flags//--skill /}"
    # $flags is unquoted on purpose: skill names have no spaces, and each one becomes its own argument
    npx --yes skills add "$source" $flags --global --yes --agent claude-code </dev/null
  done < <(grep -vE '^\s*(#|$)' "$OTHERS")
  echo "done. ./install.sh status shows the result."
}

snapshot() {
  [ -f "$LOCK" ] || { echo "no $LOCK: nothing was installed with npx skills"; exit 1; }
  python3 - "$LOCK" "$OTHERS" <<'PY'
import json, sys
from pathlib import Path

lock, others = Path(sys.argv[1]), Path(sys.argv[2])
header, sources = [], {}
for line in others.read_text().splitlines() if others.exists() else []:
    if not line.strip() or line.lstrip().startswith("#"):
        if not sources:
            header.append(line)
        continue
    source, *skills = line.split()
    sources[source] = set(skills)

from_lock = {}
for name, entry in json.loads(lock.read_text())["skills"].items():
    from_lock.setdefault(entry["source"], set()).add(name)
sources.update(from_lock)  # the lock wins for its sources; lines it doesn't know stay

lines = header + [f"{source} {' '.join(sorted(skills))}" for source, skills in sorted(sources.items(), key=lambda s: s[0].lower())]
others.write_text("\n".join(lines) + "\n")
print(f"others.txt: {len(sources)} repos, {sum(len(s) for s in sources.values())} skills")
PY
}

case "${1:-link}" in
  link) link_all ;;
  status) status ;;
  others) install_others ;;
  snapshot) snapshot ;;
  *) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 1 ;;
esac
