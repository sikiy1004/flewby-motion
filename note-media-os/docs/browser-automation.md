# ブラウザ自動化（Playwright MCP）

Claude Code から note.com の公開ページを閲覧・記録するための設定。Microsoft 公式の Playwright MCP（`@playwright/mcp`）を使う。

## 方針

| 項目 | 方針 |
|---|---|
| 自動化に使うブラウザ | Playwright 専用の Chromium（`browserName: chromium`）。Arc や普段の Chrome は使わない |
| プロファイル | 自動化専用の永続プロファイル `note-media-os/.browser-profile/note-automation/`（git 管理外） |
| Arc | 分離する。Arc のプロファイル・Cookie・履歴は読まない。CDP 接続は「可否の確認」だけにとどめ、接続はしない |
| note のログイン | 必要なときだけ、自動化用ウィンドウで人間が手動ログインする。ログイン状態は自動化専用プロファイルに保存される |
| 認証情報 | ソースコード・設定ファイル・ログに保存しない。Claude はパスワードを入力しない。Cookie の値を読まない |
| 操作の範囲 | 閲覧だけ。購入・スキ・フォロー・コメント・投稿はしない |
| 負荷 | ページ間3秒以上、1回30ページ以下。robots.txt を確認する |

## 構成ファイル

| ファイル | 役割 |
|---|---|
| `.mcp.json` | Claude Code にプロジェクト単位で MCP サーバーを登録する。`@playwright/mcp@0.0.83` に固定 |
| `config/playwright-mcp.json` | Playwright MCP の設定：Chromium、専用プロファイル、ウィンドウ表示（headless: false）、出力先 |
| `scripts/browser/extract_note_article.js` | 記事ページからタイトル・著者・公開日・本文（公開部分）などを取り出す関数 |
| `scripts/note_pages.py` | 取り出した情報の保存（Markdown・CSV）、エラーとログイン状態の記録 |
| `scripts/browser/check_arc_cdp.sh` | Arc の CDP エンドポイントが応答するかだけを確認する |
| `.claude/skills/note-browse/` | `/note-browse` コマンド |

保存先：

| データ | 場所 | git |
|---|---|---|
| 記事の一覧 | `research/note-pages/index.csv` | 管理する |
| 記事ごとのメタデータと冒頭の抜粋 | `research/note-pages/<id>.md` | 管理する |
| 記事本文の全文（`--keep-body` のときだけ） | `research/note-pages/raw/` | **管理しない** |
| エラー記録 | `research/browser/errors.csv` | 管理する |
| ログイン状態の記録（状態と根拠だけ） | `research/browser/login_status.csv` | 管理する |
| スナップショット等の生の出力 | `research/browser/output/` | **管理しない** |
| ブラウザのプロファイル（Cookie を含む） | `.browser-profile/` | **管理しない** |

## 導入（Mac で行う）

この自動化は、**ウィンドウを表示して人間が手動ログインできる環境**、つまりあなたの Mac で動かす前提。クラウドのセッションには画面がなく、手動ログインができない。

1. Node.js 18 以上を確認する。
   ```bash
   node -v
   ```
   入っていなければ https://nodejs.org/ から LTS 版を入れる。
2. リポジトリを Mac に取得して、`note-media-os` に移動する。
3. Playwright 専用の Chromium を入れる。`@playwright/mcp@0.0.83` が使う Playwright と同じ版を入れること。
   ```bash
   npx -y playwright@1.64.0-alpha-1790635538000 install chromium
   ```
   ※ 版がずれると「Executable doesn't exist」というエラーになる。そのときは、エラー文に表示されるコマンドで入れ直す。
4. Claude Code を起動する。
   ```bash
   claude
   ```
   初回は `.mcp.json` の `playwright` サーバーを使ってよいか確認されるので、承認する。`/mcp` で `playwright` が connected になっていることを確認する。
5. 初期テストを実行する。
   ```
   /note-browse test
   ```
   Chromium のウィンドウが開く。ログインを頼まれたら、そのウィンドウで手動ログインする。

### プロジェクト単位でなく、自分の環境全体に登録したい場合

```bash
claude mcp add playwright -s user -- npx -y @playwright/mcp@0.0.83 --config "$(pwd)/config/playwright-mcp.json"
```

