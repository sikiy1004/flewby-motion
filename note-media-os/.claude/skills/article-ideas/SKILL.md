---
name: article-ideas
description: 選定ジャンルの記事企画を作り、採点して ideas/backlog/ideas.csv に追加する（STEP 3）。バックログが減ったときや、新しいジャンルを追加したときに使う。
argument-hint: "[genre_id（省略時は全選定ジャンル）] [本数（既定20）]"
---

# /article-ideas

引数：$ARGUMENTS

1. `prompts/ideation.md` の手順に従う。
2. 対象ジャンルを決める。引数に genre_id があればそのジャンル、なければ `genres/selected/top5.md` の全ジャンル。本数の既定は1ジャンルあたり20本。
3. 既存の企画（`ideas/backlog/ideas.csv`）と記事（`articles/index.csv`）を読み、重複を避ける。各タイトルで `python3 scripts/ideas.py dup "<タイトル>"` を実行する。
4. `ideas.csv` に行を追記する。CSVの列順を守り、カンマを含む値はダブルクォートで囲む。
5. `python3 scripts/ideas.py score` を実行する。続いて `python3 scripts/ideas.py top 10 <genre_id>` を実行し、上位を報告する。
