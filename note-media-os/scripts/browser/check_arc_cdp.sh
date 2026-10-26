#!/bin/sh
# Arc に CDP（Chrome DevTools Protocol）で接続できるかだけを確かめる（macOS で人間が実行する）。
# 接続はしない。/json/version のメタデータ（ブラウザ名・バージョン）を表示するだけで、タブ・Cookie・履歴には触れない。
#
# 事前準備（人間が行う）:
#   1. Arc を完全に終了する
#   2. open -a Arc --args --remote-debugging-port=9222
#   3. このスクリプトを実行する: sh scripts/browser/check_arc_cdp.sh
#   4. 確認が終わったら Arc を終了し、通常どおり起動し直す（デバッグポートを開いたままにしない）
PORT="${1:-9222}"
if curl -fsS --max-time 3 "http://127.0.0.1:${PORT}/json/version"; then
  echo
  echo "CDP エンドポイントが応答しました（port ${PORT}）。"
  echo "注意: ここに Playwright MCP を接続すると、Arc の既存プロファイル（ログイン中の全サイトの Cookie）を自動化から操作できる状態になる。"
  echo "このプロジェクトでは接続しない方針。必要な場合は、オーナーが明示的に判断すること。"
else
  echo "CDP エンドポイントが応答しませんでした（port ${PORT}）。"
  echo "考えられる原因: Arc が起動フラグを無視した／既存の Arc プロセスが残っていた／Chromium 系ブラウザの新しい版は既定プロファイルでのリモートデバッグを制限している。"
fi
