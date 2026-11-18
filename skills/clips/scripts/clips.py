#!/usr/bin/env python3
"""Run a local OpenShorts clipping pipeline from one command.

    clips.py setup [--openshorts DIR] [--library DIR]
                                    install checklist: does what it can, prints the next step
    clips.py key                    paste the Gemini key into OpenShorts' .env (run in a terminal)
    clips.py build                  build OpenShorts' Docker images (slow the first time)
    clips.py up [URL] [--again]     start Docker + OpenShorts, clip URL, auto-upload
    clips.py stats                  clips made, uploaded, pending, where each one is
    clips.py down [--force]         stop the worker, OpenShorts and Docker Desktop
    clips.py auth                   sign in to YouTube (run in a terminal)
    clips.py worker                 internal: follows jobs, saves clips, uploads them

Standard library only, Python 3.9+. Settings and state live in ~/.config/clips/
(override with CLIPS_HOME), never in this repository. Uploading is done by
upload.py next to this script, run with `uv`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

HOME = Path(os.environ.get("CLIPS_HOME", Path.home() / ".config" / "clips"))
CONFIG = HOME / "config.json"
STATE = HOME / "state.json"
PIDFILE = HOME / "worker.pid"
WORKER_LOG = HOME / "worker.log"
YT = HOME / "youtube"  # upload.py's sign-in files and upload log
CLIENT_SECRET = YT / "client_secret.json"
TOKEN = YT / "token.json"
UPLOADER = Path(__file__).resolve().parent / "upload.py"

OPENSHORTS_GIT = "https://github.com/mutonby/openshorts.git"
# The OpenShorts version this skill was tested with. Newer ones may change the
# API calls below, so move this forward only after a test clip on the new one.
OPENSHORTS_COMMIT = "8af4a48a2bdda96c9a02bb8df3f09d4e7ec99e0f"
DEFAULT_ROOT = Path.home() / "clips"
DOWNLOADS = Path(os.environ.get("CLIPS_DOWNLOADS", Path.home() / "Downloads"))
# What a Mac needs in OpenShorts' .env, with the comment written above each.
ENV_SETTINGS = [
    ("GEMINI_API_KEY", "", "Google Gemini key, free from https://aistudio.google.com/app/apikey "
                           "(set it with: clips.py key)"),
    ("MAX_CONCURRENT_JOBS", "1", "One job at a time keeps memory inside Docker Desktop's limit"),
    ("FFMPEG_ENCODER", "x264", "Macs have no NVIDIA GPU: encode and transcribe on the CPU"),
    ("WHISPER_DEVICE", "cpu", None),
    ("WHISPER_COMPUTE", "int8", None),
    ("JOB_RETENTION_SECONDS", "691200", "Keep finished jobs 8 days (past YouTube's 7-day sign-in), "
                                        "downloaded sources 1 day"),
    ("SOURCE_RETENTION_SECONDS", "86400", None),
]

DEFAULTS = {
    "openshorts_dir": None,
    "library_dir": None,
    "api_url": "http://localhost:8000",
    "upload_mode": "schedule",  # schedule | private | none
    "first_delay_hours": 3,
    "every_hours": 4,
    "target_clips": 10,  # OpenShorts accepts 1-15 per job
    "clip_min_seconds": 45,  # OpenShorts accepts 5-175; its own default is 15
    "clip_max_seconds": 90,  # 10-180, at least 5 above the minimum; its default is 60
}
VIDEO_HOSTS = ("twitch.tv", "youtube.com", "youtu.be", "kick.com")
POLL_SECONDS = 30
UPLOAD_RETRY_SECONDS = 1800
ACTIVE = ("processing", "clipped")


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def now() -> datetime:
    return datetime.now().astimezone()


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(value) if value else None


def short_time(value: Optional[str]) -> str:
    dt = parse_dt(value)
    return dt.astimezone().strftime("%a %b %d %H:%M") if dt else "-"


def ago(value: Optional[str]) -> str:
    dt = parse_dt(value)
    if not dt:
        return "-"
    mins = int((now() - dt).total_seconds() // 60)
    return f"{mins} min" if mins < 90 else f"{mins // 60} h {mins % 60} min"


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    tmp.replace(path)


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    cfg.update(read_json(CONFIG, {}))
    if not cfg.get("openshorts_dir"):
        sys.exit("Not set up yet. Run: /clips setup")
    cfg["openshorts_dir"] = str(Path(cfg["openshorts_dir"]).expanduser())
    lib = cfg.get("library_dir") or str(Path(cfg["openshorts_dir"]).parent / "library")
    cfg["library_dir"] = str(Path(lib).expanduser())
    return cfg


def load_state() -> dict:
    return read_json(STATE, {"jobs": []})


def save_state(state: dict) -> None:
    write_json(STATE, state)


def ledger(_cfg: dict) -> dict:
    return read_json(YT / "uploaded.json", {})


def slug(text: str, limit: int = 60) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", text or "clip").strip("-").lower()
    return (text[:limit].rstrip("-")) or "clip"


# --------------------------------------------------------------------------- #
# Docker and the OpenShorts API
# --------------------------------------------------------------------------- #
def find_bin(name: str, *places: Path) -> Optional[str]:
    found = shutil.which(name)
    if found:
        return found
    return next((str(p) for p in places if p.exists()), None)


def docker_path() -> Optional[str]:
    return find_bin("docker", Path.home() / ".docker/bin/docker", Path("/usr/local/bin/docker"),
                    Path("/Applications/Docker.app/Contents/Resources/bin/docker"))


def uv_path() -> Optional[str]:
    return find_bin("uv", Path("/opt/homebrew/bin/uv"), Path("/usr/local/bin/uv"),
                    Path.home() / ".local/bin/uv", Path.home() / ".cargo/bin/uv")


def docker_bin() -> str:
    return docker_path() or sys.exit("Docker isn't installed (no `docker` command found). Run: /clips setup")


def uv_bin() -> str:
    return uv_path() or sys.exit("`uv` isn't installed; the YouTube uploader needs it. Run: /clips setup")


def docker_running() -> bool:
    try:
        return subprocess.run([docker_bin(), "info"], capture_output=True, timeout=20).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def compose(cfg: dict, *args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run([docker_bin(), "compose", *args], cwd=cfg["openshorts_dir"],
                          capture_output=True, text=True, timeout=timeout)


def api(cfg: dict, path: str, body: Optional[dict] = None, timeout: int = 30):
    url = cfg["api_url"].rstrip("/") + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def backend_up(cfg: dict) -> bool:
    try:
        urllib.request.urlopen(cfg["api_url"].rstrip("/") + "/health", timeout=5)
        return True
    except (urllib.error.URLError, OSError):
        return False


def start_docker() -> None:
    if docker_running():
        return
    print("Starting Docker Desktop…", flush=True)
    subprocess.run(["open", "-a", "Docker"], check=False)
    for _ in range(60):
        time.sleep(3)
        if docker_running():
            return
    sys.exit("Docker Desktop didn't start within 3 minutes. Open it once by hand "
             "(it may be waiting for you to accept its terms, an update or a prompt).")


def start_stack(cfg: dict) -> None:
    start_docker()
    if not backend_up(cfg):
        print("Starting OpenShorts…", flush=True)
        res = compose(cfg, "up", "-d", "backend", "frontend")
        if res.returncode != 0:
            sys.exit("docker compose failed:\n" + (res.stderr or res.stdout)[-1500:])
        for _ in range(60):
            time.sleep(3)
            if backend_up(cfg):
                break
        else:
            sys.exit("OpenShorts didn't come up within 3 minutes. Check: docker compose logs backend")


# --------------------------------------------------------------------------- #
# Worker process
# --------------------------------------------------------------------------- #
def worker_pid() -> Optional[int]:
    try:
        pid = int(PIDFILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        return None


def ensure_worker() -> None:
    if worker_pid():
        return
    HOME.mkdir(parents=True, exist_ok=True)
    log = open(WORKER_LOG, "a")
    proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "worker"],
                            stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                            start_new_session=True, close_fds=True)
    PIDFILE.write_text(str(proc.pid))


def log(msg: str) -> None:
    print(f"[{now().strftime('%H:%M:%S')}] {msg}", flush=True)


def harvest(cfg: dict, job: dict, result: dict) -> None:
    """Copy a finished job's clips into the library, which OpenShorts never cleans."""
    out = Path(cfg["openshorts_dir"]) / "output" / job["id"]
    folder = Path(cfg["library_dir"]) / f"{parse_dt(job['submitted_at']).strftime('%Y-%m-%d')}_{job['id'][:8]}"
    folder.mkdir(parents=True, exist_ok=True)
    clips = []
    for i, clip in enumerate(result.get("clips") or []):
        title = (clip.get("video_title_for_youtube_short") or clip.get("title") or f"clip {i}").strip()
        src = out / Path(str(clip.get("video_url", ""))).name
        dest = folder / f"{i + 1:02d}_{slug(title)}.mp4"
        if src.is_file() and not dest.exists():
            shutil.copy2(src, dest)
        clips.append({"index": i, "title": title, "file": str(dest) if dest.exists() else None})
    job["clips"] = clips
    job["folder"] = str(folder)


