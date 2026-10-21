#!/usr/bin/env bash
# flew by 冒頭フック用の素材を public/hook/ に整える（ffmpeg）。
# 指定したものだけ処理する。例:
#   bash scripts/prepare-hook-assets.sh \
#     --main-ad "~/Downloads/flewby１０月広告動画文字入り.mp4" \
#     --store   "~/Downloads/家からflewby散歩MKT02714.jpg" \
#     --logo    "~/Downloads/flew by ロゴ透過.png" \
#     --wide    ai/cut01_wide.mp4 \
#     --closeup ai/cut02_closeup.mp4 \
#     --hand    ai/cut02_hand_fg.mov
set -euo pipefail

OUT="$(cd "$(dirname "$0")/.." && pwd)/public/hook"
mkdir -p "$OUT"

# 1080×1920 に cover でクロップ（縦横比が違う素材でも黒帯を出さない）
FIT="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

while [[ $# -gt 0 ]]; do
	key="$1"; src="${2:?missing path for $1}"; shift 2
	case "$key" in
		--wide|--closeup)
			name=$([[ "$key" == --wide ]] && echo cut01_wide || echo cut02_closeup)
			ffmpeg -loglevel error -y -i "$src" -vf "$FIT,fps=30,setsar=1" -an \
				-c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p "$OUT/$name.mp4"
			;;
		--hand)
			# アルファ付き（ProRes 4444 / PNG 連番 mov 等）→ VP9 WebM（yuva420p）
			ffmpeg -loglevel error -y -i "$src" -vf "$FIT,fps=30,setsar=1,format=yuva420p" -an \
				-c:v libvpx-vp9 -b:v 0 -crf 20 -auto-alt-ref 0 "$OUT/cut02_hand_fg.webm"
			;;
		--main-ad)
			# 本編の 1 フレーム目をそのまま書き出す（フック最終フレーム＝本編冒頭）
			ffmpeg -loglevel error -y -i "$src" -vf "$FIT,setsar=1" -frames:v 1 -q:v 1 "$OUT/main_ad_first_frame.jpg"
			;;
		--store)
			ffmpeg -loglevel error -y -i "$src" -vf "scale=1440:-2" -q:v 2 "$OUT/store_photo.jpg"
			;;
		--logo)
			cp "$src" "$OUT/flewby_logo.png"
			;;
		*) echo "unknown option: $key" >&2; exit 1 ;;
	esac
	echo "✓ $key → $OUT"
done
