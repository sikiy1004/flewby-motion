---
name: note-browse
description: Playwright MCP（自動化専用の Chromium）で note.com の公開ページを閲覧し、記事情報を research/note-pages/ に Markdown と CSV で保存する。初期テスト、記事の取得、検索結果の確認、ログイン状態の確認に使う。市場調査・競合調査で note の実ページを見るときもこれを使う。
argument-hint: "test | article <URL> | search <キーワード> | login"
---

# /note-browse

引数：$ARGUMENTS

Playwright MCP のツール（`browser_navigate`、`browser_snapshot`、`browser_evaluate`、`browser_wait_for` など）を使う。ツールが見つからなければ、`docs/browser-automation.md` の「導入」を案内して止まる。

## 守ること

- **閲覧だけをする。** 購入・スキ・フォロー・コメント・投稿・設定変更など、状態を変える操作をしない。該当するボタンを押さない。
- **ログイン情報を扱わない。** メールアドレスやパスワードを入力しない。ログインが必要なら、人間に手動ログインを頼む（下の「login」）。
- **Cookie やストレージの値を読まない・記録しない。** `browser_cookie_*`、`browser_localstorage_*`、`browser_sessionstorage_*`、`browser_storage_state` は使わない。ログイン状態は、画面の表示（ログインボタン、ユーザーメニュー）で判断する。
- **負荷をかけない。** ページを開く間隔を3秒以上あける（`browser_wait_for` の time で待つ）。1回の実行で開くページは30以下にする。
- 最初に `https://note.com/robots.txt` を開き、閲覧しようとしているパスが Disallow に当たらないか確認する。当たる場合は開かない。
- 有料部分を回避して読もうとしない。取得できるのは公開されている範囲だけ。
- 他人の記事の全文は、`--keep-body` を付けたときだけ `research/note-pages/raw/`（git 管理外）に保存する。既定ではメタデータと冒頭の抜粋だけを残す。
- エラーが起きたら、その場で記録する：`python3 scripts/note_pages.py error <step> <url> "<エラー内容>" "<推定原因>" "<次の対応>"`。推定原因がわからなければ「不明」と書く。

## article <URL>

1. `browser_navigate` で URL を開く。
2. `scripts/browser/extract_note_article.js` の全文を読み、`browser_evaluate` の `function` に渡す。`filename` は `research/browser/output/extract-<日時>.json`。
3. `python3 scripts/note_pages.py save research/browser/output/extract-<日時>.json` で保存する。
4. 本文が空、またはタイトルが取れていなければ、`browser_snapshot` でページ構造を確認する。原因（セレクタのずれ、読み込み待ち、ログイン要求など）を errors.csv に記録する。セレクタのずれなら、`extract_note_article.js` の修正案を示す。

## search <キーワード>

1. `https://note.com/search?q=<URLエンコードしたキーワード>&context=note` を開く。URL の形式は未確認なので、開けなければトップページの検索欄を使う。
2. `browser_snapshot` で結果一覧を確認し、上位の記事（タイトル・URL・著者・価格表示があれば価格）を最大20件読み取る。
3. `research/competitors/` または `research/market/` に、日付付きの Markdown 表で保存する（検索語、閲覧日時、件数を冒頭に書く）。
4. 個々の記事を詳しく見る場合は、`article` の手順を3秒以上の間隔をあけて繰り返す。

## login

1. `https://note.com/` を開き、`browser_snapshot` でログイン状態を判定する。
2. ログインしていなければ、人間に次のように頼んで待つ。
   > 自動化用の Chromium ウィンドウで、note に手動でログインしてください（Arc ではなく、Playwright が開いたウィンドウです）。終わったら「ログインした」と返信してください。
3. 返信を受けたら、ページを再読み込みして判定し、`python3 scripts/note_pages.py login <logged_in|logged_out|unknown> "<判定の根拠>"` で記録する。根拠は画面の表示だけを書く（例：「ヘッダーにユーザーメニューが表示」）。
4. 保持の確認：人間に Claude Code の再起動を頼む（または `browser_close` のあと、もう一度ページを開く）。もう一度判定して記録する。

## test（初期テスト）

順に実行し、各手順の結果（成功／失敗、根拠）を最後に表にして報告する。失敗した手順は errors.csv に記録し、次の手順に進めるものは進める。

1. Playwright MCP が応答する（`browser_navigate` が実行できる）
2. `https://note.com/` を開く
3. トップページのタイトルと主要な見出しを `browser_snapshot` で取得する
4. `search 哲学` を実行する（保存は `research/browser/output/` に一時保存でよい）
5. 検索結果の1件目で `article` を実行する
6. `login` の手順1〜3（ログインが不要な範囲で閲覧できるなら、ログインは任意と報告する）
7. `login` の手順4（保持の確認）

結果を `research/browser/initial_test_<日付>.md` に保存する。