def next_slot(cfg: dict) -> datetime:
    """The first publish time: after the delay, and after the last clip already queued."""
    earliest = now() + timedelta(hours=float(cfg["first_delay_hours"]))
    slots = [parse_dt(v.get("publish_at")) for v in ledger(cfg).values() if v.get("publish_at")]
    future = [s for s in slots if s and s > now()]
    if future:
        earliest = max(earliest, max(future) + timedelta(hours=float(cfg["every_hours"])))
    return earliest.replace(second=0, microsecond=0)


def upload(cfg: dict, job: dict) -> None:
    done = ledger(cfg)
    todo = [c["index"] for c in job["clips"] if f"{job['id']}:{c['index']}" not in done]
    if not todo:
        job["status"] = "done"
        job.pop("blocked", None)
        return
    cmd = [uv_bin(), "run", str(UPLOADER), "upload", job["id"], "--clips", ",".join(map(str, todo))]
    if cfg["upload_mode"] == "schedule":
        cmd += ["--schedule", iso(next_slot(cfg)), "--every", str(cfg["every_hours"])]
    else:
        cmd += ["--privacy", "private"]
    log(f"uploading {len(todo)} clip(s) of {job['id'][:8]}")
    res = subprocess.run(cmd, cwd=cfg["openshorts_dir"], capture_output=True, text=True, timeout=3600)
    output = (res.stdout + res.stderr).strip()
    left = [i for i in todo if f"{job['id']}:{i}" not in ledger(cfg)]
    if not left:
        job["status"] = "done"
        job.pop("blocked", None)
        log(f"uploaded all clips of {job['id'][:8]}")
        return
    wait = UPLOAD_RETRY_SECONDS
    if "sign-in expired" in output or "Not signed in" in output:
        reason = "YouTube sign-in expired: run /clips auth"
    elif "limit reached" in output:
        # A daily cap: retrying every half hour only adds failed attempts.
        wait = 3 * 3600
        detail = re.search(r"limit reached \((\w+)\)", output)
        reason = (f"YouTube's upload limit reached ({detail.group(1) if detail else 'daily cap'}): "
                  f"retrying at {(now() + timedelta(seconds=wait)).strftime('%H:%M')}")
    else:
        reason = "upload failed: " + (output.splitlines()[-1] if output else f"exit {res.returncode}")
    job["blocked"] = reason
    job["retry_at"] = iso(now() + timedelta(seconds=wait))
    log(f"{job['id'][:8]}: {reason}")


