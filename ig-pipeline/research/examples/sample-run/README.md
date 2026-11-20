# 見本の実行フォルダ（テスト用データ）

R2 の動作確認で作った実行1回分の中身です。商品・価格はすべて架空です。
実際の実行は research/runs/<実行ID>/ に作られます（Git には上がりません）。

- market.md / market/：楽天の取得結果（テスト用データ）
- evidence/：出典ファイルの雛形
- ideas.json：投稿案の元データ（Claude が書く）
- ideas.md：投稿案リスト（npm run research:ideas -- render で生成）
