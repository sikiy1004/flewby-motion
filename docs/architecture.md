# SNSアフィリエイト全自動化 — システムアーキテクチャ（Phase 2）

作成日: 2026-11-19 / ステータス: **承認済み・実装済み**（実装は [`autopilot/`](../autopilot/README.md)）
前提となる戦略: [`docs/strategy.md`](./strategy.md)（ジャンル＝美容家電・セルフケアガジェット比較）

---

## 1. 設計方針

1. **ランニングコスト0円**：有料SaaS・従量課金APIを使わない。無料枠APIは「落ちても止まらない」ように必ずフォールバックを持つ。
2. **ゼロタッチ**：cron（GitHub Actions）起点で「収集 → 企画 → 台本 → 画像/動画 → ホスティング → 投稿 → 効果測定 → 学習」が無人で回る。
3. **止まらない・壊さない**：各投稿はステートマシンで管理し、失敗した段階から再開。**2日分の投稿バッファ**を先行生成しておき、当日生成が失敗してもバッファから投稿する。
4. **数値はLLMに作らせない**：価格・順位・レビュー数はAPIデータをテンプレートへ直接差し込み、LLMは文章（フック・解説・キャプション）だけを担当。誤情報と薬機法リスクを構造的に減らす。
5. **法令・規約チェックを関門化**：PR表記・NGワードの検査を通らない生成物は投稿されない。

---

## 2. 全体フロー

```
                ┌───────────── GitHub Actions（cron, 無料） ─────────────┐
                │                                                        │
 03:00 JST      │  [1] collect   楽天ランキング/商品検索API・PR TIMES RSS・   │
 （生成バッチ） │                 Googleトレンド RSS → products / signals    │
                │  [2] plan      スコアリング＋フォーマット選択（学習済み重み）│
                │                 重複・クールダウン判定 → topics             │
                │  [3] script    LLMルーター（Gemini→Groq→OpenRouter→Ollama  │
                │                 →テンプレ）で JSON 台本・キャプション生成     │
                │  [4] comply    PR表記・NGワード・類似度チェック（不合格→再生成）│
                │  [5] render    カルーセル: HTML/CSS → Playwright → JPEG     │
                │                 動画: VOICEVOX → 字幕ASS → FFmpeg → MP4     │
                │  [6] linkpage  リンク集ページ(No.xxx)を再生成して公開         │
                │                                                        │
 07:30/12:15/   │  [7] publish   バッファから1件取り出し → メディア公開URL化 →   │
 19:00/21:00    │                 Instagram Graph API / TikTok API で投稿     │
 （投稿スロット）│                 → publications に記録（重複防止）            │
                │                                                        │
 毎日 23:30     │  [8] insights  リーチ・保存・シェア・再生数を取得 → metrics    │
                │                 → フォーマット/フック別の重みを更新（学習）     │
 毎週月曜       │  [9] maintain  トークン自動更新・週次レポート通知・古いメディア削除│
                └────────────────────────────────────────────────────────┘
        状態: SQLite（state ブランチに自動コミットして永続化）
        通知: Discord Webhook（失敗時・週次レポート）
```

---

## 3. 技術スタック（すべて無料）

