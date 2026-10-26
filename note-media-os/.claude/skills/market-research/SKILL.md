---
name: market-research
description: noteの市場調査（STEP 1）を行う。人気記事・有料記事・価格帯・競合・書籍・SNSの動向を調べ、research/market/ に記録する。ジャンル選定の見直しや、3か月ごとの定期調査で使う。
argument-hint: "[調査の焦点（任意。例：G05の競合）]"
---

# /market-research

焦点：$ARGUMENTS（空なら全体調査）

1. `config/settings.md`、`prompts/market_research.md`、`market-research-report.md`、`research/market/` の最新ファイルを読む。
2. 調査項目ごとの方法と、使えるツールを確認する。WebSearch / WebFetch で `note.com` などにアクセスできない場合は、その事実を記録して先に進む。推測で補わない。
3. 情報収集は `researcher` サブエージェントに任せる。プロンプトには、焦点、`prompts/market_research.md` に従うこと、記録先のファイル名（`research/market/<今日の日付>_market-survey.md`）を含める。焦点が競合の場合は、記録先を `research/competitors/<genre_id>.md` にする。
4. 戻ってきたレポートを読み、前回調査からの変化（新しい成長ジャンル、価格帯の変化、新しい競合）を3〜5行にまとめる。
5. 結果に応じて、次の行動を提案する（例：「/genre-analysis で再評価する」）。ジャンル選定は変更しない。
