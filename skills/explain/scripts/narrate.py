#!/usr/bin/env python3
"""Voice each scene of an explainer script into its own audio file.

  python3 narrate.py script.json                                  # macOS say: free, offline
  python3 narrate.py script.json --voice "Ava (Premium)" --rate 170
  python3 narrate.py script.json --engine elevenlabs              # billed per character

script.json is a list of scenes: [{"id": "01-hook", "say": "Words to speak."}, ...]
Writes audio/<id>.wav (say) or audio/<id>.mp3 (elevenlabs) next to script.json, and
audio/durations.json: {"01-hook": {"file": "01-hook.wav", "seconds": 4.82, "key": "..."}}.
A scene is voiced again only when its words, engine or voice changed, so a rerun
after a small edit costs only the changed scenes.

ElevenLabs reads its key from ELEVENLABS_API_KEY.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
ELEVENLABS_VOICE = "JBFqnCBsd6RMkjVDRZzb"  # "George", the voice in the ElevenLabs docs examples
ELEVENLABS_MODEL = "eleven_multilingual_v2"


def voice_say(text, out, args):
    command = ["say", "-o", str(out), "--file-format=WAVE", "--data-format=LEI16@24000"]
    if args.voice:
        command += ["-v", args.voice]
    if args.rate:
        command += ["-r", str(args.rate)]
    # the words go in on stdin, so text that starts with "-" is never read as a flag
    subprocess.run(command, input=text, text=True, check=True)


def voice_elevenlabs(text, out, args):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is not set")
    request = urllib.request.Request(
        ELEVENLABS_URL.format(voice=args.voice_id),
        data=json.dumps({"text": text, "model_id": args.model}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            out.write_bytes(response.read())
    except urllib.error.HTTPError as error:
        sys.exit(f"ElevenLabs answered {error.code}: {error.read().decode(errors='replace')}")


ENGINES = {"say": (voice_say, "wav"), "elevenlabs": (voice_elevenlabs, "mp3")}


def seconds(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return round(float(result.stdout.strip()), 2)


def load_scenes(path):
    scenes = json.loads(path.read_text())
    seen = set()
    for scene in scenes:
        scene_id = scene.get("id", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]+", scene_id):
            sys.exit(f"scene id {scene_id!r}: use only letters, digits, - and _")
        if scene_id in seen:
            sys.exit(f"scene id {scene_id!r} appears twice")
        if not scene.get("say", "").strip():
            sys.exit(f"scene {scene_id} has nothing to say")
        seen.add(scene_id)
    return scenes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script", help="path to script.json")
    parser.add_argument("--engine", choices=sorted(ENGINES), default="say")
    parser.add_argument("--voice", help="say: a voice name from `say -v '?'`")
    parser.add_argument("--rate", type=int, help="say: words per minute")
    parser.add_argument("--voice-id", default=ELEVENLABS_VOICE, help="elevenlabs: voice id")
    parser.add_argument("--model", default=ELEVENLABS_MODEL, help="elevenlabs: model id")
    args = parser.parse_args()

    needed = ["ffprobe"] + (["say"] if args.engine == "say" else [])
    missing = [tool for tool in needed if not shutil.which(tool)]
    if missing:
        sys.exit(f"missing: {', '.join(missing)}")

    script = Path(args.script)
    scenes = load_scenes(script)
    audio = script.parent / "audio"
    audio.mkdir(exist_ok=True)
    index_path = audio / "durations.json"
    old_index = json.loads(index_path.read_text()) if index_path.exists() else {}

    speak, extension = ENGINES[args.engine]
    voice = f"{args.voice}@{args.rate}" if args.engine == "say" else f"{args.voice_id}@{args.model}"
    index = {}
    for scene in scenes:
        scene_id, text = scene["id"], scene["say"].strip()
        key = hashlib.sha256(f"{args.engine}|{voice}|{text}".encode()).hexdigest()[:16]
        old = old_index.get(scene_id)
        if old and old["key"] == key and (audio / old["file"]).exists():
            index[scene_id] = old
            print(f"  {scene_id}: unchanged, {old['seconds']}s")
            continue
        out = audio / f"{scene_id}.{extension}"
        speak(text, out, args)
        index[scene_id] = {"file": out.name, "seconds": seconds(out), "key": key}
        print(f"  {scene_id}: {index[scene_id]['seconds']}s")

    index_path.write_text(json.dumps(index, indent=2) + "\n")
    total = sum(clip["seconds"] for clip in index.values())
    print(f"{len(index)} scenes, {total:.1f}s of narration, index in {index_path}")


if __name__ == "__main__":
    main()