| レイヤー | 採用 | 無料の根拠 / 備考 | フォールバック |
|---|---|---|---|
| 実行基盤 | **GitHub Actions** | publicリポジトリは無料無制限、privateでも月2,000分の無料枠（本システムの想定使用量は月700分前後） | ローカルPCの cron / タスクスケジューラ、Oracle Cloud Always Free VM（docker compose 同梱） |
| 言語 | Python 3.11+ | — | — |
| 商品データ | **楽天ウェブサービス**（ランキングAPI・商品検索API・ジャンル検索API） | アプリID登録のみで無料。アフィリエイトID付きURLが返る | Yahoo!ショッピングAPI（任意） |
| トレンド | PR TIMES RSS、Google トレンド（急上昇）RSS、ガジェット系ニュースRSS | 無料RSS | — |
| LLM | **Gemini API 無料枠**（Flash系） | 無料枠（レート制限あり・無料枠の入力は学習利用され得る＝公開前提の投稿文なので許容） | Groq無料枠 → OpenRouter無料モデル → Ollama（ローカル）→ 決定論テンプレ（LLMゼロでも投稿は止まらない） |
| 画像生成 | **Jinja2 + HTML/CSS + Playwright（Chromium）** | OSS。リポジトリ既存の Noto Sans JP / Inter フォントを再利用 | Pillow 簡易レンダラー |
| 音声合成 | **VOICEVOX Engine（Docker, CPU版 `cpu-0.26.2`。既定の声は冥鳴ひまり）** | 無料・商用可（キャラクターごとの規約に従いクレジット表記を自動付与） | Edge-TTS（※非公式利用のため規約上グレー。あくまで非常用） |
| 素材 | Pexels API / Pixabay API | 無料（Pexels: 200req/時） | 単色グラデ＋図形のモーション背景（素材なしでも成立） |
| 動画編集 | **Remotion**（React でモーション・字幕・音声ミックス）＋ **FFmpeg**（音量正規化） | 個人・3人以下の企業は無料。デザイン刷新（2026-11）で FFmpeg 単体から移行 | — |
| BGM | `assets/bgm/` に置いた商用可・クレジット不要の音源 | 素材を置かない場合はFFmpegで生成する環境音パッドを使用 | — |
| 投稿 | **Instagram Graph API**（Content Publishing：カルーセル・リール・ストーリーズ） | 公式・無料 | — |
| 投稿 | **TikTok Content Posting API**（Direct Post, FILE_UPLOAD） | 公式・無料（公開投稿には審査通過が必要） | 審査前は無効化 |
| メディア公開URL | **GitHub Pages（public の別リポジトリ）** | Instagram APIは画像/動画を「公開URL」から取得する仕様のため。投稿後7日で自動削除 | Cloudflare R2 無料枠（10GB） |
| リンク集ページ | GitHub Pages（同上） | Linktree等の有料プラン不要 | Cloudflare Pages |
| DB | **SQLite** | 単一ファイル。Actions実行ごとに `state` ブランチへコミット | — |
| 通知 | Discord Webhook | 無料 | GitHub Actions の失敗メール |
| 秘密情報 | GitHub Secrets ＋ 更新されるトークンはDB内で暗号化（Fernet） | 無料 | ローカル運用時は `.env` |

---

## 4. モジュール設計

### 4-1. ネタ収集・台本生成

