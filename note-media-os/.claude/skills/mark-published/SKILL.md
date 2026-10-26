---
name: mark-published
description: オーナーが note で公開した記事を、公開済みとして記録する。オーナーが手動で実行するためのコマンド。
argument-hint: "<slug> <noteの記事URL> [公開日 YYYY-MM-DD]"
disable-model-invocation: true
---

# /mark-published

引数：$ARGUMENTS

1. 記録する：`python3 scripts/article_state.py published <slug> <URL> [公開日]`
   - 承認されていない記事は、スクリプトが拒否する。拒否された場合は、承認の手順（`/approve-article`）を案内する。
2. `articles/published/<slug>/` にファイルが移ったことを確認する。
3. 販売実績の入力方法を案内する：月に一度、note のダッシュボードからビュー数・購入数・売上を `/analytics <period> <slug> views=.. purchases=..` で入力する。
