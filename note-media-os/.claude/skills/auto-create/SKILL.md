---
name: auto-create
description: 次に作るべき企画を自動で選び、リサーチから投稿用データの出力まで一括で制作する（STEP 3〜12）。1回の実行で1本だけ作り、公開前に必ず人間の承認を求める。
argument-hint: "[genre_id（任意。ジャンルを指定する場合）]"
---

# /auto-create

ジャンル指定：$ARGUMENTS

1. `config/settings.md` を読む。承認待ちの記事数が上限以上なら、制作せずに承認を促して終了する。
2. **市場調査の鮮度を確認する。** `research/market/` の最新ファイル、または `market-research-report.md` の作成日が90日以上前なら、「`/market-research` での再調査を推奨」と報告に書く（自動では実行しない）。
3. **企画の残量を確認する。** 対象ジャンルの `status=backlog` の企画が5本未満なら、`/article-ideas` の手順（`prompts/ideation.md`）で、そのジャンルの企画を10本追加する。
4. **テーマを選ぶ（STEP 4）。**
   - `python3 scripts/ideas.py next 5` を実行する（ジャンル指定があれば、出力のうち該当ジャンルを優先する）。
   - `genres/selected/top5.md` の初期配分と、`articles/index.csv` の既存記事のジャンル構成を比べる。配分より少ないジャンルの上位企画を優先する。
   - 同じジャンルの記事が直近3本続いている場合は、別のジャンルを選ぶ。
   - 選んだ理由を1〜2行で記録する。
5. 選んだ企画IDで、`.claude/skills/write-article/SKILL.md` の手順 0〜8 をすべて実行する。
6. 最後の報告に、テーマ選定の理由と、手順2の推奨（あれば）を加える。**公開はしない。**
