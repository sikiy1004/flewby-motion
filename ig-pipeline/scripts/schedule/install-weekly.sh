#!/bin/zsh
# Install / remove the weekly research job (macOS launchd).
#   zsh scripts/schedule/install-weekly.sh                  every Monday 07:40 (default)
#   zsh scripts/schedule/install-weekly.sh 4 21 10          weekday(0=Sun..6=Sat) hour minute → Thursday 21:10
#   zsh scripts/schedule/install-weekly.sh --remove
# If the Mac is asleep at that time, launchd runs the job when it wakes up.
set -eu
LABEL="com.igpipeline.weekly-research"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DIR="$(cd "$(dirname "$0")/../.." && pwd)"
if [ "${1:-}" = "--remove" ]; then
  launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"; echo "removed $LABEL"; exit 0
fi
WD="${1:-1}"; HH="${2:-7}"; MM="${3:-40}"
mkdir -p "$HOME/Library/LaunchAgents" "$DIR/research/logs"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array><string>/bin/zsh</string><string>-l</string><string>$DIR/scripts/schedule/weekly-research.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Weekday</key><integer>$WD</integer><key>Hour</key><integer>$HH</integer><key>Minute</key><integer>$MM</integer></dict>
  <key>StandardOutPath</key><string>$DIR/research/logs/launchd.out.log</string>
  <key>StandardErrorPath</key><string>$DIR/research/logs/launchd.err.log</string>
</dict>
</plist>
PL
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "installed $LABEL：毎週 weekday=$WD $HH:$(printf %02d $MM) に投稿案リストを作ります（承認・描画はしません）"
