---
name: review-article
description: 既存の記事（下書き・投稿準備済み・公開済み）を4人の編集者の視点で評価し、修正する（STEP 9・11）。公開済み記事の改訂にも使う。
argument-hint: "<slug> [--no-fix（評価だけ）]"
---

# /review-article

対象：$ARGUMENTS

1. 記事ファイルを探す。`articles/drafts/<slug>.md` → `articles/ready_to_publish/` → `articles/published/<slug>/` の順に探す。
2. `.claude/skills/write-article/SKILL.md` の手順4（ファクトチェックと編集）を実行し、結果を `articles/review/<slug>.md` に保存する。既存のレビューがあれば `articles/review/<slug>.v<N>.md` に退避する。
3. `--no-fix` が指定されていれば、評価の要約を報告して終了する。
4. 修正する場合は、手順5（修正）と手順6（分割と最終評価）を実行する。
   - 投稿準備済み（awaiting_approval）の記事を修正した場合は、`python3 scripts/export_note.py` で投稿用ファイルを作り直す。承認は無効になるため、改めて承認を求める。
   - **公開済みの記事は、`articles/published/<slug>/` を直接書き換えない。** 修正版を `articles/drafts/<slug>.rev<N>.md` として作り、人間が note 上で更新するための差分の要約を報告する。