**collectors/**
- `rakuten.py`：対象ジャンル（美容家電・ヘアケア家電・オーラルケア・脱毛器 等。ジャンルIDは初回にジャンル検索APIで名前から自動解決し `config/genres.yaml` にキャッシュ）のランキング上位を毎日取得。価格・レビュー数・平均・順位を時系列保存 → 「価格が下がった」「順位が急上昇」を**シグナル**として抽出。
- `rss.py`：PR TIMES・Googleトレンド・ガジェットニュースのRSSからキーワード一致の新着を収集（新商品速報・季節ネタ用）。
- `calendar.py`：セール・季節イベントカレンダー（楽天スーパーSALE、ブラックフライデー、初売り、新生活、ボーナス期等）を持ち、該当期間は「セール速報」フォーマットの重みを上げる。
- `amazon_link.py`：商品名から `tag=` 付きのAmazon検索URLを生成（PA-API不要）。

**planner/**
- スコア = シグナル強度（順位上昇・値下げ・新着）× 季節係数 × フォーマット重み（学習値）× 鮮度。
- 除外ルール：同一商品は21日クールダウン／同一フォーマット連続2回まで／同一トピックの重複は `content_hash` で排除。

**llm/**
- `router.py`：プロバイダーを順に試行。各プロバイダーの「当日失敗回数」をDBに記録し、レート制限時は次へ即スキップ。
- 出力は**JSONスキーマ固定**（Pydanticで検証、壊れていれば再試行）：

```json
{
  "hook": "冒頭3秒の一文（15字以内）",
  "slides": [{"heading": "...", "body": "...", "product_ref": "item_code or null"}],
  "video_scenes": [{"on_screen": "...", "narration": "...", "visual": "slide|broll:<keyword>"}],
  "caption_instagram": "...",
  "caption_tiktok": "...",
  "hashtags_instagram": ["..."],
  "hashtags_tiktok": ["..."],
  "cta": "保存して比べてね / No.042はプロフのリンクから"
}
```

- プロンプトは `prompts/*.j2`（フォーマット別）。フックは「数字型」「損失回避型」「比較型」「問いかけ型」等の型を指定して生成させ、型ごとの成績を学習に使う。

**compliance/**
- `PR` 表記の有無、NGワード辞書（薬機法・景表法の典型表現）、断定・最上級表現、数値の捏造（スライド本文に API にない数値がないか）、直近50投稿とのキャプション類似度（しきい値超過で再生成）。

### 4-2. カルーセル画像（Instagramフィード）

- サイズ **1080×1350（4:5）**、JPEG（Instagram APIはJPEGのみ）、6〜8枚。
- 構成：①表紙（フック＋PRラベル）→ ②比較表 → ③〜⑥商品別カード（価格・レビュー・機能アイコン・向いている人）→ ⑦まとめ → ⑧CTA（保存・フォロー・No.xxx）。
- `render/templates/carousel/*.html.j2` + `themes/*.css`（配色テーマ3〜4種をローテーションしてマンネリ・スパム判定を回避）。
- Playwright で1枚ずつ `page.screenshot()`。フォントはローカル埋め込み（ネット不要・高速）。

### 4-3. ショート動画（リール / TikTok 共通）

| 工程 | 処理 |
|---|---|
| 1. シーン画像 | 1080×1920 の HTML テンプレートを Playwright で PNG 化（文字は**上下のセーフゾーン**を避けて配置：上 220px・下 420px・右 160px を空ける） |
| 2. 背景 | `visual: broll:<kw>` のシーンは Pexels の縦動画を取得して半透明カードの背面に、それ以外は Ken Burns（zoompan）で静止画に動きを付与 |
| 3. 音声 | VOICEVOX でシーンごとに WAV 生成 → 実測の長さでシーン尺を決定（読み上げ速度 1.1〜1.2倍） |
| 4. 字幕 | ナレーションを13〜16字単位に分割した ASS 字幕（縁取り・強調色）を生成し libass で焼き込み |
| 5. 合成 | xfade でシーン遷移、冒頭0.3秒に効果音、BGM は sidechaincompress でナレーション時に自動ダッキング、最終 loudnorm（-14 LUFS） |
| 6. 出力 | H.264 High / yuv420p / 30fps / AAC 128kbps / `+faststart`、9:16、15〜45秒（媒体別に尺を調整） |
| 7. カバー | 1枚目シーン画像をリールのカバー画像として流用 |

### 4-4. 投稿・スケジューラー・エラー検知

**publish/instagram.py**
- カルーセル：子コンテナ（`is_carousel_item=true`）を枚数分作成 → 親コンテナ（`media_type=CAROUSEL`）→ `status_code` が `FINISHED` になるまでポーリング → `media_publish`。
- リール：`media_type=REELS`（`share_to_feed=true`、`cover_url`）→ ポーリング → 公開。
- ストーリーズ：`media_type=STORIES`（告知画像。リンクスタンプはAPI非対応のため画像内で誘導）。
- 公開前に `content_publishing_limit` で残り枠を確認。
- トークン：長期トークン（約60日）を毎週自動リフレッシュし、DBに暗号化保存。

**publish/tiktok.py**
- `post/publish/video/init`（FILE_UPLOAD）→ チャンクアップロード → `status/fetch` で完了確認。
- 審査前は `TIKTOK_ENABLED=false` で無効。AIGCフラグ・プライバシー設定は config で制御。
- アクセストークン（短期）はリフレッシュトークンで実行ごとに更新。

**publish/media_host.py**
- `github_pages`（既定）：公開用リポジトリの `media/<post_no>/` にプッシュ → Pages の URL が配信可能になるまでHEADで確認 → Instagramへ渡す。投稿完了7日後に削除。
- `r2`：Cloudflare R2（S3互換）に置き換え可能なインターフェース。

**ステートマシン（posts.status）**

```
planned → scripted → checked → rendered → hosted → published
   └──────── 各段階で失敗 → failed(attempts+1) → 次回実行で同じ段階から再開
                                    └─ attempts ≥ 3 → skipped（通知）
```

**重複投稿防止**
- `publications` に `UNIQUE(post_id, platform)`。
- 公開APIを呼ぶ前に `publishing` 状態を書き込み、呼んだ後にメディアIDを保存（途中で落ちても、次回は Instagram 側の直近投稿一覧と照合してから再投稿判定）。
- `posts.content_hash`（商品集合＋フォーマット＋週番号）に `UNIQUE`。
- GitHub Actions の `concurrency` グループで同時実行を禁止。

**エラー検知・通知**
- 段階ごとに指数バックオフで最大3回リトライ。
- 3回連続で投稿失敗 → サーキットブレーカー作動（以後のスロットを停止）＋ Discord に通知。
- 週次レポート（投稿数・失敗数・リーチ・保存数・上位投稿・トークン期限）を Discord に送信。
- `doctor` コマンドで、各APIキーの有効性・トークン期限・フォント・VOICEVOX疎通・FFmpeg を一括診断。

### 4-5. 効果測定と自動学習

- 毎晩 Instagram Insights（リーチ・保存・シェア・再生）と TikTok の動画統計を取得。
- 指標 = （保存＋シェア×1.5）/ リーチ。フォーマット × フック型 × テーマの組み合わせごとに **Thompson Sampling** で次回の選択確率を更新 → 人が分析しなくても「伸びる型」に自動で寄っていく。

---

## 5. データベース設計（SQLite）

| テーブル | 主なカラム | 役割 |
|---|---|---|
| `products` | id, source, item_code(UNIQUE), name, brand, genre_id, image_url, affiliate_url, amazon_url | 商品マスタ |
| `product_snapshots` | product_id, date, price, rank, review_count, review_avg | 価格・順位の推移（シグナル検出用） |
| `signals` | id, kind(rank_up/price_drop/new/news/season), ref, strength, created_at | ネタ候補 |
| `posts` | id, post_no(UNIQUE), format, hook_type, theme, status, script_json, content_hash(UNIQUE), assets_dir, attempts, last_error, scheduled_for | 投稿単位（バッファ兼ステート） |
| `post_products` | post_id, product_id | 投稿に含まれる商品（クールダウン判定） |
| `publications` | id, post_id, platform, kind(carousel/reel/story/tiktok), container_id, media_id, permalink, status, published_at — UNIQUE(post_id, platform, kind) | 投稿実績・重複防止 |
| `metrics` | publication_id, fetched_at, reach, plays, likes, saves, shares, comments | 効果測定 |
| `arm_stats` | arm_key, alpha, beta, updated_at | 学習用（Thompson Sampling） |
| `secrets_store` | platform, ciphertext, expires_at | 自動更新されるトークン（暗号化） |
| `runs` | id, job, started_at, finished_at, status, summary | 実行ログ |

---

## 6. ディレクトリ構成

既存の Remotion プロジェクトとは独立させ、`autopilot/` 配下に構築します（ワークフローだけはGitHubの仕様上リポジトリ直下の `.github/workflows/`）。

```
flewby-motion/
├── docs/
│   ├── strategy.md
│   └── architecture.md
├── .github/workflows/
│   ├── autopilot-generate.yml     # 03:00 JST 収集〜生成（バッファ補充）
│   ├── autopilot-publish.yml      # 投稿スロット（07:30 / 12:15 / 19:00 / 21:00 JST）
│   └── autopilot-maintain.yml     # insights・トークン更新・週次レポート・掃除
└── autopilot/
    ├── README.md                  # セットアップ手順書
    ├── pyproject.toml
    ├── .env.example
    ├── docker-compose.yml         # VOICEVOX + ローカル/VPS運用用
    ├── config/
    │   ├── settings.yaml          # 投稿スロット・媒体ON/OFF・尺・テーマ
    │   ├── genres.yaml            # 対象ジャンル（ID自動解決キャッシュ）
    │   ├── offers.yaml            # 提携済みASP案件（承認済みのみ）
    │   ├── ng_words.yaml          # 薬機法・景表法NG表現
    │   └── calendar.yaml          # セール・季節イベント
    ├── assets/
    │   ├── fonts/                 # Noto Sans JP / Inter（既存 public/fonts を利用）
    │   ├── bgm/  sfx/  icons/
    ├── sample/
    │   └── products.json          # オフライン動作確認用サンプルデータ
    ├── src/autopilot/
    │   ├── cli.py                 # run / collect / plan / generate / publish / insights / maintain / doctor
    │   ├── config.py
    │   ├── pipeline.py            # ステートマシン・オーケストレーター
    │   ├── db/                    # schema.sql, repository.py
    │   ├── collectors/            # rakuten.py, rss.py, calendar.py, amazon_link.py
    │   ├── planner/               # scoring.py, bandit.py
    │   ├── llm/                   # router.py, providers/, prompts/, schemas.py
    │   ├── compliance/            # checker.py
    │   ├── render/                # carousel.py, html.py, templates/, themes/
    │   ├── video/                 # tts.py, stock.py, subtitles.py, composer.py, bgm.py
    │   ├── publish/               # instagram.py, tiktok.py, media_host.py
    │   ├── linkpage/              # build.py, templates/
    │   └── notify/                # discord.py
    ├── tests/
    ├── data/                      # SQLite（git管理外、Actionsでは state ブランチへ）
    └── output/                    # 生成物（git管理外）
```

---

## 7. スケジュールとリソース見積もり

| ジョブ | 時刻（JST） | 内容 | 所要（目安） |
|---|---|---|---|
| generate | 毎日 03:00 | 収集・企画・台本・カルーセル1〜2本・動画1本・ストーリー画像・リンク集更新 | 8〜15分 |
| publish | 07:30 / 12:15 / 19:00 / 21:00 | ストーリー / カルーセル / TikTok / リール をバッファから投稿 | 各1〜3分 |
| maintain | 毎日 23:30（週次処理は月曜） | insights取得・学習更新・トークン更新・掃除・レポート | 1〜2分 |

- GitHub Actions 使用量：約 20〜25分/日 ≒ **月 600〜750分**（private の無料枠 2,000分に収まる）。
- 注意点（対策込み）
  - Actions の cron は数分〜十数分遅れることがある → 投稿時刻は「おおよそ」で問題ない設計。
  - **publicリポジトリでは60日間活動がないと定期実行が自動停止** → maintain ジョブが状態コミットを行うことで回避（private推奨）。
  - Gemini 等の無料枠は仕様変更があり得る → LLMルーターで自動フォールバック、最終手段はテンプレ生成。

---

## 8. コスト

| 項目 | 月額 |
|---|---|
| GitHub Actions / Pages | 0円（無料枠内） |
| LLM（Gemini / Groq / OpenRouter 無料枠, Ollama） | 0円 |
| VOICEVOX / FFmpeg / Playwright / SQLite | 0円（OSS） |
| Pexels / Pixabay / 楽天API | 0円 |
| Instagram Graph API / TikTok API | 0円 |
| Discord Webhook | 0円 |
| **合計** | **0円** |

（任意で独自ドメインを使う場合のみ年1,000〜2,000円程度）

---

## 9. Phase 3 での実装範囲（承認後）

1. `autopilot/` 一式（上記モジュール）と GitHub Actions ワークフロー
2. **サンプルデータ（`sample/products.json`）とLLMなし（テンプレ）モードで、ネットワーク・APIキーなしでも**「カルーセル1投稿分（JPEG×8）」と「ショート動画1本（MP4）」がローカル生成されることをテストで確認
3. VOICEVOX が使えない環境でも動作確認できるよう、音声はフォールバック（無音＋字幕、またはEdge-TTS）で通し確認
4. 投稿モジュールは `--dry-run` で API リクエスト内容を検証（実投稿は `.env` 設定後）
5. `autopilot/README.md`：アカウント連携（Meta / 楽天 / ASP / TikTok / Discord / GitHub Secrets）〜 定期実行の有効化までの手順書
