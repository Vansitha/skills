# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-api-python-client==2.202.0",
#     "google-auth-oauthlib==1.5.0",
#     "google-auth-httplib2==0.4.4",
# ]
# ///
"""Upload OpenShorts clips straight to YouTube (no Upload-Post).

clips.py runs this for you; by hand it is:
    uv run upload.py auth
    uv run upload.py jobs
    uv run upload.py upload JOB_ID [--top 3] [--schedule next]

Uploads go through the YouTube Data API with your own OAuth client, so they
cost nothing. Every upload is recorded in uploaded.json so a clip is never
posted twice. The sign-in files live in ~/.config/clips/youtube/ (override
with CLIPS_HOME), never next to this script: see references/google-setup.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLIPS_HOME = Path(os.environ.get("CLIPS_HOME", Path.home() / ".config" / "clips"))
DATA = CLIPS_HOME / "youtube"
CLIENT_SECRET = DATA / "client_secret.json"
TOKEN = DATA / "token.json"
LEDGER = DATA / "uploaded.json"
# Shared with clips.py: openshorts_dir, api_url, and an optional "youtube"
# section that overrides DEFAULT_CONFIG below (tags, footer, ...).
CONFIG = CLIPS_HOME / "config.json"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    # Only used to show which channel you signed in to.
    "https://www.googleapis.com/auth/youtube.readonly",
]

DEFAULT_CONFIG = {
    "api_url": "http://localhost:8000",
    "output_dir": None,  # <openshorts_dir>/output
    "category_id": "20",  # Gaming
    "tags": ["GTA 6", "GTA VI", "Grand Theft Auto 6", "GTA 6 clips", "Shorts"],
    "title_suffix": "",
    "use_ai_description": True,
    "description_footer": "",
    "default_privacy": "private",
    "schedule_every_hours": 24,
    "notify_subscribers": True,
}

TITLE_MAX = 100
DESCRIPTION_MAX = 5000
TAGS_MAX_CHARS = 500
FINISHED = {"completed", "failed", "error", "cancelled"}


# --------------------------------------------------------------------------- #
# Config and ledger
# --------------------------------------------------------------------------- #
def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    clips = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
    config["api_url"] = clips.get("api_url") or config["api_url"]
    config.update(clips.get("youtube") or {})
    if not config.get("output_dir"):
        if not clips.get("openshorts_dir"):
            sys.exit("Not set up yet: run /clips setup first.")
        config["output_dir"] = str(Path(clips["openshorts_dir"]).expanduser() / "output")
    return config


def load_ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text())
    return {}


def save_ledger(ledger: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    tmp = LEDGER.with_suffix(".tmp")
    tmp.write_text(json.dumps(ledger, indent=2, sort_keys=True))
    tmp.replace(LEDGER)


def ledger_key(job_id: str, index: int) -> str:
    return f"{job_id}:{index}"


# --------------------------------------------------------------------------- #
# OpenShorts side
# --------------------------------------------------------------------------- #
def fetch_job(api_url: str, job_id: str) -> dict:
    url = f"{api_url.rstrip('/')}/api/status/{job_id}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit(f"Job {job_id} not found. Run the 'jobs' command to see the ones on disk.")
        raise
    except urllib.error.URLError as e:
        sys.exit(f"Can't reach OpenShorts at {api_url} ({e.reason}). Is Docker running "
                 "and OpenShorts up? Run: /clips up")


def clip_file(output_dir: Path, job_id: str, clip: dict) -> Path:
    name = Path(str(clip.get("video_url", ""))).name
    if not name:
        raise ValueError("clip has no video_url")
    path = output_dir / job_id / name
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing (OpenShorts deletes job files after 24 h)")
    return path


def clean_text(text: str) -> str:
    """YouTube rejects < and > in titles and descriptions."""
    return re.sub(r"[<>]", "", text or "").strip()


def build_title(clip: dict, config: dict) -> str:
    title = (clip.get("video_title_for_youtube_short") or clip.get("title")
             or clip.get("viral_hook_text") or "GTA 6 clip")
    title = re.sub(r"\s+", " ", clean_text(title))
    suffix = config.get("title_suffix") or ""
    room = TITLE_MAX - len(suffix)
    if len(title) > room:
        title = title[: room - 1].rstrip() + "…"
    return title + suffix


def build_description(clip: dict, config: dict, override: str | None) -> str:
    parts = []
    if override is not None:
        parts.append(override)
    elif config.get("use_ai_description", True):
        parts.append(clip.get("video_description_for_instagram")
                     or clip.get("video_description_for_tiktok") or "")
    if config.get("description_footer"):
        parts.append(config["description_footer"])
    text = clean_text("\n\n".join(p for p in parts if p))
    return text[:DESCRIPTION_MAX]


def build_tags(config: dict) -> list[str]:
    tags, total = [], 0
    for tag in config.get("tags") or []:
        tag = clean_text(tag)
        cost = len(tag) + (2 if " " in tag else 0)  # quoted multi-word tags count their quotes
        if not tag or total + cost > TAGS_MAX_CHARS:
            continue
        tags.append(tag)
        total += cost + 1
    return tags


# --------------------------------------------------------------------------- #
# Scheduling
# --------------------------------------------------------------------------- #
def parse_when(value: str) -> datetime:
    """'2026-11-20 18:00' (local time) or a full ISO time with an offset."""
    when = datetime.fromisoformat(value.strip().replace(" ", "T"))
    if when.tzinfo is None:
        when = when.astimezone()  # treat as this Mac's local time
    return when


def first_slot(schedule: str, ledger: dict, every: timedelta) -> datetime:
    now = datetime.now().astimezone()
    if schedule == "next":
        future = [datetime.fromisoformat(v["publish_at"]) for v in ledger.values()
                  if v.get("publish_at")]
        future = [t for t in future if t > now]
        if future:
            return max(future) + every
        # The top of the hour that is at least 30 minutes away.
        return (now + timedelta(minutes=90)).replace(minute=0, second=0, microsecond=0)
    when = parse_when(schedule)
    if when <= now + timedelta(minutes=15):
        sys.exit(f"--schedule {schedule} is in the past or too soon; YouTube needs a future time.")
    return when


def to_rfc3339_utc(when: datetime) -> str:
    return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


# --------------------------------------------------------------------------- #
# YouTube side
# --------------------------------------------------------------------------- #
def credentials(interactive: bool):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    creds = None
    if TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN.write_text(creds.to_json())
            return creds
        except Exception as e:  # noqa: BLE001 - expired/revoked token
            if not interactive:
                sys.exit(f"Your YouTube sign-in expired ({e}). Run: /clips auth")
    if not interactive:
        sys.exit("Not signed in to YouTube yet. Run: /clips auth")
    if not CLIENT_SECRET.exists():
        sys.exit(f"Missing {CLIENT_SECRET}. Make the Google sign-in client first: "
                 "run /clips setup, it walks you through it.")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", open_browser=True)
    DATA.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(creds.to_json())
    os.chmod(TOKEN, 0o600)
    return creds


def youtube_client(interactive: bool = False):
    from googleapiclient.discovery import build

    return build("youtube", "v3", credentials=credentials(interactive), cache_discovery=False)


def upload_one(youtube, path: Path, body: dict, notify: bool) -> dict:
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    media = MediaFileUpload(str(path), mimetype="video/mp4", chunksize=8 * 1024 * 1024,
                            resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media,
                                      notifySubscribers=notify)
    response = None
    while response is None:
        try:
            # num_retries makes the client back off and retry 5xx and dropped connections.
            status, response = request.next_chunk(num_retries=5)
        except HttpError as e:
            reason = ""
            try:
                reason = json.loads(e.content)["error"]["errors"][0]["reason"]
            except Exception:  # noqa: BLE001
                pass
            if reason in ("quotaExceeded", "uploadLimitExceeded", "rateLimitExceeded"):
                raise QuotaHit(reason) from e
            raise
        if status:
            print(f"    {int(status.progress() * 100)}%", end="\r", flush=True)
    return response


class QuotaHit(Exception):
    pass


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_auth(_args, _config) -> None:
    # Always a fresh sign-in, so running auth again can switch account or channel.
    TOKEN.unlink(missing_ok=True)
    youtube = youtube_client(interactive=True)
    resp = youtube.channels().list(part="snippet", mine=True).execute()
    items = resp.get("items") or []
    if not items:
        TOKEN.unlink(missing_ok=True)  # a sign-in with no channel can't upload anything
        print("Signed in, but the account you picked has no YouTube channel.\n"
              "Create the channel first (youtube.com, signed in as that account: profile "
              "picture > Create a channel), then run auth again. If the channel is a brand "
              "channel, pick it on Google's account chooser instead of the plain account.")
        sys.exit(1)
    print(f"Signed in. Clips will upload to: {items[0]['snippet']['title']}")
    print(f"Token saved to {TOKEN} (keep it private).")


JOB_DIR = re.compile(r"^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$")


def cmd_jobs(_args, config) -> None:
    out = Path(config["output_dir"])
    if not out.exists():
        sys.exit(f"No output folder at {out}")
    try:
        urllib.request.urlopen(f"{config['api_url'].rstrip('/')}/health", timeout=10)
    except urllib.error.URLError as e:
        sys.exit(f"Can't reach OpenShorts at {config['api_url']} ({e.reason}). Is Docker running "
                 "and OpenShorts up? Run: /clips up")
    ledger = load_ledger()
    dirs = sorted((d for d in out.iterdir() if d.is_dir() and JOB_DIR.match(d.name)),
                  key=lambda d: d.stat().st_mtime, reverse=True)
    if not dirs:
        print("No jobs yet. Clip something in the dashboard or the API first.")
        return
    for d in dirs[:20]:
        try:
            job = fetch_job(config["api_url"], d.name)
        except SystemExit:
            continue
        clips = ((job.get("result") or {}).get("clips")) or []
        done = sum(1 for i in range(len(clips)) if ledger_key(d.name, i) in ledger)
        when = datetime.fromtimestamp(d.stat().st_mtime).strftime("%b %d %H:%M")
        print(f"{d.name}  {when}  {job.get('status'):<10} {len(clips)} clips, {done} uploaded")


def cmd_upload(args, config) -> None:
    job = fetch_job(config["api_url"], args.job_id)
    if job.get("status") != "completed":
        sys.exit(f"Job {args.job_id} is '{job.get('status')}', not completed yet.")
    clips = ((job.get("result") or {}).get("clips")) or []
    if not clips:
        sys.exit("That job finished without clips.")

    if args.clips:
        indexes = [int(x) for x in args.clips.split(",") if x.strip() != ""]
    else:
        indexes = list(range(len(clips)))[: args.top or len(clips)]
    bad = [i for i in indexes if i < 0 or i >= len(clips)]
    if bad:
        sys.exit(f"Clip index {bad} out of range; this job has clips 0-{len(clips) - 1}.")

    ledger = load_ledger()
    every = timedelta(hours=args.every if args.every is not None else config["schedule_every_hours"])
    privacy = args.privacy or config["default_privacy"]
    slot = first_slot(args.schedule, ledger, every) if args.schedule else None
    if slot:
        privacy = "private"  # YouTube only schedules private videos; it flips them public.
    notify = config["notify_subscribers"] and not args.no_notify
    output_dir = Path(config["output_dir"])

    plan = []
    for i in indexes:
        key = ledger_key(args.job_id, i)
        if key in ledger and not args.force:
            print(f"[{i}] already uploaded: {ledger[key]['url']} (use --force to post again)")
            continue
        clip = clips[i]
        path = clip_file(output_dir, args.job_id, clip)
        status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False,
                  "containsSyntheticMedia": False}
        if slot:
            status["publishAt"] = to_rfc3339_utc(slot)
        body = {
            "snippet": {
                "title": build_title(clip, config),
                "description": build_description(clip, config, args.description),
                "tags": build_tags(config),
                "categoryId": str(config["category_id"]),
            },
            "status": status,
        }
        plan.append((i, key, path, body, slot))
        if slot:
            slot = slot + every

    if not plan:
        print("Nothing to upload.")
        return

    for i, _key, path, body, when in plan:
        size_mb = path.stat().st_size / 1_048_576
        sched = f"goes public {when.strftime('%a %b %d %H:%M %Z')}" if when else body["status"]["privacyStatus"]
        print(f"[{i}] {body['snippet']['title']!r}  ({size_mb:.1f} MB, {sched})")
        if args.dry_run:
            desc = body["snippet"]["description"].replace("\n", " ")
            print(f"     description: {desc[:140]}{'…' if len(desc) > 140 else ''}")
    if args.dry_run:
        print("Dry run: nothing uploaded.")
        return

    youtube = youtube_client(interactive=False)
    for i, key, path, body, when in plan:
        print(f"[{i}] uploading {path.name} …")
        try:
            video = upload_one(youtube, path, body, notify)
        except QuotaHit as e:
            print(f"\nYouTube upload limit reached ({e}). Stopped; try the rest tomorrow.")
            break
        url = f"https://youtube.com/shorts/{video['id']}"
        ledger[key] = {
            "video_id": video["id"],
            "url": url,
            "title": body["snippet"]["title"],
            "privacy": body["status"]["privacyStatus"],
            "publish_at": when.isoformat() if when else None,
            "uploaded_at": datetime.now().astimezone().isoformat(),
            "file": path.name,
        }
        save_ledger(ledger)
        print(f"[{i}] done: {url}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Upload OpenShorts clips to YouTube.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("auth", help="sign in to YouTube once (opens your browser)")
    sub.add_parser("jobs", help="list recent OpenShorts jobs and what's been uploaded")

    up = sub.add_parser("upload", help="upload a job's clips")
    up.add_argument("job_id")
    up.add_argument("--clips", help="comma list of clip indexes, e.g. 0,2 (default: all)")
    up.add_argument("--top", type=int, help="only the best N clips (OpenShorts ranks them)")
    up.add_argument("--privacy", choices=["private", "unlisted", "public"],
                    help="when not scheduling (default from config: private)")
    up.add_argument("--schedule", help="'next' to continue after your last scheduled clip, "
                    "or a start time like '2026-11-20 18:00' (local)")
    up.add_argument("--every", type=float, help="hours between scheduled clips (default 24)")
    up.add_argument("--description", help="use this description instead of the AI one")
    up.add_argument("--no-notify", action="store_true", help="don't notify subscribers")
    up.add_argument("--force", action="store_true", help="upload even if already uploaded")
    up.add_argument("--dry-run", action="store_true", help="show what would upload, upload nothing")

    args = parser.parse_args(argv)
    config = load_config()
    {"auth": cmd_auth, "jobs": cmd_jobs, "upload": cmd_upload}[args.command](args, config)


if __name__ == "__main__":
    main()
