#!/bin/zsh -l
# Weekly research run (macOS). Produces the idea list (ideas.md) and STOPS — it never approves, drafts or renders.
# Installed by scripts/schedule/install-weekly.sh; can also be run by hand to test:  zsh scripts/schedule/weekly-research.sh
set -u
cd "$(dirname "$0")/../.." || exit 1
mkdir -p research/logs
LOG="research/logs/$(date +%Y%m%d-%H%M).log"
{
  echo "== weekly research $(date '+%Y-%m-%d %H:%M') =="
  git pull --ff-only 2>&1 || echo "(git pull skipped)"
  claude -p "/research 定期実行です。リサーチして投稿案リスト（ideas.md）を作ったら止まってください。承認・原稿データの生成・取り込み・描画には進まないでください。最後に、作った実行IDと案の数を1行で書いてください。" \
    --allowedTools "Read" "Glob" "Grep" "WebSearch" "WebFetch" \
      "Edit(research/**)" "Write(research/**)" \
      "Bash(npm run research:rakuten*)" "Bash(npm run research:evidence*)" "Bash(npm run research:calendar*)" \
      "Bash(npm run research:ideas*)" "Bash(npm run research:competitors -- summary*)" "Bash(node -e *)" \
    --disallowedTools "Bash(npm run research:approve*)" "Bash(*approve.mjs*)" "Bash(npm run research:draft*)" \
      "Bash(npm run research:install*)" "Bash(npm run build*)" "Bash(git push*)" "Bash(git commit*)" \
      "Edit(data/**)" "Edit(templates/**)" "Edit(tokens/**)" "Edit(research/runs/**/approval.json)"
  echo "== exit $? =="
} >> "$LOG" 2>&1
LATEST=$(ls -d research/runs/*/ 2>/dev/null | grep -v sample | tail -1)
if [ -n "$LATEST" ] && [ -f "${LATEST}ideas.md" ]; then
  osascript -e "display notification \"${LATEST}ideas.md を確認して、承認する案を選んでください\" with title \"ig-pipeline：投稿案リストができました\"" 2>/dev/null
else
  osascript -e "display notification \"ログを確認してください：$LOG\" with title \"ig-pipeline：リサーチが完了しませんでした\"" 2>/dev/null
fi
