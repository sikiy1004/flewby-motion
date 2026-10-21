#!/usr/bin/env bash
# flew by 冒頭フック用の素材を public/hook/ に整える（ffmpeg）。
# 指定したものだけ処理する。例:
#   bash scripts/prepare-hook-assets.sh \
#     --main-ad "~/Downloads/flewby１０月広告動画文字入り.mp4" \
#     --store   "~/Downloads/MKT02421.jpg" \
#     --logo    "~/Downloads/flew by ロゴ透過.png" \
#     --bg-x 0.27 --background ~/Downloads/susukino.jpg \
#     --still   ~/Downloads/woman.webp \
#     --wide    ai/cut01_wide.mp4 \
#     --closeup ai/cut02_closeup.mp4 \
#     --hand    ai/cut02_hand_fg.mov
set -euo pipefail

OUT="$(cd "$(dirname "$0")/.." && pwd)/public/hook"

# ffmpeg が入っていなければ Remotion 同梱の ffmpeg を使う（npm install 済みなら追加インストール不要）。
# 同梱版はフィルタが最小限なので、fps / setsar フィルタは使わず -r で fps を揃える。
if command -v ffmpeg >/dev/null 2>&1; then
	FFMPEG=(ffmpeg)
else
	FFMPEG=(npx --no-install remotion ffmpeg)
fi
mkdir -p "$OUT"

# 1080×1920 に cover でクロップ（縦横比が違う素材でも黒帯を出さない）
FIT="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

while [[ $# -gt 0 ]]; do
	key="$1"; src="${2:?missing path for $1}"; shift 2
	case "$key" in
		--wide|--closeup)
			name=$([[ "$key" == --wide ]] && echo cut01_wide || echo cut02_closeup)
			"${FFMPEG[@]}" -loglevel error -y -i "$src" -vf "$FIT" -r 30 -an \
				-c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p "$OUT/$name.mp4"
			;;
		--hand)
			# アルファ付き（ProRes 4444 / PNG 連番 mov 等）→ VP9 WebM（yuva420p）
			"${FFMPEG[@]}" -loglevel error -y -i "$src" -vf "$FIT,format=yuva420p" -r 30 -an \
				-c:v libvpx-vp9 -b:v 0 -crf 20 -auto-alt-ref 0 "$OUT/cut02_hand_fg.webm"
			;;
		--bg-x)
			# 横長写真から 9:16 を切り出すときの左右位置（0 = 左端, 1 = 右端）。--background より前に指定する。
			BG_X="$src"
			;;
		--background)
			# 横長の夜景写真から 9:16 を切り出して 1080×1920 に拡大（ボケさせて使うので解像度は低くてよい）
			"${FFMPEG[@]}" -loglevel error -y -i "$src" \
				-vf "crop=ih*9/16:ih:(iw-ih*9/16)*${BG_X:-0.5}:0,scale=1080:1920:flags=lanczos" \
				-q:v 2 "$OUT/susukino_crossing.jpg"
			;;
		--still)
			# 女性の静止画 1 枚（動画の代わり）。1080×1920 に cover で整える。座標は config.ts の STILL。
			"${FFMPEG[@]}" -loglevel error -y -i "$src" -vf "$FIT" -q:v 2 "$OUT/woman_still.jpg"
			;;
		--main-ad)
			# 本編の 1 フレーム目をそのまま書き出す（フック最終フレーム＝本編冒頭）
			"${FFMPEG[@]}" -loglevel error -y -i "$src" -vf "$FIT" -frames:v 1 -q:v 1 "$OUT/main_ad_first_frame.jpg"
			;;
		--store)
			"${FFMPEG[@]}" -loglevel error -y -i "$src" -vf "scale=1440:-2" -q:v 2 "$OUT/store_photo.jpg"
			;;
		--logo)
			cp "$src" "$OUT/flewby_logo.png"
			;;
		*) echo "unknown option: $key" >&2; exit 1 ;;
	esac
	echo "✓ $key → $OUT"
done
