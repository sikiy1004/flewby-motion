# 見本の実行フォルダ（テスト用データ・架空の商品）

リサーチ層の R1〜R3 の動作確認で作った、実行1回分の中身です。商品・価格・出典はすべて架空です
（出典 URL が `fixture:` で始まるものは、テスト用データを指す見本です）。
実際の実行は `research/runs/<実行ID>/` に作られ、Git には上がりません。

| ファイル | 内容 |
|---|---|
| market.md / market/ | 楽天の取得結果（テスト用データ） |
| evidence/ | 出典ファイル。test-ems-device・test-light-dryer・test-scalp-dryer は記入済み、test-sonic-brush は雛形のまま |
| ideas.json | 投稿案の元データ（I09 は、チェックが違反を止めることを示すための「違反の見本」） |
| ideas.md | 投稿案リスト |
| drafts/<投稿ID>/ | 原稿データ一式：post.json・products.json（既存スキーマ準拠）、posts.csv・products.csv、caption.txt、check.md（判定と出典の一覧） |

**注意**：drafts/ は、承認の手順を省いて生成処理だけを試した見本です。実際のコマンド
（`npm run research:draft` / `research:install`）は、オーナーの承認（`npm run research:approve`）がない案では生成しません。
