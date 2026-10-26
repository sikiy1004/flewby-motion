# Note Media OS — AI Editorial & Growth System

noteで、知的で独自性のある有料記事（基本500円）を継続的に制作し、販売実績から改善していくためのシステム。Claude Code（Proプラン）で動き、外部の有料サービスは使わない。

- 企画・リサーチ・執筆・編集・投稿用データの出力：Claude Code が自動で進める
- 公開の承認と、noteへの公開作業：**人間が行う**

## はじめに

```bash
cd note-media-os
claude
```

Claude Code は、このフォルダの `CLAUDE.md`、`.claude/skills/`（コマンド）、`.claude/agents/`（サブエージェント）を読み込む。

### 初回にやること

1. `market-research-report.md` を読む（Phase 1 の調査結果）。
2. `genres/selected/top5.md` の選定ジャンルを確認し、問題なければ status を `approved` に変える。
3. `brand/brand_proposal.md` からメディア名・筆名・AI利用の開示方針を決め、`config/settings.md` の「オーナー」欄に記入する。
4. （任意）`config/claude-settings.example.json` を `.claude/settings.json` にコピーする。
   - よく使うスクリプトの実行が、許可なしで通るようになる。
   - 承認・公開の記録を実行する前には、必ず確認が入るようになる。

## 日常の使い方

| やりたいこと | コマンド |
|---|---|
| 次の1本を作る | `/auto-create` |
| 作るテーマを自分で決める | `/write-article I-G05-01` または `/write-article 「テーマ」` |
| 何を作るべきか相談する | `/next-article` |
| 記事を承認する | `articles/ready_to_publish/<slug>.publish.md` を確認してから `/approve-article <slug>` |
| 公開を記録する | noteで公開した後に `/mark-published <slug> <URL>` |
| 売上を入力・分析する | `/analytics 2026-11 i-g05-01 views=420 purchases=9` → `/analytics` |
| 記事を見直す | `/review-article <slug>`、`/fact-check <slug>` |
| 市場を調べ直す | `/market-research` → `/genre-analysis`（3か月ごとが目安） |
| note の実ページを見る | `/note-browse search 哲学`、`/note-browse article <URL>`（導入は `docs/browser-automation.md`） |
| 企画を補充する | `/article-ideas G05 10` |

## ワークフロー（STEP 1〜12）

| STEP | 内容 | 担当 | コマンド |
|---|---|---|---|
| 1 | 市場調査 | researcher | `/market-research` |
| 2 | ジャンル分析 | メイン | `/genre-analysis` |
| 3 | 記事企画 | メイン | `/article-ideas` |
| 4 | テーマ選定 | メイン（`ideas.py next`） | `/auto-create`、`/next-article` |
| 5 | 文献・情報収集 | researcher | `/write-article` 内 |
| 6 | 記事構成 | writer | 〃 |
| 7 | 記事執筆 | writer | 〃 |
| 8 | ファクトチェック | editor-factcheck | 〃、`/fact-check` |
| 9 | 編集・校正 | editor-logic / reader / originality → writer | 〃、`/review-article` |
| 10 | 無料部分と有料部分の分割 | `check_article.py` | 〃 |
| 11 | 最終品質評価（100点、合格80点） | メイン | 〃 |
| 12 | note投稿用データの出力 | `export_note.py` | 〃 |
| — | **承認** | **人間** | `/approve-article` |
| — | **公開** | **人間（noteで手動）** | `/mark-published` |

## フォルダ構成

```
note-media-os/
├── CLAUDE.md                  Claude Code への指示（最重要ルール）
├── README.md
├── market-research-report.md  Phase 1 の成果物
├── config/
│   ├── settings.md            目標・品質基準・レビューモード・利用ツール
│   ├── editorial_policy.md    編集方針（確度ラベル・禁止表現・無料/有料の設計）
│   └── claude-settings.example.json  権限設定の例
├── brand/brand_proposal.md    メディアブランド案（承認待ち）
├── research/{market,competitors,trends,literature}/
├── genres/{candidates,selected}/
├── ideas/{backlog,approved}/  ideas.csv が企画のバックログ
├── articles/
│   ├── index.csv              記事の台帳
│   ├── research/ outlines/ drafts/ review/
│   ├── ready_to_publish/      承認待ちの投稿用ファイル
│   └── published/<slug>/      公開済み
├── analytics/{sales,reports}/ sales.csv に実績を手入力
├── docs/browser-automation.md  Playwright MCP の導入・運用
├── .mcp.json                  Playwright MCP の登録（プロジェクト単位）
├── prompts/                   各工程の手順書（人間が編集してよい）
├── agents/README.md           サブエージェントの説明
├── scripts/                   採点・状態管理・品質チェック・出力・分析（Python標準ライブラリ）
└── .claude/{skills,agents}/   Claude Code のコマンドとサブエージェント
```

## 販売実績の入力

`analytics/sales/sales.csv` に、月ごと・記事ごとに1行ずつ入力する。noteのダッシュボードの値を転記する。

```csv
period,slug,views,purchases,revenue_yen,likes,comments,reaction_notes
2026-11,i-g05-01,420,9,4500,31,2,"再現性の話が面白いというコメント"
```

`revenue_yen` が空欄なら、購入数×価格で計算する。

## 設計上の判断

- **note への自動投稿はしない。** 2026-10-26 時点の調査では、公式の投稿APIを確認できなかった。非公式APIやブラウザ自動操作は、規約上の位置づけが不明。
- **承認の二重化**：
  - 承認・公開記録のコマンドは、モデルが自分では呼び出せない設定にしている（`disable-model-invocation`）。
  - スクリプト側でも状態遷移を検査し、承認なしでは公開済みにできないようにしている。
- **編集者は読み取り専用**：4人の編集者サブエージェントは、記事を書き換えられない。
- **データはすべて Markdown と CSV**：人間がいつでも直接編集できる。
- **重複防止**：企画・記事のタイトル類似度（`ideas.py dup`）と、Editor D の内容比較の二段で防ぐ。

## 既知の制約

- Phase 1 の調査時、実行環境のネットワーク設定で `note.com` への直接アクセスが遮断されていた。競合アカウントの指標や検索ボリュームは取得できていない（`market-research-report.md` §1.2）。
- noteエディタへの Markdown 貼り付けの挙動は未確認。初回の公開時に確認し、`prompts/note_export.md` の公開手順を更新すること。