def cmd_worker(_args) -> None:
    cfg = load_config()
    PIDFILE.write_text(str(os.getpid()))
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    log("worker started")
    try:
        while True:
            state = load_state()
            active = [j for j in state["jobs"] if j["status"] in ACTIVE]
            if not active:
                log("nothing left to do, worker stopping")
                return
            for job in active:
                try:
                    if job["status"] == "processing":
                        st = api(cfg, f"/api/status/{job['id']}")
                        status = st.get("status")
                        logs = st.get("logs") or []
                        job["progress"] = str(logs[-1])[:160] if logs else None
                        if status == "completed":
                            harvest(cfg, job, st.get("result") or {})
                            job["status"] = "clipped"
                            job["finished_at"] = iso(now())
                            log(f"{job['id'][:8]} finished with {len(job['clips'])} clips")
                        elif status in ("failed", "error", "cancelled"):
                            job["status"] = "failed"
                            job["error"] = job.get("progress") or status
                            log(f"{job['id'][:8]} failed: {job['error']}")
                    if job["status"] == "clipped":
                        if cfg["upload_mode"] == "none":
                            job["blocked"] = "uploads are off (upload_mode: none)"
                            job["status"] = "done"
                        elif not job.get("retry_at") or parse_dt(job["retry_at"]) <= now():
                            upload(cfg, job)
                except (urllib.error.URLError, OSError, subprocess.TimeoutExpired) as e:
                    job["progress"] = f"waiting for OpenShorts ({e.__class__.__name__})"
            # Merge into a fresh read so a concurrent `up` isn't overwritten.
            fresh = load_state()
            by_id = {j["id"]: j for j in active}
            fresh["jobs"] = [by_id.get(j["id"], j) for j in fresh["jobs"]]
            fresh["worker_seen"] = iso(now())
            save_state(fresh)
            time.sleep(POLL_SECONDS)
    finally:
        if worker_pid() == os.getpid():
            PIDFILE.unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def get_openshorts(dest: Path) -> None:
    """Download OpenShorts at the tested commit: that one commit, no history."""
    git = shutil.which("git")
    if not git:
        sys.exit("git isn't installed. Run `xcode-select --install`, finish Apple's installer, "
                 "then run setup again.")
    print(f"Downloading OpenShorts to {dest} …", flush=True)
    partial = dest.with_name(dest.name + ".partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    for args in (["init", "-q"], ["remote", "add", "origin", OPENSHORTS_GIT],
                 ["fetch", "-q", "--depth", "1", "origin", OPENSHORTS_COMMIT],
                 ["checkout", "-q", "-B", "clips", "FETCH_HEAD"]):
        res = subprocess.run([git, *args], cwd=partial, capture_output=True, text=True)
        if res.returncode != 0:
            sys.exit(f"Downloading OpenShorts failed (git {args[0]}): {res.stderr.strip()[-500:]}")
    if dest.exists():
        dest.rmdir()  # only ever an empty folder here
    partial.rename(dest)


