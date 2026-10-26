# Note Media OS

noteで知的な有料記事（基本500円）を継続的に制作・販売するための、編集・制作・分析システム。Claude Code は企画から投稿用データの出力までを担当する。**公開の判断と公開作業は人間が行う。**

## 最重要ルール

1. **記事を公開しない。** note への投稿・予約投稿・非公式APIの利用・ブラウザ自動操作による投稿は、一切行わない。投稿用ファイルを `articles/ready_to_publish/` に出力し、人間の承認を求めて止まる。
2. **承認と公開の記録は、人間のコマンドでしか行わない。** `article_state.py approve` / `published` は、オーナーが `/approve-article` / `/mark-published` を実行したときだけ使う。記事の status を `approved` や `published` に手で書き換えない。
3. **存在しない情報を作らない。** 論文・引用・著者・出版情報・数値・URLを捏造しない。確認していないことを確認済みとして扱わない。取得できなかったデータは「取得不能」「未確認」と書き、推測で補わない。
4. **事実と推測を区別する。** 事実・学説・仮説・筆者の考察を書き分け、主要な主張には確度ラベルを付ける（`config/editorial_policy.md` §2）。
5. **販売実績がない段階で、成功パターンを断定しない。**
6. **重要な仕様は勝手に決めない。** ジャンル選定（`genres/selected/top5.md`）、ブランド（`brand/`）、価格方針、有料ツールの追加は、オーナーの承認を得てから変更する。
7. **秘密情報をリポジトリに書かない。** APIキー・パスワード・note のログイン情報・Cookie を扱わない。
8. サイトの利用規約とアクセス制限を守る。スクレイピングや制限回避をしない。
9. **ブラウザ自動化は閲覧だけ。** Playwright MCP では、購入・スキ・フォロー・コメント・投稿をしない。パスワードを入力しない。Cookie やストレージの値を読まない。Arc に接続しない。詳細は `docs/browser-automation.md` と `/note-browse`。

## 作業の前に読むもの

| 工程 | 読むファイル |
|---|---|
| すべて | `config/settings.md`、`config/editorial_policy.md` |
| 市場調査・ジャンル分析 | `prompts/market_research.md`、`prompts/genre_analysis.md`、`market-research-report.md` |
| 企画 | `prompts/ideation.md`、`genres/selected/top5.md` |
| リサーチ | `prompts/research.md` |
| 構成・執筆 | `prompts/writing.md` |
| 編集・評価 | `prompts/editing.md`、`prompts/fact_check.md` |
| 投稿用出力 | `prompts/note_export.md` |

## コマンド（`.claude/skills/`）

| コマンド | 内容 |
|---|---|
| `/market-research` | 市場調査（STEP 1） |
| `/genre-analysis` | ジャンルの評価と選定（STEP 2） |
| `/article-ideas` | 記事企画の作成（STEP 3） |
| `/write-article <企画ID or テーマ>` | 指定テーマの記事制作（STEP 4〜12） |
| `/auto-create` | テーマ選定から記事完成まで一括実行（STEP 3〜12、1本） |
| `/review-article <slug>` | 既存記事の評価・修正 |
| `/fact-check <slug>` | 事実関係と出典の検証 |
| `/analytics` | 販売実績の分析 |
| `/next-article` | 次に作る記事の提案 |
| `/note-browse test\|article\|search\|login` | Playwright MCP で note の公開ページを閲覧・記録 |
| `/approve-article <slug>` | **オーナー専用**：公開の承認 |
| `/mark-published <slug> <URL>` | **オーナー専用**：公開済みの記録 |

## サブエージェント（`.claude/agents/`）

`researcher`、`writer`、`editor-logic`（A）、`editor-factcheck`（B）、`editor-reader`（C）、`editor-originality`（D）。編集者は記事を書き換えず、指摘と採点だけを返す。

## 記事のライフサイクル

```
ideas.csv (backlog)
  → register → draft（articles/research, outlines, drafts）
  → in_review（articles/review）
  → [export_note.py] awaiting_approval（articles/ready_to_publish）
  → [オーナー /approve-article] approved
  → [オーナーが note で手動公開 → /mark-published] published（articles/published/<slug>/）
```

`needs_human`：品質基準を満たさない、または文献が不足している。人間の判断を待つ。

## ブラウザ自動化（Playwright MCP）

`.mcp.json` で `playwright` サーバーを登録している（自動化専用の Chromium と、専用プロファイル `.browser-profile/`）。note の実ページを見るときは `/note-browse` の手順に従う。取得した記事情報は `research/note-pages/`、エラーは `research/browser/errors.csv` に記録する。

## データの置き場所

| データ | 場所 | 形式 |
|---|---|---|
| 記事企画 | `ideas/backlog/ideas.csv` | CSV（`scripts/ideas.py` で採点） |
| 記事の台帳 | `articles/index.csv` | CSV（`scripts/article_state.py` で更新） |
| 販売実績 | `analytics/sales/sales.csv` | CSV（人間が手入力） |
| レポート | `analytics/reports/` | Markdown / CSV |

CSV は Python の csv モジュールで読み書きする。カンマを含む値はダブルクォートで囲む。

## スクリプト（標準ライブラリのみ。`note-media-os/` で実行）

- `python3 scripts/ideas.py score | top [N] [GENRE] | dup "<タイトル>" | next [N]`
- `python3 scripts/article_state.py register | status | score | minutes | list`
- `python3 scripts/check_article.py <draft> [--final]`
- `python3 scripts/export_note.py <draft>`
- `python3 scripts/analytics.py`

## 利用量への配慮

Proプランには利用上限がある。`/auto-create` は1回1本にとどめる。上限が近いときは、`config/settings.md` のレビューモードを `light` にする。大量の記事をまとめて作らない。
