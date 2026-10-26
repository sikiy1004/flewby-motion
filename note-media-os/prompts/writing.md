# 構成・執筆プロンプト

STEP 6（記事構成）と STEP 7（記事執筆）の手順書。`writer` サブエージェントが使う。

## 入力

- `articles/research/<slug>.md`（リサーチレポート。**ここに載っている確認済みの文献だけを使う**）
- `config/editorial_policy.md`（全体）
- 企画（`ideas.csv` の該当行）

## STEP 6：構成

`articles/outlines/<slug>.md` に書く。

```markdown
---
slug: <slug>
title_candidates:
  - <案1>
  - <案2>
  - <案3>
title_type: question | verify | classic | concept
---
# 構成：<slug>

## 中心の問い（1文）
## 読者が読み終えたときに得ている「新しい見方」（1〜2文）
## 掛け合わせる分野
## 章立て
| 章 | 見出し | 役割（導入／問題提起／背景／本論／根拠／独自考察／現代との接続／結論） | 使う文献（リサーチの#） | 無料/有料 |
## 有料ラインの位置と理由
## 有料部分で得られるもの（無料部分の末尾で読者に示す内容）
```

構成は基本形（編集方針 §5）から始め、テーマに合わせて変えてよい。変えた場合は理由を一行書く。

## STEP 7：執筆

`articles/drafts/<slug>.md` に書く。書き直すときは同じファイルを上書きし、front matter の `version` を1つ上げる。古い版は `articles/drafts/<slug>.v<N>.md` に退避する。

### ファイル形式

```markdown
---
slug: <slug>
idea_id: <idea_id>
genre_id: <genre_id>
genre_status: provisional | approved
title: <タイトル>
title_type: question | verify | classic | concept
price_yen: 500
status: draft
version: 1
created: YYYY-MM-DD
updated: YYYY-MM-DD
quality_score:
approved_by:
approved_at:
---

# <タイトル>

（無料部分）

<!-- PAYWALL -->

（有料部分）

## 確度の一覧

| 主張 | 確度 | 根拠 |
|---|---|---|

## 参考文献

1. 著者（年）「タイトル」『媒体』巻(号), ページ. DOI または URL（閲覧日：YYYY-MM-DD）
```

### 書き方

- 編集方針 §4 の「目指す文章」と「禁止事項」を守る。
- 導入では、具体的な場面・事例・小さな謎から入る。定型の挨拶や「〜について解説します」で始めない。
- 本文の主張には、根拠の文献番号を `［1］` の形で付ける。
- 研究を紹介するときは、方法・対象・規模・限界を、文脈上必要な範囲で一文以内に添える。
- 「筆者の考察」は、そうとわかる言い方で書く（例：「ここからは筆者の見立てである」）。
- 確認済みの文献にない事実を書かない。書きたい事実の根拠がなければ、リサーチに戻るか、その記述を削る。
- 原文を確認していない文章を、引用符で囲んで引用しない。
- 無料部分の末尾に、有料部分で何がわかるかを示す。目次の形で具体的に書き、煽らない。
- 長さは内容に従う。水増しをしない。

### 執筆後の自己点検

`python3 scripts/check_article.py articles/drafts/<slug>.md` を実行し、エラーを直してから編集工程に渡す。