def env_value(env: Path, key: str) -> str:
    try:
        found = re.findall(rf"^{key}=(.*)$", env.read_text(), re.M)
    except OSError:
        return ""
    return found[-1].strip().strip("\"'") if found else ""


def set_env(env: Path, key: str, value: str) -> None:
    text = env.read_text() if env.exists() else ""
    line = f"{key}={value}"
    if re.search(rf"^{key}=", text, re.M):
        text = re.sub(rf"^{key}=.*$", lambda _m: line, text, flags=re.M)
    else:
        text += ("\n" if text and not text.endswith("\n") else "") + line + "\n"
    env.write_text(text)
    env.chmod(0o600)


def write_env(os_dir: Path) -> list:
    """Make OpenShorts' .env from its template once, then add any ENV_SETTINGS it lacks."""
    env = os_dir / ".env"
    if not env.exists():
        example = os_dir / ".env.example"
        text = example.read_text() if example.exists() else ""
        # The template's placeholder AWS keys would make OpenShorts try to back clips up to S3.
        env.write_text(re.sub(r"^(AWS_\w+=)", r"# \1", text, flags=re.M))
    env.chmod(0o600)
    text = env.read_text()
    missing = [s for s in ENV_SETTINGS if not re.search(rf"^{s[0]}=", text, re.M)]
    if missing:
        lines = ["", "# Added by the clips skill"]
        for key, value, why in missing:
            lines += ([f"# {why}"] if why else []) + [f"{key}={value}"]
        with env.open("a") as f:
            f.write(("\n" if text and not text.endswith("\n") else "") + "\n".join(lines) + "\n")
    return [s[0] for s in missing]


