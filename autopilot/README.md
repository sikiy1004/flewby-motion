# autopilot — 美容家電アフィリエイト 全自動 SNS 運用システム

楽天ランキングの実データをもとに、**ネタ収集 → 台本 → カルーセル画像 / ショート動画 → Instagram（・TikTok）投稿 → 効果測定 → 学習** までを GitHub Actions の定期実行で無人で回すシステムです。ランニングコストは 0 円です。

- 戦略: [`../docs/strategy.md`](../docs/strategy.md)
- 設計: [`../docs/architecture.md`](../docs/architecture.md)
- デザインのリサーチと方針: [`../docs/design-research.md`](../docs/design-research.md)

あなたがやることは **最初のアカウント連携（2〜3 時間）** と **月 1 回の収益確認** だけです。

---

## 目次

1. [まず試す（APIキー不要のデモ）](#1-まず試すapiキー不要のデモ)
2. [本番セットアップ（チェックリスト）](#2-本番セットアップチェックリスト)
3. [試運転 → 本番開始](#3-試運転--本番開始)
4. [TikTok を追加する](#4-tiktok-を追加する)
5. [日々の運用](#5-日々の運用)
6. [カスタマイズ](#6-カスタマイズ)
7. [トラブルシューティング](#7-トラブルシューティング)
8. [自宅 PC / VPS で動かす場合](#8-自宅-pc--vps-で動かす場合)
9. [仕組み](#9-仕組み)
10. [注意事項](#10-注意事項)

---

## 1. まず試す（APIキー不要のデモ）

サンプルデータ（架空の商品 12 件）で「カルーセル 1 投稿分」と「ショート動画 1 本」を生成します。投稿は行いません（dry-run）。

### A. GitHub 上で試す（PC 不要）

1. このリポジトリの **Actions** タブ →「autopilot-demo」→ **Run workflow**
2. 10 分ほどで完了。実行結果ページ下部の **Artifacts → autopilot-demo** をダウンロード
3. 中身: `post_001/slide_*.jpg`（カルーセル）、`story.jpg`、`post_002/reel.mp4`（動画）、`caption_*.txt`、`public/index.html`（リンク集ページ）

### B. 手元で試す

必要なもの: Python 3.10+、FFmpeg、Node.js 18+（動画テンプレート）、（音声も確認するなら）Docker

```bash
cd autopilot
```

```bash
pip install -e ".[dev]"
```

```bash
python -m playwright install chromium
```

```bash
cd remotion && npm ci && cd ..
```

```bash
docker run -d --name voicevox -p 50021:50021 voicevox/voicevox_engine:cpu-0.26.2
```

```bash
autopilot demo --out output/demo
```

`output/demo/` にカルーセル画像・動画・キャプションが出力されます。VOICEVOX を起動していなければ、無音（字幕のみ）の動画になります。

テスト:

```bash
pytest -q
```

---

## 2. 本番セットアップ（チェックリスト）

上から順に進めれば OK です。取得した値は最後に GitHub の **Secrets / Variables** に登録します。

### 2-1. このリポジトリを Private にする（推奨）

Settings → General → Danger Zone → Change visibility → **Private**

- Private でも GitHub Actions の無料枠（月 2,000 分）に収まります（想定使用量 月 600〜750 分）。
- Public のままだと「60 日間リポジトリに動きがないと定期実行が自動停止する」仕様の影響を受けます。

### 2-2. 公開用リポジトリ（GitHub Pages）を作る

Instagram API は画像・動画を「インターネット上の URL」から取りに来るため、公開置き場が必要です。プロフィールに貼るリンク集ページもここで公開します。

1. GitHub で **新しい Public リポジトリ** を作成（例: `your-name/bikaden-links`）。「Add a README file」にチェック。
2. そのリポジトリの Settings → **Pages** → Source: `Deploy from a branch` / Branch: `main` / `/ (root)` → Save
3. 数分後、`https://your-name.github.io/bikaden-links/` が公開 URL になります（= `MEDIA_BASE_URL`）。
4. **アクセストークン（Fine-grained PAT）** を作成: GitHub 右上アイコン → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token
   - Repository access: **Only select repositories** → 上で作った公開用リポジトリだけ
   - Permissions → Repository permissions → **Contents: Read and write**
   - 有効期限は最長に設定し、期限前に作り直してください（期限切れは Discord に失敗通知が来ます）
   - 生成された値 = `MEDIA_REPO_TOKEN`

投稿に使った画像・動画は公開から 7 日後に自動で削除されます（リンク集ページは残ります）。

### 2-3. Instagram（必須）

1. Instagram アプリで、アカウントを **プロアカウント（クリエイター or ビジネス）** に切り替える
2. [Meta for Developers](https://developers.facebook.com/) でアプリを作成
   - ユースケース: **「Instagram API」（Instagram ログインを使う方式）**
3. アプリの「Instagram API」設定画面で、自分の Instagram アカウントを追加し、アクセストークンを生成
   - 必要な権限: `instagram_business_basic`、`instagram_business_content_publish`、`instagram_business_manage_insights`
   - 生成されるのは **長期トークン（約 60 日）**。以後はシステムが毎週自動で延長します
4. 値を控える: アクセストークン = `IG_ACCESS_TOKEN`（`IG_USER_ID` は空でも自動取得されます）

> 自分が管理するアカウントへ投稿するだけなら、通常はアプリ審査なしで使えます。Meta 側の画面・権限名は変わることがあるため、迷ったら公式ドキュメント「Instagram Platform → Content Publishing」を確認してください。
> Facebook ページ経由で連携した場合は、Variables の `IG_GRAPH_HOST` を `graph.facebook.com` にします。

### 2-4. 楽天（必須）

1. [楽天ウェブサービス](https://webservice.rakuten.co.jp/) にログイン → **アプリ ID 発行** → `RAKUTEN_APP_ID`
2. [楽天アフィリエイト](https://affiliate.rakuten.co.jp/) に登録 → 「アフィリエイト ID」を確認 → `RAKUTEN_AFFILIATE_ID`
   - これを設定すると、システムが取得する商品 URL が自動であなたのアフィリエイトリンクになります
3. （任意・推奨）[もしもアフィリエイト](https://af.moshimo.com/) に登録すると、楽天・Amazon の報酬を現金で受け取りやすくなります

### 2-5. Amazon・ASP（任意）

- Amazon アソシエイトのトラッキング ID（例 `yourid-22`）→ `AMAZON_ASSOCIATE_TAG`（リンク集ページに「Amazon で探す」ボタンが付きます）
- A8.net / afb / アクセストレード / バリューコマース などで **提携承認された案件だけ** を `config/offers.yaml` に書きます。書いた案件だけがリンク集ページに表示されます。

### 2-6. 文章生成 AI（任意・推奨）

キーが 1 つも無くても、人が書いた定型文で投稿は続きます。あると文章のバリエーションが増えます。

| サービス | 取得場所 | 登録名 |
|---|---|---|
| Google Gemini（無料枠） | Google AI Studio → Get API key | `GEMINI_API_KEY` |
| Groq（無料枠・予備） | console.groq.com → API Keys | `GROQ_API_KEY` |
| OpenRouter（無料モデル・予備） | openrouter.ai → Keys | `OPENROUTER_API_KEY` |

生成文は必ず「PR 表記・薬機法 NG ワード・データに無い数値・過去投稿との類似」の検査を通り、不合格なら次の AI → 定型文へ自動で切り替わります。

### 2-7. その他（任意）

| 用途 | 取得場所 | 登録名 |
|---|---|---|
| 冒頭シーンの背景動画 | pexels.com/api（無料） | `PEXELS_API_KEY` |
| 失敗通知・週次レポート | Discord のチャンネル設定 → 連携サービス → ウェブフック → URL をコピー | `DISCORD_WEBHOOK_URL` |

### 2-8. 暗号化キーを作る（必須）

自動更新されるトークンを暗号化して保存するためのキーです。手元で 1 回だけ実行:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

（`pip install -e .` 済みなら `autopilot keygen` でも可）→ `AUTOPILOT_SECRET_KEY`

### 2-9. GitHub に登録する

このリポジトリの Settings → **Secrets and variables → Actions**

**Secrets**（New repository secret）

| 名前 | 必須 | 内容 |
|---|---|---|
| `AUTOPILOT_SECRET_KEY` | ✅ | 2-8 で作ったキー |
| `RAKUTEN_APP_ID` | ✅ | 楽天アプリ ID |
| `RAKUTEN_AFFILIATE_ID` | ✅ | 楽天アフィリエイト ID |
| `IG_ACCESS_TOKEN` | ✅ | Instagram 長期トークン |
| `MEDIA_REPO_TOKEN` | ✅ | 2-2 の Fine-grained PAT |
| `IG_USER_ID` | | 空なら自動取得 |
| `AMAZON_ASSOCIATE_TAG` | | Amazon トラッキング ID |
| `GEMINI_API_KEY` / `GROQ_API_KEY` / `OPENROUTER_API_KEY` | | 文章生成 AI |
| `PEXELS_API_KEY` | | 素材動画 |
| `DISCORD_WEBHOOK_URL` | | 通知 |
| `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` / `TIKTOK_REFRESH_TOKEN` | | TikTok（4 章） |

**Variables**（Variables タブ → New repository variable）

| 名前 | 値の例 | 内容 |
|---|---|---|
| `AUTOPILOT_ENABLED` | `true` | **定期実行のオン/オフスイッチ**（`true` 以外なら何もしない） |
| `AUTOPILOT_DRY_RUN` | `true` → 後で `false` | `true` の間は生成・公開まで行い、SNS 投稿だけしない |
| `MEDIA_REPO` | `your-name/bikaden-links` | 2-2 の公開用リポジトリ |
| `MEDIA_BASE_URL` | `https://your-name.github.io/bikaden-links` | 2-2 の公開 URL |
| `TIKTOK_ENABLED` | `false` | TikTok 審査通過後に `true` |
| `IG_GRAPH_HOST` | （空） | Facebook ページ経由の場合のみ `graph.facebook.com` |

### 2-10. アカウント情報を書き換える

`autopilot/config/settings.yaml` の `account.name` / `account.handle` を自分のアカウントに変更してコミットします（画像のフッターとリンク集ページに表示されます）。

---

## 3. 試運転 → 本番開始

1. Variables を `AUTOPILOT_ENABLED=true`、`AUTOPILOT_DRY_RUN=true` にする
2. Actions →「autopilot-generate」→ **Run workflow**（初回は 10〜15 分）
3. 確認
   - `MEDIA_BASE_URL` を開き、リンク集ページに No.001〜 が並んでいるか、楽天ボタンのリンク先が正しいか
   - 失敗した場合は実行ログの末尾と、Artifacts の `autopilot-output` を確認
4. Actions →「autopilot-publish」→ Run workflow（slot に `carousel`）→ ログに dry-run の結果が出れば OK
5. **Instagram のプロフィールのリンク欄に `MEDIA_BASE_URL` を設定**
6. Variables の `AUTOPILOT_DRY_RUN` を `false` に変更 → **本番開始**

以後は何もしなくても、毎日次のスケジュールで動きます。

| 時刻（JST） | ワークフロー | 内容 |
|---|---|---|
| 03:07 | autopilot-generate | 楽天ランキング収集 → 2 日分の投稿を先行生成 → 公開 |
| 07:30 | autopilot-publish | ストーリーズ（前日のカルーセルを告知） |
| 12:15 | autopilot-publish | カルーセル投稿 |
| 19:00 | autopilot-publish | TikTok（有効時のみ） |
| 21:00 | autopilot-publish | リール投稿 |
| 23:37 | autopilot-maintain | インサイト取得・学習・トークン更新・掃除・週次レポート（月曜） |

GitHub Actions の定期実行は混雑時に数分〜十数分遅れることがあります（投稿時刻が多少ずれても問題ない設計です）。

**止めたいとき**は Variables の `AUTOPILOT_ENABLED` を `false` にするだけです。

---

## 4. TikTok を追加する

TikTok の投稿 API は、審査（audit）に通るまで「自分のみ閲覧可」の投稿しかできません。Instagram で運用を始めてから並行して申請するのがおすすめです。

1. TikTok アカウントをビジネスアカウントにする
2. [TikTok for Developers](https://developers.tiktok.com/) でアプリを作成し、**Login Kit** と **Content Posting API（Direct Post）** を追加
   - スコープ: `user.info.basic`、`video.publish`
3. OAuth で自分のアカウントを認可し、`refresh_token` を取得（有効期限約 1 年。以後はシステムが自動更新）
4. Secrets に `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` / `TIKTOK_REFRESH_TOKEN` を登録
5. Content Posting API の審査を申請（申請フォームでは「自社アカウントへの自動投稿」用途と説明）
6. 審査通過後、Variables の `TIKTOK_ENABLED` を `true` に

- 審査前に有効にした場合は、自動で「自分のみ（SELF_ONLY）」投稿になります。
- アフィリエイト投稿なので「ブランドコンテンツ」表示と「AI 生成コンテンツ」ラベルを自動で付けます（`config/settings.yaml` の `tiktok` で変更可）。
- TikTok のプロフィールリンクは、アカウントの種類やフォロワー数によって設定できない場合があります。その間は Instagram への誘導が中心になります。

---

## 5. 日々の運用

| 頻度 | やること |
|---|---|
| 毎日 | なし |
| 週 1 回 | Discord に届く週次レポートを眺める（任意） |
| 月 1 回 | 楽天アフィリエイト / もしも / ASP の管理画面で収益確認 |
| 失敗通知が来たとき | 通知の内容を確認（多くはトークン期限切れ・API 仕様変更） |
| 約 1 年ごと | `MEDIA_REPO_TOKEN`（PAT）の作り直し、TikTok の再認可 |

状態の確認（手元で）:

```bash
git fetch origin autopilot-state && git show FETCH_HEAD:autopilot.db > autopilot/data/autopilot.db
```

```bash
cd autopilot && autopilot status
```

---

## 6. カスタマイズ

| やりたいこと | 変更場所 |
|---|---|
| 投稿数・投稿時刻 | `config/settings.yaml` の `volume` / `slots`（時刻を変えたら `.github/workflows/autopilot-publish.yml` の cron も UTC で合わせる） |
| ジャンル追加（例: 生活家電） | `config/genres.yaml` にブロックを追加（`keyword`・`features`・`tips` を書くだけ） |
| ASP 案件の掲載 | `config/offers.yaml` |
| NG 表現の追加 | `config/ng_words.yaml` |
| 季節イベント | `config/calendar.yaml` |
| 声の変更 | `config/settings.yaml` の `tts.voicevox_speaker`（VOICEVOX のキャラクター名） |
| BGM | `assets/bgm/upbeat` `cute` `chill` に曲を置き、`assets/bgm/bgm.yaml` に盛り上がり位置・クレジットを書く（下の「BGM の入れ方」参照） |
| 美容 / 暮らし家電の比率 | `config/settings.yaml` の `content.group_weights`（初期値 美容 0.7 : 暮らし 0.3） |
| デザイン（共通パーツ・配色テーマ） | `assets/design/design.css`（kraft / rose / sage / noir） |
| カルーセルのレイアウト | `src/autopilot/render/templates/carousel.html.j2` |
| 動画の演出 | `remotion/src/Reel.tsx`（`cd remotion && npm run studio` でブラウザ上でプレビュー可） |
| 商品イラスト | `src/autopilot/render/illustrations.py`（自作SVG） |
| 商品画像を使わない | `content.use_product_images: false`（自作イラストに切り替わる） |

フォーマット（ランキング / 価格帯別 / 注目モデル / 選び方）、フックの型、配色テーマは、保存数・シェア数をもとに **自動で伸びる組み合わせに寄っていきます**（Thompson Sampling）。

---

### BGM の入れ方

API からの自動投稿では、**Instagram / TikTok アプリ内の流行曲や J-POP は使えません**（権利処理がアプリ内の機能に限られるため。無断で使うとミュート・削除・アカウント制限の原因になります）。代わりに「商用利用可・SNS 利用可」のフリー BGM の中から、人気順・再生数順の上位でテンポの良い曲を選んで入れます。

1. DOVA-SYNDROME / 甘茶の音楽工房 / Pixabay Music などで、**人気順** に並べて 10〜20 曲ほど選ぶ（各曲の規約を確認）
   - ランキング・価格帯向け: BPM 110〜130 の明るいポップ → `assets/bgm/upbeat/`
   - 注目モデル向け: かわいい・キラキラ系 → `assets/bgm/cute/`
   - 選び方向け: Lo-fi・チル系 → `assets/bgm/chill/`
2. `assets/bgm/bgm.yaml` に曲ごとの `start`（いちばん盛り上がる秒数）と、必要なら `credit` を書く
3. コミットして push。以後は形式に合う曲から、直近 3 本と被らないように自動で選曲し、**保存・シェア率の高い曲ほど選ばれやすく**なります。クレジットが必要な曲はキャプションに自動で表記されます。

### 動画冒頭の実写背景

`PEXELS_API_KEY` を登録すると、動画の冒頭に実写の縦動画（ジャンルごとの検索語は `config/genres.yaml` の `stock_queries`）が自動で入ります。同じ動画は 30 本空けるまで再利用しません。

## 7. トラブルシューティング

| 症状 | 原因と対処 |
|---|---|
| `RAKUTEN_APP_ID が未設定です` | Secrets の登録漏れ・名前の打ち間違い |
| `MEDIA_REPO / MEDIA_REPO_TOKEN / MEDIA_BASE_URL を設定してください` | 2-2 と 2-9 を確認（`MEDIA_REPO` と `MEDIA_BASE_URL` は **Variables** 側） |
| `git clone failed` | PAT の対象リポジトリ・Contents 権限・有効期限を確認 |
| `メディア URL がまだ公開されていません` | GitHub Pages が無効、または反映待ち。Pages の設定を確認。次のスロットで自動再試行 |
| Instagram `OAuthException 190` | トークン切れ。2-3 で再発行して `IG_ACCESS_TOKEN` を更新 |
| Instagram `container ... ERROR` | 画像が JPEG でない／URL に届かない。`MEDIA_BASE_URL` をブラウザで開けるか確認 |
| `投稿を24時間停止しました` | 3 回連続失敗による自動停止。原因を直せば 24 時間後に自動再開（すぐ再開するなら手元で `autopilot reset-breaker` → state を push） |
| `投稿バッファが空です` | 生成が連続で失敗。Actions の autopilot-generate のログを確認 |
| 動画が無音 | VOICEVOX が起動していない（Actions ではサービスコンテナが自動起動します） |
| 定期実行が動かない | Variables の `AUTOPILOT_ENABLED` が `true` か / Actions が有効か |

---

## 8. 自宅 PC / VPS で動かす場合

GitHub Actions を使わず、常時起動の PC や VPS（Oracle Cloud Always Free など）で動かすこともできます。

```bash
cd autopilot && cp .env.example .env
```

`.env` に値を記入してから:

```bash
docker compose up -d --build
```

スケジュールは `scripts/crontab` です（コンテナ内は日本時間）。状態は `data/`、生成物は `output/` に保存されます。

---

## 9. 仕組み

```
autopilot/
├── config/                 設定（投稿量・ジャンル・NG表現・季節・ASP案件）
├── assets/                 フォント・Webフォント・デザインCSS・効果音・BGM
├── remotion/               動画テンプレート（React / Remotion）
├── sample/products.json    デモ用の架空商品データ
├── scripts/state.sh        SQLite を autopilot-state ブランチに保存・復元
└── src/autopilot/
    ├── collectors/         楽天API・RSS・価格/順位シグナル・サンプル取り込み
    ├── planner.py          ジャンル/フォーマット/フック/テーマ選択（Thompson Sampling）・重複防止
    ├── llm/                無料LLMルーター（Gemini→Groq→OpenRouter→Ollama→定型文）
    ├── compliance.py       PR表記・薬機法NG・数値捏造・類似度チェック
    ├── render/             HTML/CSS → Playwright でカルーセル・ストーリー（雑誌風デザイン・自作イラスト）
    ├── scoring.py          データスコア・◎○△（実データから算出）
    ├── video/              VOICEVOX（発話タイミング付き）・字幕・Remotion 呼び出し・音量正規化
    ├── publish/            Instagram Graph API・TikTok API・メディア公開
    ├── linkpage/           プロフィール用リンク集ページ
    └── pipeline.py         ステートマシン（失敗段階から再開・3回で諦めて通知）
```

- 投稿の状態: `planned → scripted → rendered → ready → published`。各段階で失敗したら次回その段階から再開し、3 回失敗したらスキップして通知します。
- 二重投稿防止: 投稿 × 媒体 × 種類で一意。API 呼び出し中に落ちた場合は、次回 Instagram 側の直近投稿を No.xxx で照合してから再投稿を判断します。
- 数値（価格・順位・レビュー）は API データをテンプレートに直接差し込み、AI には文章だけを書かせます。

---

## 10. 注意事項

- **ステマ規制**: キャプション冒頭の「PR」、画像右上の「PR」、リンク集ページの広告表記は自動で入ります。削除しないでください。
- **薬機法・景品表示法**: NG 表現は自動検査していますが、完全ではありません。`config/ng_words.yaml` を随時強化し、ときどき投稿を目視してください。
- **商品画像**: 楽天 API の商品画像は各ショップ・メーカーに権利があります。楽天アフィリエイト等の規約上の扱いを確認のうえ利用し、権利者から指摘があった場合は該当投稿を削除して `content.use_product_images: false` にしてください。
- **Remotion**（動画テンプレート）: 個人および従業員 3 人以下の企業は無料で利用できます。それを超える組織で使う場合は Remotion の会社ライセンスが必要です。
- **フォント**: Noto Sans JP / Zen Kaku Gothic New / Zen Old Mincho / Klee One / DM Serif Display / Inter / Archivo Black（いずれも SIL Open Font License）。
- **VOICEVOX**: キャラクターごとの利用規約に従い、キャプションと動画内にクレジット（例「VOICEVOX:冥鳴ひまり」）を自動表記しています。
- **Edge-TTS** は非公式な利用方法のため予備扱いです（VOICEVOX が使えない場合のみ）。
- **無料枠の変更**: 各 API の無料枠・仕様は予告なく変わることがあります。失敗通知が続いたら公式情報を確認してください。
- **楽天 API**: エンドポイントが変わった場合は `RAKUTEN_API_BASE` で差し替えられます。
- デモの商品データ（`sample/products.json`）はすべて架空です。
