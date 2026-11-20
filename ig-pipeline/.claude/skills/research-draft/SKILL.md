---
name: research-draft
description: オーナーが承認した投稿案から、既存の入力スキーマに沿った原稿データ（JSON・CSV・キャプション案・ハッシュタグ案）を作ってチェックし、取り込むかを確認する。「原稿を作って」「承認した案を進めて」や /research-draft <案ID> [実行ID] で使う。
---

# /research-draft — 承認済みの案 → 原稿データ

引数：案ID（例 `I01`）、任意で実行ID（省略時は最新）。CLAUDE.md のルールをすべて守る。

1. **承認の確認**：`npm run research:approve -- status <実行ID>` を実行する。対象の案が承認済み（✓）でなければ、オーナーに承認方法を伝えて止まる。
   承認を代行しない。
2. **出典ファイルの仕上げ**：対象商品の `research/runs/<実行ID>/evidence/*.json` が `complete` でなければ、メーカー公式ページなどを読んで記入する
   （/research の手順3と同じ。推測で埋めない）。価格が古い・セール期限が近い場合は取り直す。
   - **案（ideas.json）の文言を変える必要が出たら、変えずにオーナーに伝える**（変えると承認がやり直しになる）。
3. **生成とチェック**：`npm run research:draft -- <実行ID> <案ID>`
   - 結果は `research/runs/<実行ID>/drafts/<投稿ID>/`（post.json・products.json・posts.csv・products.csv・caption.txt・check.md）。
   - エラーは出典ファイルの不足を埋めて直す。表現のエラーは、出典ファイルのポイントなら書き直し、案の文言ならオーナーに相談する。
     ルール（`research/compliance.json`）を緩めない。
   - 画像がレイアウト確認用のままなら、オーナーに写真の用意を頼む。レイアウト確認だけを頼まれた場合に限り `--allow-placeholder` を使う。
4. **オーナーに確認**：check.md の判定・警告・価格と出典の表、caption.txt（キャプション案とハッシュタグ案）を見せて、取り込むか聞く。
5. **取り込み**（了承後）：`npm run research:install -- <実行ID> <案ID>`（`--allow-placeholder` を使った場合は同じく付ける）。
   既存の商品と内容が違うと止まるので、置き換えてよいかオーナーに確認してから `--update` を付ける。
6. **描画はオーナーの指示で**：`npm run cutout && npm run build -- data/posts/<投稿ID>.json`。完成画像の場所を伝える。
