---
name: competitor-log
description: オーナーが貼った競合アカウントの公開投稿（URL・キャプション本文・スクリーンショット）から、投稿の「型」（テーマ・構成・見出しの作り方）を分類して記録する。Instagram を自分で閲覧・収集しない。「競合を記録して」「この投稿を記録」や /competitor-log で使う。
---

# /competitor-log — 競合の投稿の「型」を記録する（半自動）

**前提**：Instagram の規約に反する自動収集はしない。Claude は Instagram のページを開かない・検索で集めない。
扱うのは、オーナーがアプリで見て貼った公開投稿の情報だけ。

1. オーナーに、次を貼ってもらう（1件ずつでも、まとめてでもよい）：
   - 投稿の URL（`https://www.instagram.com/p/…` か `/reel/…`）
   - キャプション本文、または表紙や各ページのスクリーンショット、枚数、投稿日（分かれば）
2. 1件ごとに「型」を分類する：
   - `format`：carousel / reel / image、`slides`：枚数
   - `theme`：何についての投稿か（例：美顔器3機種の比較）、`category`：research/config.json のカテゴリキー（なければ other）
   - `structure`：ページ構成（例：表紙→比較表→各機種→結論→保存の呼びかけ）
   - `headlinePattern`：見出しの作り方（例：「〇〇、結局これ。」結論先出し／数字＋悩み／ビフォーアフター型）
   - `hook`：表紙の要点を**40字以内の自分の言葉で要約**（本文や表紙の文をそのまま写さない）
   - `cta`：誘導の仕方（例：プロフィールのリンク、保存の呼びかけ）
3. 分類結果を表で見せて、オーナーの了承を得てから記録する（1件につき1回）：
   `npm run research:competitors -- add --account @… --url … --format … --slides … --theme "…" --category … --structure "…" --headline-pattern "…" --hook "…" --cta "…" --posted YYYY-MM-DD --entered-by claude`
4. 記録後に `npm run research:competitors -- summary` で集計を更新し、目立つ傾向を1〜2行で伝える。
5. 使い方の注意：競合の文言・画像・レイアウトを真似しない。テーマや構成の傾向を知るためだけに使い、このアカウントの世界観（A案／B案）は変えない。
   キャプション本文は記録しない（貼られた本文は分類にだけ使う）。
