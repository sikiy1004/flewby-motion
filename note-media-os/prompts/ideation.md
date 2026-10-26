# 記事企画プロンプト

`/article-ideas` が使う手順書。

## 入力

- `genres/selected/top5.md`（対象ジャンル）
- `ideas/backlog/ideas.csv`（既存の企画。重複を避ける）
- `articles/index.csv`（制作済み・公開済みの記事）
- `analytics/reports/latest_genre_stats.csv`（あれば）
- `config/editorial_policy.md`

## 手順

1. 対象ジャンルごとに、新しい企画を作る（既定は1ジャンル20本。引数で本数を指定できる）。
2. 企画ごとに、次の列を埋める（`ideas.csv` の列順に従う）。

   | 列 | 内容 |
   |---|---|
   | id | `I-<genre_id>-<連番2桁>`。既存の最大番号の次から振る |
   | title | 煽らず、知的好奇心を刺激するタイトル（編集方針 §7） |
   | summary | 記事の概要（1〜2文） |
   | target_reader | 想定読者 |
   | reader_question | 読者が抱える疑問 |
   | reader_value | 記事で得られる価値 |
   | unique_angle | 独自の切り口（どの分野を掛け合わせるか） |
   | key_references | 必要な参考文献の候補（著者・年・媒体）。**この段階では未検証の候補であり、STEP 5で必ず実在を確認する。** 存在が疑わしいものは書かない |
   | paid_fit | 有料記事としての適性（高・中・低） |
   | price_yen | 想定価格（基本は500、無料記事は0） |
   | s_interest | 読者の関心（0〜20） |
   | s_originality | 独自性（0〜20） |
   | s_depth | 情報の深さ（0〜20） |
   | s_paid | 有料化の適性（0〜20） |
   | s_fit | メディアとの親和性（0〜10） |
   | s_series | 継続記事への展開性（0〜10） |
   | total / priority | 空欄でよい（スクリプトが計算する） |
   | status | `backlog` |

3. 重複を確認する。各タイトルについて `python3 scripts/ideas.py dup "<タイトル>"` を実行する。類似度0.6以上の既存企画・記事がある場合は、切り口が明確に違うときだけ残す。違いは `unique_angle` に書く。
4. `ideas.csv` に追記したあと、`python3 scripts/ideas.py score` を実行する。
5. 販売実績がある場合は、購入率の高いジャンル・タイトルの型を優先する。ただし公開本数が少ない段階では、成功パターンを断定しない。

## 品質の目安

- 各ジャンルに、メディアの方法論を示す無料記事を1〜2本入れる。
- 1ジャンルの企画が、同じ一つの論点の言い換えばかりにならないようにする。
- 実在する研究や古典に根拠を置けない企画は作らない。
