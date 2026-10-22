#!/usr/bin/env bash
# Turns mascot3d.py's transparent PNG frames into files an app or a page can play, and makes contact sheets to look at.
#
#   encode.sh FRAMES_DIR OUT_BASE [targets] [--fps 60] [--bg "#FFFFFF"] [--kbps N]
#       targets (default: ios web preview still):
#         ios      OUT_BASE.mov   HEVC with alpha (Apple devices: AVFoundation, Safari). Needs macOS (VideoToolbox).
#         web      OUT_BASE.webm  VP9 with alpha (Chrome, Firefox, Edge, Android WebView).
#         preview  OUT_BASE-preview.mp4  on a solid background, to share or check.
#         gif      OUT_BASE.gif   30 fps with 1-bit transparency (edges are jagged; for docs and chats only).
#         still    OUT_BASE.png   the last frame, for Reduce Motion and posters.
#
#   encode.sh sheet DIR OUT.png [--bg "#FFFFFF"] [--count 12] [--cols 6] [--scale 0.5]
#       Tiles the PNGs in DIR on a background: every still in a check, or COUNT frames spread across an animation.
#
# Needs ffmpeg (and ffprobe). The ios target also checks with AVFoundation that the alpha survived, when swiftc exists.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
die() { echo "encode.sh: $*" >&2; exit 1; }
command -v ffmpeg >/dev/null || die "ffmpeg isn't installed (brew install ffmpeg)"

size_of() { ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$1"; }

if [[ "${1:-}" == "sheet" ]]; then
  dir="${2:?sheet needs a folder}"; out="${3:?sheet needs an output .png}"; shift 3
  bg="#FFFFFF"; count=12; cols=6; scale=0.5
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --bg) bg="$2"; shift 2 ;; --count) count="$2"; shift 2 ;; --cols) cols="$2"; shift 2 ;;
      --scale) scale="$2"; shift 2 ;; *) die "unknown option $1" ;;
    esac
  done
  tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
  files=()
  shopt -s nullglob
  all=("$dir"/f_*.png)
  if [[ ${#all[@]} -gt 0 ]]; then
    n=${#all[@]}
    (( count > n )) && count=$n
    for ((k = 0; k < count; k++)); do files+=("${all[$(( k * (n - 1) / (count > 1 ? count - 1 : 1) ))]}"); done
  else
    for f in "$dir"/*.png; do [[ "$(basename "$f")" == last.png ]] || files+=("$f"); done
  fi
  [[ ${#files[@]} -gt 0 ]] || die "no PNGs in $dir"
  k=0; for f in "${files[@]}"; do k=$((k + 1)); ln -s "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" "$tmp/$(printf %04d $k).png"; done
  rows=$(( (k + cols - 1) / cols )); (( k < cols )) && cols=$k
  wh="$(size_of "${files[0]}")"
  ffmpeg -loglevel error -y -i "$tmp/%04d.png" -f lavfi -i "color=c=${bg}:s=${wh}" -filter_complex \
    "[1][0]overlay=shortest=1,scale=iw*${scale}:-2,tile=${cols}x${rows}:padding=6:color=${bg}" -frames:v 1 "$out"
  echo "sheet: $out (${k} images)"
  exit 0
fi

dir="${1:?usage: encode.sh FRAMES_DIR OUT_BASE [targets] [options]}"; base="${2:?usage: encode.sh FRAMES_DIR OUT_BASE}"; shift 2
targets=(); fps=60; bg="#FFFFFF"; kbps=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fps) fps="$2"; shift 2 ;; --bg) bg="$2"; shift 2 ;; --kbps) kbps="$2"; shift 2 ;;
    ios|web|preview|gif|still) targets+=("$1"); shift ;;
    *) die "unknown target or option $1" ;;
  esac
done
[[ ${#targets[@]} -gt 0 ]] || targets=(ios web preview still)
shopt -s nullglob
frames=("$dir"/f_*.png)       # a glob, not `ls | head`: under pipefail a long listing dies of SIGPIPE without a word
[[ ${#frames[@]} -gt 0 ]] || die "no f_####.png frames in $dir"
first="${frames[0]}"
start="$(basename "$first" .png)"; start="$((10#${start#f_}))"
wh="$(size_of "$first")"; w="${wh%x*}"; h="${wh#*x}"
# About 900 kbit/s for a 300 px square, scaled by area, kept between 600 and 4000.
[[ -n "$kbps" ]] || kbps=$(( w * h / 100 )); (( kbps < 600 )) && kbps=600; (( kbps > 4000 )) && kbps=4000
in=(-framerate "$fps" -start_number "$start" -i "$dir/f_%04d.png")
mkdir -p "$(dirname "$base")"

for t in "${targets[@]}"; do
  case "$t" in
    ios)
      ffmpeg -hide_banner -encoders 2>/dev/null | grep -q hevc_videotoolbox || die "ios needs macOS (hevc_videotoolbox)"
      ffmpeg -loglevel error -y "${in[@]}" -c:v hevc_videotoolbox -alpha_quality 0.8 -b:v "${kbps}k" -tag:v hvc1 \
        -pix_fmt bgra "$base.mov"
      echo "ios: $base.mov ($(du -h "$base.mov" | cut -f1))"
      if command -v swiftc >/dev/null; then
        check="${TMPDIR:-/tmp}/mascot-alphacheck"
        [[ -x "$check" ]] || swiftc -O "$HERE/alphacheck.swift" -o "$check" 2>/dev/null || true
        [[ -x "$check" ]] && "$check" "$base.mov" || true      # checks frames across the clip, not just the first
      fi
      ;;
    web)
      ffmpeg -loglevel error -y "${in[@]}" -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 32 -row-mt 1 \
        -auto-alt-ref 0 "$base.webm"
      echo "web: $base.webm ($(du -h "$base.webm" | cut -f1))"
      ;;
    preview)
      ffmpeg -loglevel error -y "${in[@]}" -f lavfi -i "color=c=${bg}:s=${w}x${h}:r=${fps}" -filter_complex \
        "[1][0]overlay=shortest=1,format=yuv420p" -c:v libx264 -crf 18 -movflags +faststart "$base-preview.mp4"
      echo "preview: $base-preview.mp4"
      ;;
    gif)
      ffmpeg -loglevel error -y "${in[@]}" -vf \
        "fps=30,split[a][b];[a]palettegen=reserve_transparent=1:stats_mode=diff[p];[b][p]paletteuse=alpha_threshold=128" \
        -loop 0 "$base.gif"
      echo "gif: $base.gif ($(du -h "$base.gif" | cut -f1))"
      ;;
    still)
      last="$dir/last.png"; [[ -f "$last" ]] || last="${frames[${#frames[@]}-1]}"
      cp "$last" "$base.png"; echo "still: $base.png"
      ;;
  esac
done
