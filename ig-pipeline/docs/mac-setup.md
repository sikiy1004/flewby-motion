# Mac での始め方（初回だけ・約30〜40分）

コマンドは「ターミナル」に1行ずつ貼り付けて Enter を押します。
`$` などの記号は付けずに、枠の中をそのままコピーしてください。

---

## ステップ0：ターミナルを開く

1. `⌘ command` + `スペース` を押して Spotlight を開く
2. 「ターミナル」と入力して Enter

黒か白の画面が出たら準備完了です。以降のコマンドはすべてここに貼り付けます。

---

## ステップ1：必要な道具を入れる（初回だけ）

### 1-1. Homebrew（Mac 用のインストール管理ツール）

まず、すでに入っているか確認します。

```bash
brew --version
```

- `Homebrew 4.x.x` のように表示された → 1-2 へ進む
- `command not found` と表示された → 次のコマンドで入れる

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- 途中で Mac のログインパスワードを聞かれたら入力します（入力しても画面には何も表示されませんが、入力はされています）。
- 最後に「Next steps」として2〜3行のコマンドが表示されたら、それも順番に貼り付けて実行します。
- 終わったら、ターミナルを一度閉じて開き直します。

### 1-2. git・Node.js・Python・GitHub CLI

```bash
brew install git node python gh
```

入ったか確認します（それぞれバージョン番号が出れば OK）。

```bash
node -v && python3 --version && gh --version
```

### 1-3. Claude Code

```bash
npm install -g @anthropic-ai/claude-code
```

```bash
claude --version
```

バージョン番号が出れば OK です。

---

## ステップ2：GitHub にログインして、プロジェクトを取得する

### 2-1. GitHub にログイン

```bash
gh auth login
```

質問には、次のように答えます（矢印キーで選んで Enter）。

| 質問 | 選ぶもの |
|---|---|
| Where do you use GitHub? | **GitHub.com** |
| What is your preferred protocol? | **HTTPS** |
| Authenticate Git with your GitHub credentials? | **Yes** |
| How would you like to authenticate? | **Login with a web browser** |

1. 画面に8桁のコード（例：`ABCD-1234`）が表示されるので、メモします。
2. Enter を押すとブラウザが開くので、コードを入力して「Authorize」を押します。
3. ターミナルに「Logged in as …」と出れば完了です。

### 2-2. プロジェクトを取得

保存場所は「書類」フォルダにします。

```bash
cd ~/Documents
```

```bash
gh repo clone sikiy1004/flewby-motion
```

```bash
cd flewby-motion && git checkout claude/vibrant-ritchie-8coc7l
```

`Switched to branch …` と出れば OK です。

---

## ステップ3：プロジェクトのセットアップ（初回だけ・5〜10分）

```bash
cd ~/Documents/flewby-motion/ig-pipeline
```

```bash
npm install
```

```bash
npx playwright install chromium
```

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

### 動作確認（サンプル画像を作る）

```bash
npm run all
```

- 初回は、背景除去用の AI モデル（約1GB）をダウンロードするので、数分かかります。
- 終わったら、次のコマンドで出力フォルダを開きます。

```bash
open out
```

`post-01-morning` などのフォルダに画像ができていれば成功です。

### Adobe Fonts が使われているか確認（任意）

先に Creative Cloud アプリの「フォント」で、**Cormorant Garamond・貂明朝・源ノ角ゴシック**をアクティベートしておきます。そのうえで次を実行します。

```bash
npm run build -- data/posts/post-01-morning.json --only cover --fonts
```

表示の中に `Ten Mincho` があれば、Adobe Fonts で描画されています（`Zen Old Mincho` なら代替フォントです）。

---

## ステップ4：楽天のキーを `.env` に入れる

楽天ウェブサービスでアプリ登録をして、**アプリID**と**アクセスキー**を取得してから行います。

1. 空のファイルを作って、テキストエディットで開きます。

```bash
touch .env && open -e .env
```

2. 開いた画面に次の4行を書き、`=` の右側に自分の値を入れます（前後に空白や引用符は付けません）。

```
RAKUTEN_APP_ID=ここにアプリID
RAKUTEN_ACCESS_KEY=ここにアクセスキー（pk_で始まる）
RAKUTEN_REFERER=アプリ登録で入力したサイトのURL
RAKUTEN_AFFILIATE_ID=ここにアフィリエイトID
```

3. `⌘ command` + `S` で保存して閉じます。

- `.env` はファイル名が「.」で始まるため、Finder では表示されません（`⌘ command` + `shift` + `.` で表示を切り替えられます）。
- このファイルは GitHub には上がらない設定にします。**キーをチャットや他の場所に貼らないでください。**

---

## ステップ5：Claude Code を起動して、リサーチ層の作業を始める

```bash
cd ~/Documents/flewby-motion/ig-pipeline && claude
```

- 初回は、Anthropic のアカウントでのログインを求められます。画面の案内どおりにブラウザでログインします。
- 「このフォルダを信頼しますか」と聞かれたら **Yes** を選びます。

起動したら、次の文をそのまま送ります。

```
docs/research-layer-plan.md を読んで、「Mac で最初にやること」の 1 から進めてください。各ステップの終わりに確認を取ってください。
```

以降は、Claude Code が公式仕様を確認し、最小実装からサンプルのリサーチまで、ステップごとに確認を取りながら進めます。

---

## 2回目以降の始め方

```bash
cd ~/Documents/flewby-motion/ig-pipeline && git pull && claude
```

## うまくいかないとき

| 症状 | 対処 |
|---|---|
| `command not found: brew` | ステップ1-1 の最後に表示された「Next steps」のコマンドを実行してから、ターミナルを開き直す |
| `gh repo clone` で「not found」 | `gh auth login` を、リポジトリの持ち主（sikiy1004）の GitHub アカウントでやり直す |
| `npm run all` が背景除去の途中で止まる | ほかのアプリを閉じてから、もう一度実行する（メモリが足りないと、軽いモデルに自動で切り替わります） |
| 何かのエラーで止まった | エラーの文章をコピーして、Claude Code に「このエラーを直して」と送る |