def adopt_client_secret() -> Optional[str]:
    """Move the newest Google client file from Downloads into place; returns what happened."""
    if CLIENT_SECRET.exists():
        return None
    try:
        found = sorted(DOWNLOADS.glob("client_secret*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None
    for path in found:
        data = read_json(path, {})
        if "installed" in data:
            YT.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(CLIENT_SECRET))
            CLIENT_SECRET.chmod(0o600)
            return f"Moved the Google client file from Downloads to {CLIENT_SECRET}"
        if "web" in data:
            return (f"{path.name} in Downloads is a 'Web application' client. Make another client "
                    "with application type 'Desktop app'.")
    return None


def images_built(os_dir: Path) -> bool:
    project = re.sub(r"[^a-z0-9_-]", "", os_dir.name.lower())  # how Compose names the images
    res = subprocess.run([docker_bin(), "image", "inspect", f"{project}-backend", f"{project}-frontend"],
                         capture_output=True)
    return res.returncode == 0


def cmd_setup(args) -> None:
    cfg = dict(DEFAULTS)
    cfg.update(read_json(CONFIG, {}))
    if args.openshorts:
        os_dir = Path(args.openshorts).expanduser().resolve()
    elif cfg.get("openshorts_dir"):
        os_dir = Path(cfg["openshorts_dir"]).expanduser()
    else:
        os_dir = DEFAULT_ROOT / "openshorts"
    if sys.platform != "darwin":
        print("Note: this is made for macOS. Elsewhere, start Docker yourself before `up`.")

    # What needs nobody: download OpenShorts, write its .env, save the settings.
    done = []
    if not (os_dir / "docker-compose.yml").exists():
        if os_dir.exists() and any(os_dir.iterdir()):
            sys.exit(f"{os_dir} exists and isn't OpenShorts. Run setup with "
                     "--openshorts <a new folder> instead.")
        get_openshorts(os_dir)
        done.append(f"Downloaded OpenShorts to {os_dir}")
    added = write_env(os_dir)
    if added:
        done.append(f"Added to OpenShorts' .env: {', '.join(added)}")
        if backend_up(cfg) and docker_path():
            compose(dict(cfg, openshorts_dir=str(os_dir)), "restart", "backend")  # reads .env at start
            done.append("Restarted OpenShorts so it uses them")
    cfg["openshorts_dir"] = str(os_dir)
    library = args.library or cfg.get("library_dir") or os_dir.parent / "library"
    cfg["library_dir"] = str(Path(library).expanduser().resolve())
    write_json(CONFIG, cfg)
    note = adopt_client_secret()
    if note:
        done.append(note)

    has_docker = bool(docker_path())
    if has_docker:
        start_docker()
    me = f"python3 {Path(__file__).resolve()}"
    checks = [
        ("Docker Desktop installed and running", has_docker,
         "Install Docker Desktop: `brew install --cask docker` (asks for the Mac password), or "
         "download it from https://www.docker.com/products/docker-desktop/ . Open it once and "
         "accept its terms."),
        ("OpenShorts built", has_docker and images_built(os_dir),
         f"Build OpenShorts: `{me} build`. It takes 10 to 30 minutes the first time; carry on "
         "with the other steps meanwhile."),
        ("uv installed", bool(uv_path()),
         "Install uv: `brew install uv`, or without Homebrew: "
         "`curl -LsSf https://astral.sh/uv/install.sh | sh`"),
        ("Gemini key saved", bool(env_value(os_dir / ".env", "GEMINI_API_KEY")),
         f"Save a Gemini key: run `{me} key` in a terminal and paste the key there."),
        ("Google sign-in client", CLIENT_SECRET.exists(),
         "Make the Google sign-in client: follow references/google-setup.md, then run setup "
         "again (it picks the file up from Downloads)."),
        ("Signed in to YouTube", TOKEN.exists(),
         f"Sign in to YouTube: run `{me} auth` in a terminal."),
    ]
    for line in done:
        print(line)
    print(f"\nOpenShorts: {os_dir}\nClips folder: {cfg['library_dir']}\nSettings: {CONFIG}\n")
    for title, ok, _ in checks:
        print(f"  [{'x' if ok else ' '}] {title}")
    todo = [how for _, ok, how in checks if not ok]
    if not todo:
        print("\nAll set. Clip a past broadcast with: /clips up <link>")
        return
    print("\nStill to do, in this order:")
    for i, how in enumerate(todo, 1):
        print(f"  {i}. {how}")


def check_gemini_key(key: str) -> Optional[bool]:
    """True if Google accepts the key, False if it rejects it, None if it can't tell."""
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models?pageSize=1",
                                 headers={"x-goog-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=20):
            return True
    except urllib.error.HTTPError as e:
        return False if e.code in (400, 401, 403) else None
    except (urllib.error.URLError, OSError):
        return None


def cmd_key(_args) -> None:
    import getpass

    cfg = load_config()
    print("Make a free key at https://aistudio.google.com/app/apikey (Create API key) and copy it.")
    key = getpass.getpass("Paste it here (it stays hidden), then press Return: ").strip()
    if not key:
        sys.exit("Nothing pasted, nothing saved.")
    verdict = check_gemini_key(key)
    if verdict is False:
        sys.exit("Google says that key doesn't work. Nothing saved: copy it again and rerun this.")
    set_env(Path(cfg["openshorts_dir"]) / ".env", "GEMINI_API_KEY", key)
    print("Saved the key." if verdict else
          "Saved the key. (Couldn't reach Google to test it; the first clip will.)")
    if backend_up(cfg):
        compose(cfg, "restart", "backend")
        print("Restarted OpenShorts so it uses the new key.")


def cmd_build(_args) -> None:
    cfg = load_config()
    start_docker()
    print("Building OpenShorts. The first build takes 10 to 30 minutes…", flush=True)
    res = subprocess.run([docker_bin(), "compose", "build", "backend", "frontend"], cwd=cfg["openshorts_dir"])
    if res.returncode != 0:
        sys.exit("The build failed; the lines above say why.")
    print("Built.")


def to_seconds(text: str) -> float:
    """'1:15:00', '45:00' or '900' -> seconds."""
    parts = [float(p) for p in str(text).strip().split(":")]
    if not parts or len(parts) > 3 or any(p < 0 for p in parts):
        raise ValueError(text)
    secs = 0.0
    for p in parts:
        secs = secs * 60 + p
    return secs


def stretch(args) -> Optional[list]:
    """The [start, end] seconds to clip, or None for the whole video."""
    if args.start is None and args.minutes is None:
        return None
    try:
        start = to_seconds(args.start) if args.start is not None else 0.0
    except ValueError:
        sys.exit(f"--from takes a time like 1:15:00 or 45:00, not {args.start!r}")
    minutes = args.minutes if args.minutes is not None else 30.0
    if minutes < 1:
        sys.exit("--minutes must be at least 1.")
    # OpenShorts reads a stretch that starts at 0 as "the whole video" when it
    # can't tell the length first, so start a moment in.
    start = max(start, 2.0)
    return [start, start + minutes * 60]


MAX_UPLOAD_MB = 2048  # OpenShorts' upload limit (app.MAX_FILE_SIZE_MB)


def hms(secs: float) -> str:
    return time.strftime("%H:%M:%S", time.gmtime(secs))


def container(*args: str, timeout: int = 3600) -> subprocess.CompletedProcess:
    """Run a command in the OpenShorts backend container (it has yt-dlp and ffmpeg).
    Its /app is the OpenShorts checkout, so /app/uploads is <checkout>/uploads."""
    return subprocess.run([docker_bin(), "exec", "openshorts-backend", *args],
                          capture_output=True, text=True, timeout=timeout)


def hls_segments(playlist_url: str, span: list) -> list:
    """The URLs to fetch, in order, for the part of an HLS playlist covering span.

    Twitch serves fragmented-MP4 pieces, which only play after their header
    (#EXT-X-MAP), so the header goes first, and again if it changes mid-stretch.
    """
    with urllib.request.urlopen(playlist_url, timeout=60) as resp:
        text = resp.read().decode(errors="replace")
    t, picked, dur, header, sent_header = 0.0, [], None, None, None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#EXT-X-MAP:"):
            m = re.search(r'URI="([^"]+)"', line)
            header = urllib.parse.urljoin(playlist_url, m.group(1)) if m else None
        elif line.startswith("#EXTINF:"):
            dur = float(line[8:].split(",")[0])
        elif line and not line.startswith("#") and dur is not None:
            if t + dur > span[0] and t < span[1]:
                if header and header != sent_header:
                    picked.append(header)
                    sent_header = header
                picked.append(urllib.parse.urljoin(playlist_url, line))
            t, dur = t + dur, None
    return picked


def fetch_stretch(cfg: dict, url: str, span: list) -> Path:
    """Download only span of url and return a local MP4 of it.

    Self-hosted OpenShorts ignores source_start/source_end (it applies them only
    when metering a cloud plan), so a URL job would download the whole stream.
    A Twitch recording is an HLS playlist of ~10 s pieces: fetch just the pieces
    that cover the stretch, several at a time, and join them. (yt-dlp's
    --download-sections hands this to ffmpeg, which stalls seeking into long
    Twitch playlists.) Anything that isn't HLS falls back to --download-sections.
    """
    from concurrent.futures import ThreadPoolExecutor

    stamp = int(time.time())
    uploads = Path(cfg["openshorts_dir"]) / "uploads"
    uploads.mkdir(exist_ok=True)
    path = uploads / f"clips-stretch-{stamp}.mp4"
    print(f"Downloading {hms(span[0])} to {hms(span[1])} of the stream…", flush=True)
    res = container("python", "-m", "yt_dlp", "--no-warnings", "--no-playlist",
                    "-f", "b[height<=1080]/b", "--print", "%(protocol)s %(url)s", url, timeout=300)
    proto, _, media_url = (res.stdout.strip().splitlines() or [""])[-1].partition(" ")
    if res.returncode != 0 or not media_url:
        sys.exit("Couldn't read that video: " + (res.stderr.strip().splitlines() or ["unknown error"])[-1])

    if "m3u8" in proto:
        segs = hls_segments(media_url, span)
        if not segs:
            sys.exit(f"The stream is shorter than {hms(span[0])}.")
        ts = uploads / f"clips-stretch-{stamp}.joined"

        def get(u):
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(u, timeout=60) as r:
                        return r.read()
                except (urllib.error.URLError, OSError):
                    time.sleep(2 * (attempt + 1))
            raise RuntimeError(f"segment failed: {u}")

        done = 0
        with ts.open("wb") as out, ThreadPoolExecutor(8) as pool:
            for chunk in pool.map(get, segs):  # map keeps playlist order
                out.write(chunk)
                done += 1
                if done % 30 == 0 or done == len(segs):
                    print(f"  {done}/{len(segs)} pieces", flush=True)
        res = container("ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", f"/app/uploads/{ts.name}",
                        "-c", "copy", "-movflags", "+faststart", f"/app/uploads/{path.name}")
        ts.unlink(missing_ok=True)
    else:
        res = container("python", "-m", "yt_dlp", "--no-warnings", "--no-playlist",
                        "--download-sections", f"*{hms(span[0])}-{hms(span[1])}",
                        "-f", "b[height<=1080]/bv*[height<=1080]+ba/b", "--merge-output-format", "mp4",
                        "-o", f"/app/uploads/{path.name}", url, timeout=3 * 3600)
    if res.returncode != 0 or not path.is_file():
        tail = (res.stderr or res.stdout).strip().splitlines()[-3:]
        sys.exit("Couldn't download that stretch:\n" + "\n".join(tail))
    size_mb = path.stat().st_size / 1_048_576
    if size_mb > MAX_UPLOAD_MB:
        path.unlink()
        sys.exit(f"That stretch is {size_mb:.0f} MB, over OpenShorts' {MAX_UPLOAD_MB} MB upload "
                 "limit. Use fewer --minutes.")
    print(f"Downloaded {size_mb:.0f} MB.", flush=True)
    return path


def clip_options(cfg: dict) -> dict:
    """How many clips and how long, as OpenShorts' /api/process fields."""
    opts = {"target_clips": int(cfg["target_clips"])}
    for key in ("clip_min_seconds", "clip_max_seconds"):
        if cfg.get(key):
            opts[key] = int(cfg[key])
    return opts


def submit_file(cfg: dict, path: Path) -> str:
    """Send a local video to OpenShorts as an upload; returns the job id."""
    res = subprocess.run(
        ["curl", "-sS", "-X", "POST", cfg["api_url"].rstrip("/") + "/api/process",
         "-F", f"file=@{path};type=video/mp4", "-F", "acknowledged=true",
         *[a for k, v in clip_options(cfg).items() for a in ("-F", f"{k}={v}")]],
        capture_output=True, text=True, timeout=1800)
    try:
        job_id = json.loads(res.stdout).get("job_id")
    except ValueError:
        job_id = None
    if not job_id:
        sys.exit(f"OpenShorts refused the file: {(res.stdout or res.stderr)[:300]}")
    path.unlink(missing_ok=True)  # OpenShorts keeps its own copy of the upload
    return job_id


def sync_clip_length(cfg: dict) -> None:
    """Mirror the clip length into OpenShorts' .env.

    Each job gets the length with its request, but a job that OpenShorts
    resumes after a restart is re-run without it and falls back to .env
    (15-60 s when unset). Writing it there too keeps resumed jobs at the
    chosen length; OpenShorts reads .env at its next start.
    """
    env = Path(cfg["openshorts_dir"]) / ".env"
    for key in ("clip_min_seconds", "clip_max_seconds"):
        if cfg.get(key) and env_value(env, key.upper()) != str(int(cfg[key])):
            set_env(env, key.upper(), str(int(cfg[key])))


def cmd_up(args) -> None:
    cfg = load_config()
    sync_clip_length(cfg)
    span = stretch(args)
    if args.url:
        parsed = urlparse(args.url.strip())
        host = (parsed.hostname or "").lower()
        if not any(host == h or host.endswith("." + h) for h in VIDEO_HOSTS):
            sys.exit(f"Not a supported video link: {args.url} (Twitch, YouTube or Kick).")
        if host.endswith("twitch.tv") and not re.search(r"/(videos?|v)/\d+|/clip/|clips\.", args.url):
            sys.exit("That's a Twitch channel page, not a recording. Open the channel's Videos tab "
                     "and paste a past broadcast link (twitch.tv/videos/…).")
        state = load_state()
        dupes = [j for j in state["jobs"] if j["url"] == args.url.strip() and j["status"] != "failed"
                 and j.get("range") == span]
        if dupes and not args.again:
            sys.exit(f"Already clipped or clipping this link (job {dupes[-1]['id'][:8]}, "
                     f"{dupes[-1]['status']}). Use --again to clip it again.")
    start_stack(cfg)
    if not args.url:
        print("OpenShorts is running: dashboard http://localhost:5175/#app")
        if any(j["status"] in ACTIVE for j in load_state()["jobs"]):
            ensure_worker()
        return
    if span:
        job_id = submit_file(cfg, fetch_stretch(cfg, args.url.strip(), span))
    else:
        body = {"url": args.url.strip(), "acknowledged": True, "layouts": ["auto"], **clip_options(cfg)}
        try:
            resp = api(cfg, "/api/process", body, timeout=120)
        except urllib.error.HTTPError as e:
            sys.exit(f"OpenShorts refused the link ({e.code}): {e.read().decode(errors='replace')[:300]}")
        job_id = resp.get("job_id")
        if not job_id:
            sys.exit(f"OpenShorts didn't return a job: {resp}")
    state = load_state()
    state["jobs"].append({"id": job_id, "url": args.url.strip(), "submitted_at": iso(now()),
                          "status": "processing", "clips": [], "range": span})
    save_state(state)
    ensure_worker()
    mode = {"schedule": f"auto-scheduled, one every {cfg['every_hours']} h, "
                        f"first about {cfg['first_delay_hours']} h after clipping",
            "private": "uploaded as private for you to review",
            "none": "not uploaded (upload_mode is none)"}[cfg["upload_mode"]]
    print(f"Clipping started: job {job_id[:8]}")
    if span:
        print(f"Only {hms(span[0])} to {hms(span[1])}. Processing takes about "
              f"{(span[1] - span[0]) / 60:.0f} min.")
    else:
        print("Processing takes about as long as the video itself on this Mac.")
    print(f"Clips will be saved to: {cfg['library_dir']}")
    print(f"Then they'll be {mode}.")


def clip_rows(cfg: dict, job: dict, done: dict):
    for c in job.get("clips") or []:
        entry = done.get(f"{job['id']}:{c['index']}")
        if entry:
            when = parse_dt(entry.get("publish_at"))
            if when and when > now():
                status = f"scheduled {short_time(entry['publish_at'])}"
            elif when or entry.get("privacy") == "public":
                status = "live"
            else:
                status = entry.get("privacy", "uploaded")
            link = entry.get("url")
        else:
            status, link = "pending", None
        yield c, status, link


def cmd_stats(_args) -> None:
    cfg = load_config()
    state, done = load_state(), ledger(cfg)
    created = uploaded = live = scheduled = private = pending = 0
    for job in state["jobs"]:
        for c, status, _ in clip_rows(cfg, job, done):
            created += 1
            if status == "pending":
                pending += 1
            else:
                uploaded += 1
                live += status == "live"
                scheduled += status.startswith("scheduled")
                private += status == "private"
    processing = [j for j in state["jobs"] if j["status"] == "processing"]
    failed = [j for j in state["jobs"] if j["status"] == "failed"]

    print(f"Clips created: {created}")
    detail = ", ".join(p for p in (f"{live} live" if live else "", f"{scheduled} scheduled" if scheduled else "",
                                    f"{private} private" if private else "") if p)
    print(f"Uploaded: {uploaded}" + (f" ({detail})" if detail else ""))
    print(f"Pending: {pending}")
    print(f"Processing: {len(processing)} stream(s)")
    if failed:
        print(f"Failed: {len(failed)} stream(s)")
    print()
    up = backend_up(cfg)
    print(f"OpenShorts: {'running' if up else 'stopped'} | worker: {'running' if worker_pid() else 'stopped'}"
          f" | uploads: {cfg['upload_mode']}")
    print(f"Clips folder: {cfg['library_dir']}")
    for job in processing:
        print(f"\n[processing] {job['url']}  (started {ago(job['submitted_at'])} ago, job {job['id'][:8]})")
        if job.get("progress"):
            print(f"  latest: {job['progress']}")
    for job in failed:
        print(f"\n[failed] {job['url']}  (job {job['id'][:8]}): {job.get('error', '')}")
    for job in reversed(state["jobs"]):
        if not job.get("clips"):
            continue
        print(f"\n{job['url']}  (clipped {short_time(job.get('finished_at'))}, job {job['id'][:8]})")
        if job.get("blocked"):
            print(f"  ! {job['blocked']}")
        print(f"  folder: {job.get('folder')}")
        for c, status, link in clip_rows(cfg, job, done):
            print(f"  {c['index'] + 1:>2}. {c['title']}")
            print(f"      {status}" + (f"  {link}" if link else ""))
            f = c.get("file")
            print(f"      file: {f if f and Path(f).exists() else '(missing)'}")
    if not state["jobs"]:
        print("\nNothing clipped yet. Run: /clips up <twitch past-broadcast link>")


def cmd_down(args) -> None:
    cfg = load_config()
    state = load_state()
    processing = [j for j in state["jobs"] if j["status"] == "processing"]
    if processing and not args.force:
        print("Still clipping, stopping now loses that work:")
        for j in processing:
            print(f"  {j['url']} (started {ago(j['submitted_at'])} ago)")
        print("Run `down --force` to stop anyway.")
        sys.exit(2)
    pid = worker_pid()
    if pid:
        os.kill(pid, signal.SIGTERM)
        PIDFILE.unlink(missing_ok=True)
        print("Stopped the worker.")
    for j in processing:
        j["status"] = "failed"
        j["error"] = "stopped by /clips down before it finished; run up with the link again"
    save_state(state)
    if docker_running():
        res = compose(cfg, "stop")
        print("Stopped OpenShorts." if res.returncode == 0 else "docker compose stop failed: " + res.stderr[-500:])
        subprocess.run(["osascript", "-e", 'quit app "Docker"'], capture_output=True)
        print("Quit Docker Desktop.")
    else:
        print("Docker Desktop isn't running.")
    pending = [j for j in state["jobs"] if j["status"] == "clipped"]
    if pending:
        print(f"{len(pending)} stream(s) still have clips waiting to upload; they'll go up at the next `up`.")


def cmd_auth(_args) -> None:
    cfg = load_config()
    res = subprocess.run([uv_bin(), "run", str(UPLOADER), "auth"], cwd=cfg["openshorts_dir"])
    if res.returncode == 0:
        state = load_state()
        for j in state["jobs"]:
            if j["status"] == "clipped":
                j.pop("retry_at", None)
        save_state(state)
        if any(j["status"] == "clipped" for j in state["jobs"]):
            ensure_worker()
            print("Retrying the waiting uploads now.")
    sys.exit(res.returncode)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Local OpenShorts clipping pipeline.")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup")
    s.add_argument("--openshorts", help=f"where OpenShorts lives (default {DEFAULT_ROOT}/openshorts)")
    s.add_argument("--library", help="where clips are saved (default: next to OpenShorts)")
    sub.add_parser("key")
    sub.add_parser("build")
    u = sub.add_parser("up")
    u.add_argument("url", nargs="?")
    u.add_argument("--from", dest="start", help="clip only from this time, e.g. 1:15:00")
    u.add_argument("--minutes", type=float, help="how many minutes from --from (default 30)")
    u.add_argument("--again", action="store_true")
    sub.add_parser("stats")
    d = sub.add_parser("down")
    d.add_argument("--force", action="store_true")
    sub.add_parser("auth")
    sub.add_parser("worker")
    args = p.parse_args(argv)
    {"setup": cmd_setup, "key": cmd_key, "build": cmd_build, "up": cmd_up, "stats": cmd_stats,
     "down": cmd_down, "auth": cmd_auth, "worker": cmd_worker}[args.cmd](args)


if __name__ == "__main__":
    main()
