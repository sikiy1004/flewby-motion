# agents/

サブエージェントの定義は、Claude Code の仕様に合わせて `.claude/agents/` に置いている。このフォルダは案内用。

| エージェント | 役割 | 使う工程 |
|---|---|---|
| `researcher` | 文献・情報収集、市場調査の情報収集 | STEP 1, 5 |
| `writer` | 構成・執筆・書き直し | STEP 6, 7, 9 |
| `editor-logic` | Editor A：論理性 | STEP 9, 11 |
| `editor-factcheck` | Editor B：ファクトチェック | STEP 8, 11 |
| `editor-reader` | Editor C：読者視点 | STEP 9, 11 |
| `editor-originality` | Editor D：独自性 | STEP 9, 11 |

各エージェントの詳しい手順は `prompts/` にある。手順を変えたいときは `prompts/` を編集する（エージェント定義は、どの手順書を読むかだけを指定している）。

編集者（editor-*）には、記事を書き換える権限を与えていない（Read / Grep / Glob と、Editor B だけ Web 検索）。指摘と採点だけを返し、修正はメインのセッションと `writer` が行う。
