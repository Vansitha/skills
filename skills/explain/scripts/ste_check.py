#!/usr/bin/env python3
"""Flag text that breaks STE-80, the plain-writing rules of the explain skill.

  python3 ste_check.py page.html
  python3 ste_check.py script.json --max-words 15    # narration: the "say" of each scene
  python3 ste_check.py notes.md --max-words 20       # steps

Checks sentence length, paragraph length, dashes, wordy phrases, phrasal verbs
and likely passive voice. It is a helper, not a judge: a flag you can defend may stay.
Exits with 1 when anything is flagged.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

MAX_SENTENCES = 6

WORDY = {
    "in order to": "to",
    "utilize": "use",
    "utilise": "use",
    "leverage": "use",
    "due to the fact that": "because",
    "at this point in time": "now",
    "prior to": "before",
    "subsequently": "then, later",
    "facilitate": "help",
    "a number of": "some, several",
    "in the event that": "if",
    "with regard to": "about",
    "is able to": "can",
    "approximately": "about",
    "commence": "start",
    "under the hood": "inside",
    "basically": "cut it",
    "essentially": "cut it",
    "actually": "cut it",
    "simply": "cut it",
}

# (verb stem, particle, plain verb); the stem also matches "kicks", "kicked", "kicking"
PHRASAL = [
    ("kick", "off", "start"),
    ("spin", "up", "start"),
    ("set", "up", "install, prepare"),
    ("figure", "out", "find"),
    ("find", "out", "learn, find"),
    ("carr", "out", "do"),
    ("get", "rid of", "remove"),
    ("come", "up with", "make, think of"),
    ("look", "into", "examine"),
    ("point", "out", "show"),
    ("turn", "on", "start"),
    ("turn", "off", "stop"),
    ("go", "through", "examine"),
    ("end", "up", "become"),
    ("show", "up", "appear"),
    ("hand", "off", "give, pass"),
]

PASSIVE = re.compile(
    r"\b(am|is|are|was|were|be|been|being|gets?|got)\s+(\w+ly\s+)?"
    r"(?!(?:often|even|open|then|when|seven|eleven|token|happen|listen|sudden)\b)"
    r"(\w{2,}ed|\w+en|made|done|sent|built|set|put|kept|held|known|shown|seen|given|taken|written|run|found|lost|paid|sold|told)\b",
    re.IGNORECASE,
)
DASH = re.compile(r"[–—]|\s--?\s")
SENTENCE_END = re.compile(r"(?<=[.!?])[\"')\]]*\s+(?=[A-Z0-9\"'(])")
WORD = re.compile(r"[A-Za-z0-9][\w'’./-]*")


def units_from_markdown(text):
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    text = re.sub(r"^>[ \t]?", "", text, flags=re.MULTILINE)
    text = re.sub(r"```.*?```", "\n\n", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", "Code", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    units, current = [], []
    for line in text.splitlines():
        stripped = line.strip()
        starts_new = re.match(r"([-*+]|\d+[.)]|#+|>)\s", stripped)
        if not stripped or stripped.startswith("|") or starts_new:
            if current:
                units.append(" ".join(current))
            current = []
            if starts_new and not stripped.startswith("#"):
                current = [stripped[starts_new.end():]]
            continue
        current.append(stripped)
    if current:
        units.append(" ".join(current))
    return [(f"paragraph {i + 1}", u) for i, u in enumerate(units)]


def units_from_html(text):
    text = re.sub(r"<(script|style|pre|code)\b.*?</\1>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<(p|li|h[1-6]|div|br|td|th|figcaption|button|label|section|text)\b[^>]*>", "\n\n", text, flags=re.IGNORECASE)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    blocks = [re.sub(r"\s+", " ", b).strip() for b in re.split(r"\n\s*\n", text)]
    return [(f"block {i + 1}", b) for i, b in enumerate(b for b in blocks if b)]


def units_from_script(text):
    return [(f"scene {s['id']}", s["say"]) for s in json.loads(text)]


def check(label, unit, max_words):
    flags = []
    sentences = [s for s in SENTENCE_END.split(unit) if s.strip()]
    if len(sentences) > MAX_SENTENCES:
        flags.append(f"{label}: {len(sentences)} sentences in one paragraph, {MAX_SENTENCES} at most")
    for sentence in sentences:
        found = []
        count = len(WORD.findall(sentence))
        if count > max_words:
            found.append(f"{count} words, {max_words} at most")
        if DASH.search(sentence):
            found.append("dash: split into two sentences")
        lower = sentence.lower()
        for phrase, plain in WORDY.items():
            if re.search(rf"\b{re.escape(phrase)}\b", lower):
                found.append(f'"{phrase}": {plain}')
        for stem, particle, plain in PHRASAL:
            match = re.search(rf"\b{stem}\w*\s+{particle}\b", lower)
            if match:
                found.append(f'"{match.group(0)}": {plain}')
        passive = PASSIVE.search(sentence)
        if passive:
            found.append(f'maybe passive "{passive.group(0)}": name who does it')
        if found:
            flags.append(f"{label}: {'; '.join(found)}\n    {sentence.strip()}")
    return flags, len(sentences)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="a .md, .txt, .html or script.json file, or - for stdin")
    parser.add_argument("--max-words", type=int, default=25, help="longest sentence allowed (default 25)")
    args = parser.parse_args()

    text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text()
    suffix = Path(args.file).suffix.lower()
    if suffix == ".json":
        units = units_from_script(text)
    elif suffix in (".html", ".htm"):
        units = units_from_html(text)
    else:
        units = units_from_markdown(text)

    flags, total = [], 0
    for label, unit in units:
        found, count = check(label, unit, args.max_words)
        flags += found
        total += count
    for flag in flags:
        print(flag)
    print(f"\n{total} sentences checked, {len(flags)} flagged" if flags else f"clean: {total} sentences checked")
    sys.exit(1 if flags else 0)


if __name__ == "__main__":
    main()
