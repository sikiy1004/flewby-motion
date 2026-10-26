---
name: write-article
description: 指定した企画ID、またはテーマの記事を、リサーチから投稿用データの出力まで制作する（STEP 5〜12）。公開はしない。最後に人間の承認を求める。
argument-hint: "<企画ID（例 I-G05-01）または「テーマ」>"
---

# /write-article

対象：$ARGUMENTS

この手順は `/auto-create` からも呼ばれる。**記事を公開してはならない。**

## 0. 準備

1. `config/settings.md` と `config/editorial_policy.md` を読む。
2. 承認待ちの数を確認する：`python3 scripts/article_state.py list awaiting_approval`。上限（settings の「承認待ちの上限」）以上なら、制作を始めずに、承認を促して終了する。
3. 開始時刻を記録する（`date +%s`）。

## 1. 対象の確定（STEP 4）

- 引数が企画ID（`I-` で始まる）なら、`ideas/backlog/ideas.csv` の該当行を使う。status が `backlog` でなければ、理由を確認して止まる。
- 引数が自由なテーマなら、`prompts/ideation.md` に従って企画を1行作る。採点後、ジャンルを選んで `ideas.csv` に追記する。
- `python3 scripts/ideas.py dup "<タイトル>"` で重複を確認する。類似度0.6以上の既存記事（`articles/index.csv` にあるもの）があれば、切り口の違いを確認する。違いが説明できなければ止まって、人間に相談する。
- slug は企画IDを小文字にしたもの（例：`i-g05-01`）。
- 登録する：`python3 scripts/article_state.py register <slug> <idea_id> <genre_id> <title_type> <price_yen> "<タイトル>"`

## 2. リサーチ（STEP 5）

`researcher` サブエージェントに、企画の行の内容と、`prompts/research.md` に従って `articles/research/<slug>.md` を書くことを指示する。

戻ってきたら、確認済みの文献が記事を支えるのに十分か判断する。目安は、確認済みの文献が5件以上で、中心の主張の根拠が「書誌のみ」でないこと。不十分なら、追加のリサーチを1回だけ依頼する。それでも不十分なら、`python3 scripts/article_state.py status <slug> needs_human` を実行して止まる。

## 3. 構成と執筆（STEP 6〜7）

`writer` サブエージェントに、`prompts/writing.md` に従って `articles/outlines/<slug>.md` と `articles/drafts/<slug>.md`（version: 1）を書くことを指示する。

## 4. ファクトチェックと編集（STEP 8〜9）

1. `python3 scripts/article_state.py status <slug> in_review`
2. `config/settings.md` のレビューモードを確認する。
   - `full`：`editor-logic`、`editor-factcheck`、`editor-reader`、`editor-originality` の4つのサブエージェントを**並列で**起動する。各エージェントには、slug と下書きのパスを渡す。
   - `light`：`editor-factcheck` だけをサブエージェントで起動し、A・C・D の観点はメインのセッションで `prompts/editing.md` に従って確認する。
3. 結果を `prompts/editing.md` の「最終品質評価」の形式で `articles/review/<slug>.md` に保存する（front matter の version は、レビュー対象の版）。

## 5. 修正（STEP 9 の続き）

- 判定が `revise` なら、`writer` に `articles/review/<slug>.md` の指摘への対応を指示する。version が上がる。
- 判定が `rewrite` なら、`writer` に構成からの再執筆を指示する。ファクトの blocker が原因なら、先に `researcher` で該当箇所を調べ直す。
- 修正後、指摘のあった観点の編集者だけを再実行する。blocker が出ていた場合は、必ず `editor-factcheck` を再実行する。新しい版の結果で `articles/review/<slug>.md` を更新する。前回のレビューは `articles/review/<slug>.v<N>.md` に退避する。
- 再執筆の回数が上限を超えたら、`python3 scripts/article_state.py status <slug> needs_human` を実行して止まり、論点を人間に示す。
- 最終スコアが80に届かない有料記事は、無料記事への変更を提案して止まる。

## 6. 分割と最終評価（STEP 10〜11）

1. `prompts/note_export.md` の STEP 10 を確認する。
2. `python3 scripts/article_state.py score <slug> <合計点>`
3. `python3 scripts/check_article.py articles/drafts/<slug>.md --final` が OK になることを確認する。

## 7. 投稿用データの出力（STEP 12）

1. `python3 scripts/export_note.py articles/drafts/<slug>.md`
2. `articles/ready_to_publish/<slug>.publish.md` に、ハッシュタグ案（3〜5個）とマガジン案（`brand/brand_proposal.md` §11）を記入する。
3. 経過時間（分）を記録する：`python3 scripts/article_state.py minutes <slug> <分>`

## 8. 承認の依頼

人間に次を報告して終了する。**ここで止まり、公開しない。**

- タイトル、価格、品質スコア（各編集者の点）
- 主な修正履歴（何を直したか）
- 未解決の WARN と、その判断
- 確認できなかった事項（あれば）
- 次の操作：`articles/ready_to_publish/<slug>.publish.md` のチェックリストを確認し、`/approve-article <slug>` を実行する
