---
name: fact-check
description: 記事やテキストの事実関係と出典を検証する（STEP 8）。文献の実在、引用、数値、固有名詞、最新性を Web で確認し、結果を記録する。記事は書き換えない。
argument-hint: "<slug またはファイルパス>"
---

# /fact-check

対象：$ARGUMENTS

1. 引数が slug なら、`/review-article` と同じ順で記事ファイルを探す。ファイルパスなら、そのファイルを使う。
2. `editor-factcheck` サブエージェントに、対象ファイルのパスと `prompts/fact_check.md` に従うことを指示する。
3. 結果を `articles/review/<slug>.factcheck.md` に保存する。ファイルパスで指定された場合は `articles/review/<ファイル名>.factcheck.md`。冒頭に閲覧日を書く。
4. 「不一致」「未確認」の項目を、重大なものから順に報告する。記事は修正しない（修正は `/review-article` で行う）。
