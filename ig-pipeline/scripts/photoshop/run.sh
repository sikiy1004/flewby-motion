#!/usr/bin/env bash
# macOS: run a Photoshop script from the terminal.  bash scripts/photoshop/run.sh remove-bg|export-cutout
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
script="$here/${1:-remove-bg}.jsx"
[ -f "$script" ] || { echo "no such script: $script" >&2; exit 1; }
osascript -e "tell application id \"com.adobe.Photoshop\" to do javascript (POSIX file \"$script\")"
