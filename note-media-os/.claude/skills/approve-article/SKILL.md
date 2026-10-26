---
name: approve-article
description: 人間のオーナーが、投稿準備済みの記事の公開を承認する。オーナーが手動で実行するためのコマンド。
argument-hint: "<slug>"
disable-model-invocation: true
---

# /approve-article

対象：$ARGUMENTS

このコマンドはオーナーが自分で実行したときだけ使う。オーナーが `/approve-article <slug>` を実行したこと自体を、承認の意思表示として扱う。

1. `articles/ready_to_publish/<slug>.publish.md` と `<slug>.note.md` があることを確認する。
2. `config/settings.md` から承認者名（「オーナー名」）を読む。未設定なら、オーナーに名前を尋ねる。
3. 承認を記録する：`python3 scripts/article_state.py approve <slug> "<承認者名>"`
4. `<slug>.publish.md` の「承認」欄に、承認者と承認日を記入する。
5. `prompts/note_export.md` の「公開手順」の 2〜6 を、オーナー向けに表示する。**Claude は note に投稿しない。**
