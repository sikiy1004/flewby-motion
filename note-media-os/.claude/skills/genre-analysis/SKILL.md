---
name: genre-analysis
description: ニッチジャンルを20以上挙げて100点満点で評価し、上位5ジャンルを選ぶ（STEP 2）。市場調査の後や、販売実績が溜まった後の見直しで使う。
argument-hint: "[追加で検討したいジャンル（任意）]"
---

# /genre-analysis

追加で検討するジャンル：$ARGUMENTS

1. `prompts/genre_analysis.md` の手順に従う。
2. 入力として、`research/market/` の最新調査、`genres/candidates/` の最新CSV、`analytics/reports/latest_genre_stats.csv`（あれば）を読む。
3. 点数の根拠を必ず書く。取得できていないデータは「推定」と明記する。
4. 出力：`genres/candidates/genre_scores_<今日の日付>.csv` と `genres/candidates/genre_analysis_<今日の日付>.md`。
5. 上位5ジャンルが `genres/selected/top5.md` と異なる場合は、差分と理由をオーナーに示して承認を求める。**承認されるまで `top5.md` を書き換えない。**
