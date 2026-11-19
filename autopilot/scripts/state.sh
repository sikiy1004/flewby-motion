#!/usr/bin/env bash
# SQLite の状態ファイルを、リポジトリの専用ブランチ（autopilot-state）に保存・復元する。
# 毎回 1 コミットだけのブランチを強制更新するので、履歴は肥大化しない。
#   scripts/state.sh pull   … ブランチから autopilot/data/autopilot.db を復元（無ければ何もしない）
#   scripts/state.sh push   … autopilot/data/autopilot.db をブランチへ保存
set -euo pipefail
BRANCH="${STATE_BRANCH:-autopilot-state}"
ROOT="$(git rev-parse --show-toplevel)"
DB="${AUTOPILOT_DB:-$ROOT/autopilot/data/autopilot.db}"
mkdir -p "$(dirname "$DB")"

case "${1:-}" in
  pull)
    if git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
      git fetch --depth 1 origin "$BRANCH"
      git show "FETCH_HEAD:autopilot.db" > "$DB"
      echo "state restored ($(du -h "$DB" | cut -f1))"
    else
      echo "no state branch yet (first run)"
    fi
    ;;
  push)
    [ -f "$DB" ] || { echo "no db to save"; exit 0; }
    export GIT_AUTHOR_NAME="autopilot-bot" GIT_AUTHOR_EMAIL="autopilot-bot@users.noreply.github.com"
    export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
    blob=$(git hash-object -w "$DB")
    tree=$(printf "100644 blob %s\tautopilot.db\n" "$blob" | git mktree)
    commit=$(git commit-tree "$tree" -m "autopilot state $(date -u +%FT%TZ)")
    for i in 1 2 3 4; do
      git push -f origin "$commit:refs/heads/$BRANCH" && { echo "state saved"; exit 0; }
      sleep $((i * 3))
    done
    echo "failed to push state" >&2; exit 1
    ;;
  *) echo "usage: $0 pull|push" >&2; exit 2 ;;
esac