この場合、`config/playwright-mcp.json` の `userDataDir` と `outputDir` は絶対パスに書き換える（相対パスは、Claude Code を起動したフォルダ基準になる）。

## ログイン状態の管理

- ログインは自動化用 Chromium のウィンドウで、人間が手動で行う。
- ログイン状態（Cookie）は `.browser-profile/note-automation/` に保存され、Claude Code を再起動しても残る（永続プロファイル）。
- **ログアウトしたいとき・プロファイルを捨てたいとき**：Claude Code を終了してから `.browser-profile/note-automation/` を削除する。
- このフォルダは同時に1つのブラウザしか使えない。Claude Code を2つ同時に開くとエラーになる。
- ログインの要否：公開記事・検索の閲覧にログインは不要とみられる（未確認）。自分の記事の管理画面（売上やビュー数）を見る用途が出てきたら、改めて方針を決める。

## Arc への CDP 接続について

- Arc は Chromium 系なので、`--remote-debugging-port` を付けて起動すれば CDP で接続できる可能性がある。ただし未検証。Chromium 系ブラウザの新しい版では、既定のプロファイルでのリモートデバッグが制限されている。
- 確認したい場合は `sh scripts/browser/check_arc_cdp.sh` を使う（手順はスクリプト冒頭）。このスクリプトは応答の有無とバージョンを見るだけで、接続はしない。
- **このプロジェクトでは Arc に接続しない。** 接続すると、Arc でログインしている全サイトの Cookie を自動化から操作できる状態になり、「Arc の既存プロファイルや Cookie を無断で読み取らない」という方針と両立しないため。

## エラーと対処

| 症状 | 主な原因 | 対処 |
|---|---|---|
| `Executable doesn't exist` | Chromium が未導入、または版のずれ | 導入の手順3を、エラー文に表示された版で再実行 |
| `ERR_TUNNEL_CONNECTION_FAILED`、`ERR_NAME_NOT_RESOLVED` | ネットワークが note.com への接続を許していない | 回線・プロキシを確認する。クラウドのセッションでは、環境のネットワーク設定に note.com を追加する必要がある |
| プロファイルが使用中（ProcessSingleton など） | Claude Code を2つ同時に開いている、または前回のブラウザが残っている | 片方を閉じる。残っている Chromium を終了する |
| 本文が空 | note 側のページ構造が変わった | `/note-browse article` が snapshot を確認し、`extract_note_article.js` の修正案を出す |
| ログイン後もログアウト扱い | 別のプロファイルで起動している | `config/playwright-mcp.json` の `userDataDir` を確認する |

エラーは `research/browser/errors.csv` に記録する（日時、工程、URL、エラー内容、推定原因、次の対応）。

## 動作確認の記録（2026-10-26、クラウドのセッション）

| 項目 | 結果 |
|---|---|
| Node.js | v22.22.0 |
| `@playwright/mcp` | 0.0.83（Playwright 1.64.0-alpha）。stdio で起動し、MCP として応答。ツール数25 |
| Chromium の起動と操作 | 成功（headless。コンテナに入っていた Chromium を `executablePath` で指定） |
| 記事ページからの抽出と保存 | 成功（note 形式を模したローカルのテストページで確認：タイトル・著者・公開日・本文・価格表示・有料表示を取得し、Markdown と CSV に保存） |
| 永続プロファイルでの Cookie の保持 | 成功（MCP を再起動しても Cookie が残る。隔離モードでは消えることも確認） |
| note.com への接続 | **失敗**：`net::ERR_TUNNEL_CONNECTION_FAILED`。クラウド環境のネットワーク設定で note.com が遮断されているため |
| エラー記録 | 上の失敗を `errors.csv` の形式で記録できることを確認 |
| 手動ログイン、ログインの保持 | **未実施**：画面のないクラウド環境では、手動ログインができない |
| Arc の CDP | **未実施**：Arc は Mac 上にあり、クラウドからは確認できない |

note.com での実地テスト（検索、実際の記事ページの抽出、ログイン）は、Mac で `/note-browse test` を実行して行う。`extract_note_article.js` のセレクタと、価格・有料判定の文言は推定なので、初回テストで当たり外れを確認すること。
