---
name: research
description: 美容ガジェットの最新情報（楽天の売れ筋・新商品・公式スペック・セール時期・話題の切り口）を調べ、出典つきの投稿案リストを作ってオーナーに提示する。承認の前で必ず止まる。「リサーチして」「投稿案を出して」「ネタを探して」や /research [テーマ] で使う。
---

# /research — リサーチして投稿案を提示する（承認の手前まで）

引数：任意のテーマ（例：`ドライヤー`、`ブラックフライデー`、`美顔器 2万円以下`）。`--fixture` はテスト用データで練習する場合だけ。
CLAUDE.md のルールをすべて守る。各段階の終わりに、何をしたかを1〜2行でオーナーに伝える。

## 0. 前提の確認
- `research/config.json`（カテゴリと優先順、鮮度の上限）、`data/posts/*.json`（投稿済みの内容と A/B の比率）、直近の `research/runs/*/ideas.md` を読む（同じ案を繰り返さない）。
- `research/config.json` の `rakuten.specVerified` が `false` なら、**最初に**楽天ウェブサービスの公式ドキュメント（商品検索・ランキング・ジャンル検索）を読み、
  エンドポイント・`accessKey` の渡し方・Referer/Origin の要否・価格とセールに関する出力項目・回数制限を確認してオーナーに報告する。
  設定の変更と `specVerified: true` への切り替えは、オーナーの了承を得てから行う。公式ページが読めなければ、そう伝えて楽天 API は使わない。

## 1. 楽天の売れ筋（キーがある場合）
- `.env` に `RAKUTEN_APP_ID` と `RAKUTEN_ACCESS_KEY` があれば `npm run research:rakuten`（テーマに合うカテゴリだけなら `-- <カテゴリキー>`）。
  新しい実行ID（`research/runs/<実行ID>/`）ができる。`genreId` が未設定のカテゴリは、楽天ランキングのページの URL から確認し、オーナーに伝えてから設定する。
- キーがない・失敗した場合は、その旨を1行で伝え、Web 調査だけで進める（実行IDは `node -e 'import("./pipeline/research/lib.mjs").then(m=>console.log(m.newRunId()))'` で作り、`research/runs/<実行ID>/` を用意する）。

## 2. Web 調査（並行して検索。出典 URL と取得日時を必ず控える）
1. **セールの時期**：楽天スーパーSALE・お買い物マラソン・Qoo10メガ割・Amazon の大型セール（プライムデー、ブラックフライデーなど）の、**公式の告知ページ**で開催期間を確認する。
   結果を `research/runs/<実行ID>/sales.md` に表で残す（イベント・開始・終了・URL・取得日時）。日付が公式で確認できないものは「未確認」と書く。
2. **新商品・話題の商品**：メーカー公式のニュース・商品ページを優先し、直近 `freshness.newsWindowDays` 日以内の発売・リニューアルを拾う。
3. **トレンド（切り口）**：美容ガジェットで話題のテーマ（例：韓国美容デバイス、時短ケア）を検索し、`research/runs/<実行ID>/trends.md` に出典つきで要約する。
   **デザイン（トークン・テンプレート・世界観）には反映しない。**
4. **競合の「型」**：`research/competitors/` にオーナーが記録したものがあれば参考にする（自分で Instagram を収集しない）。

## 3. 商品ごとの出典ファイル
- 楽天の取得結果から雛形を作る：`npm run research:evidence -- new <実行ID> <商品ID> --from <カテゴリキー>:<順位>`（商品IDは英小文字・数字・ハイフン）。
- **メーカー公式ページを読んで**記入する：`fields`（category・brand・name・nameJa）、`specs`（6項目まで。機能・サイズ・重量・対応モードなど）、
  `points`（3個まで・各20字まで。`basis` は `spec`＝スペックに基づく要約／`official-quote`＝「」で囲んだ公式表現の引用）。すべてに URL と取得日時。
- **価格**：`regular`（メーカー希望小売価格・公式ストア価格・ショップの通常価格表示。どれかを `label` に書く）と、
  `sale`（セール名・開始・終了つき）を分けて記録し、投稿に出す価格を `display`、その種別を `basis` に入れる。分からなければ `unverified` のまま。
- `image.sourceUrl` には画像の取得元を記録するだけ。公開用の画像はオーナーに用意してもらう（それまでは `rights: "placeholder"`）。
- 全項目に出典がそろったものだけ `status: "complete"` にする。`npm run research:evidence -- validate <実行ID>` で形式を確認する。

## 4. 投稿案を書く → `research/runs/<実行ID>/ideas.json`（形式：`research/schema/ideas.schema.json`）
- 3〜5案。A案（カルーセル：単品 `single`／2〜4点の比較 `compare`）と B案（リール：結論 `reel-conclusion`／ランキング `reel-ranking`）を、投稿済みの分も含めて約 8:2 に保つ。
- 表紙の英単語（英字のみ・9字まで）＋別案、明朝のリード（50字まで・2行）、オーロラの種類（dawn/shift/radiance/ember/tide/mist）、B案はリール見出し（30字まで）。
- 推奨タイミングは、`sales.md` のセール期間と連動させる（理由と出典を書く）。期限が切れたセール・72時間より古い価格は使わない。
- 文言は短く静かに。数値は出典ファイルにあるものだけ。効能の断定・使用感の表現は書かない。
- `npm run research:ideas -- render <実行ID>` を実行し、エラーがあれば直す（ルールを緩めない）。

## 5. 提示して止まる
- `ideas.md` の一覧表（ID・テーマ・対象商品と価格・A/B・表紙の英単語・見出し・推奨タイミング）をチャットに要約し、「確認が必要な点」も伝える。
- 承認方法を伝える：オーナーが端末で `npm run research:approve -- <実行ID> I01 I03` を実行する。
- **ここで止まる。承認コマンドは実行しない。** 承認後に `/research-draft <案ID>` で続ける。
