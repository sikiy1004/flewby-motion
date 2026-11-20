# ig-pipeline — 美容×ガジェット Instagram 投稿デザイン自動生成

原稿データ（商品名・価格・スペック・訴求コピー）を JSON か CSV で渡すと、決めた世界観に沿ったデザイン済みの投稿画像と、キャプションの定型文を生成します。

```
data/products.json ─┐
data/posts/*.json  ─┼─ 検証 ─ 背景除去（rembg）─ Nunjucks テンプレート（HTML/CSS）─ Chromium ─ out/<投稿ID>/*.png
tokens/tokens.json ─┘                                                                         └ caption.txt
```

| 世界観 | 用途 | テンプレート | サイズ |
|---|---|---|---|
| **A案**（主軸・約8割）：クリーム地／にじむオーロラ／セリフ体の英単語1語＋明朝 | カルーセル | 表紙・商品詳細・比較・まとめ | 1080×1350 |
| **B案**（アクセント・約2割）：インパストの絵の具ストローク／極太ゴシックの特大見出し | 結論系・ランキング系のリール | リールカバー | 1080×1920 |

生成例は `samples/` にあります（ダミー3件分）。

---

## 1. セットアップ（macOS）

必要なもの：Node.js 20 以上、Python 3.11 以上（Homebrew の `brew install node python` で入ります）

```bash
cd ig-pipeline
npm install
npx playwright install chromium
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Adobe Fonts

Creative Cloud アプリの「フォント」から、次のフォントをアクティベートします。
アクティベートしていない場合や、クラウド・CI で実行する場合は、同梱の OFL フォント（`assets/fonts/fallback/`）で自動的に代替して描画します。

| 役割 | Adobe Fonts | 同梱の代替フォント（OFL） |
|---|---|---|
| 英字ディスプレイ（A案の英単語・商品名・価格） | Cormorant Garamond | Cormorant Garamond（同一書体） |
| 和文明朝（A案の日本語） | 貂明朝 | Zen Old Mincho |
| 和文極太ゴシック（B案の見出し） | 源ノ角ゴシック JP | Noto Sans JP（同一デザイン） |
| ラベル（英字の小さな文字） | — | Inter |

Adobe Fonts が実際に使われたかは、`--fonts` を付けて確認できます。

```bash
npm run build -- data/posts/post-01-morning.json --only cover --fonts
# wrote out/.../01-cover.png {"mincho":["Ten Mincho"], ...}   ← "Zen Old Mincho" と出たら代替フォントで描画されている
```

`FONT_MODE=fallback npm run build` とすると、同梱フォントだけで描画します（見た目の比較用）。

---

## 2. クイックスタート

```bash
npm run all          # トークン生成 → 検証 → 背景除去 → 全投稿の画像生成
open out/            # out/<投稿ID>/01-cover.png … reel-cover.png, caption.txt
```

## 3. コマンド一覧

| コマンド | 内容 |
|---|---|
| `npm run all` | 下の tokens → validate → cutout → build をまとめて実行 |
| `npm run tokens` | `tokens/tokens.json` から CSS / TS / ASE / ffmpeg 用 JSON を生成 |
| `npm run validate` | 商品データと投稿データをスキーマで検証（エラー箇所を表示） |
| `npm run cutout` | 商品写真の背景を除去（変わったものだけ処理。`-- --force` で全件やり直し） |
| `npm run build` | 全投稿を生成。`-- data/posts/x.json` で1件だけ、`--only cover,compare` でページを絞る |
| `npm run preview -- data/posts/x.json` | テンプレート・トークン・データを保存するたびに自動で再生成 |
| `npm run csv:export` | 現在の JSON を `data/csv/products.csv`・`posts.csv` に書き出す（入力用の雛形） |
| `npm run csv:import -- data/csv/products.csv` | CSV から JSON に取り込む（商品と投稿はヘッダーで自動判別） |
| `npm run assets` | オーロラ背景と絵の具ストロークを再生成（シード固定で同じ結果になる） |
| `npm run assets:mock` | サンプル用の商品モックを再生成 |
| `npm run board` | トークンとアセットの見本ボード → `docs/previews/step1-board.png` |
| `npm run ps:remove-bg` / `ps:export` | Photoshop で背景を除去する（下記 6 章） |

`--only` に指定できるページ名：`cover`、`detail`（商品詳細すべて）、`detail-<商品ID>`、`compare`、`summary`、`reel`

---

## 4. 入力データ

### 4-1. 商品 `data/products.json`（スキーマ：`data/schema/product.schema.json`）

```json
{
  "id": "hair-dryer",
  "category": "ヘアドライヤー",
  "categoryEn": "Hair Dryer",
  "brand": "AERIS",
  "name": "Silk Flow 1600",
  "nameJa": "シルクフロー 1600",
  "price": 24800,
  "image": "assets/products/raw/hair-dryer.jpg",
  "specs": { "風量": "2.0㎥/分", "重さ": "320g", "温度": "4段階＋スカルプ" },
  "points": ["320gの軽さ", "大風量で速乾", "低温スカルプモード"],
  "links": { "rakuten": "https://…", "amazon": "https://…" }
}
```

| 項目 | 必須 | 内容 |
|---|---|---|
| `id` | ○ | 英小文字・数字・ハイフン。切り抜き画像のファイル名にも使います |
| `category` / `categoryEn` | ○ / – | カテゴリ（日本語・英語） |
| `brand` / `name` / `nameJa` | ○ / ○ / – | ブランド名、英字の商品名、日本語の商品名 |
| `price` | ○ | 税込の参考価格（円・整数） |
| `image` | ○ | 元写真。背景付きでかまいません（自動で切り抜きます） |
| `specs` | ○ | `{ 項目名: 値 }`。最大6項目、書いた順に表示します |
| `points` | ○ | 推しポイント。1〜3個、各20文字まで |
| `displayHeight` | – | 表紙での商品の高さ（px）。小さい商品を大きく見せたいときに指定 |
| `links` | – | 購入リンクの控え（画像には出しません） |

### 4-2. 投稿 `data/posts/<投稿ID>.json`（スキーマ：`data/schema/post.schema.json`）

```json
{
  "id": "post-01-morning",
  "collection": { "number": 2, "issue": 7 },
  "priceDate": "2026年11月",
  "cover": {
    "word": "Ritual",
    "kicker": "Morning Beauty Tech — 3 Items",
    "lead": "朝の5分を整える、\n美容家電3つの選び方。",
    "aurora": "dawn",
    "hero": "facial-ems"
  },
  "products": ["facial-ems", "hair-dryer", "face-brush"],
  "compare": { "kicker": "…", "lead": "…", "rows": [{ "label": "価格", "field": "price" }, { "label": "重さ", "spec": "重さ" }] },
  "summary": { "word": "Index" },
  "reel": { "headline": "朝の美容家電、\n結局この3つ。", "sub": "3年使い比べた結論", "accent": "the answer", "seed": 3 },
  "hashtags": ["#朝美容"]
}
```

| 項目 | 内容 |
|---|---|
| `collection.number` / `issue` | 左上の「COLLECTION 02」と、表紙右上の号数 |
| `priceDate` | 価格注記の時点（「価格は2026年11月時点の参考価格…」） |
| `cover.word` | 主役の英単語1語（英字のみ・9文字まで） |
| `cover.kicker` | 英単語の上に添える小さな英字（任意） |
| `cover.lead` | 明朝のリード。`\n` で改行（2行まで推奨） |
| `cover.aurora` | 背景の種類：`dawn` `shift` `radiance` `ember` `tide` `mist`。右下の3色ドットもこれに連動します |
| `cover.hero` | 表紙に載せる商品（省略時は `products` の先頭） |
| `products` | 1〜4件。**2件以上で比較ページが付きます** |
| `compare.rows` | 比較表の行。`field`（`price` `category` `points.0` など）か `spec`（specs の項目名）。省略時は「価格＋全商品に共通するスペック＋推しポイント」 |
| `summary.word` | まとめページの見出し（省略時は INDEX） |
| `reel` | 書いた場合だけ B案のリールカバーを生成。`headline` は `\n` で改行。文字数に応じて自動で幅に収めます |
| `reel.seed` | ストロークの選び方と配置の揺らぎ。値を変えると配色が変わります |
| `reel.strokes` | 使うストロークを指定（例 `["s01","s07",…]`、省略時はシードで自動選択） |
| `hashtags` | キャプション末尾のハッシュタグ（`tokens.brand.hashtags` と合わせて重複を除きます） |

### 4-3. 生成されるページ

| 投稿の内容 | カルーセル | リール |
|---|---|---|
| 商品1件 | 01 表紙 → 02 商品詳細 → 03 まとめ | `reel` があれば reel-cover |
| 商品2〜4件 | 01 表紙 → 商品詳細×件数 → 比較 → まとめ | 同上 |

### 4-4. CSV で入力する

```bash
npm run csv:export                               # data/csv/ に今のデータで雛形を書き出す
# Excel / Numbers / Google スプレッドシートで編集して、UTF-8 の CSV で保存
npm run csv:import -- data/csv/products.csv      # → data/products.json（元のファイルは .bak に退避）
npm run csv:import -- data/csv/posts.csv         # → data/posts/<id>.json を1行ごとに作成
```

- **products.csv**：`id, category, categoryEn, brand, name, nameJa, price, image, displayHeight, spec1_label, spec1_value … spec6_value, point1, point2, point3, rakuten, amazon`
  - `price` に「¥24,800」と書いても数値として読み込みます。`image` を空にすると `assets/products/raw/<id>.jpg` になります。
- **posts.csv**：`id, collection, issue, priceDate, word, kicker, lead, aurora, hero, products, compare_word, compare_kicker, compare_lead, compare_rows, summary_word, reel_headline, reel_sub, reel_accent, reel_kicker, reel_seed, reel_layout, hashtags`
  - `products` は `|` で区切ります（`facial-ems|hair-dryer`）。
  - `compare_rows` は `価格=price|重さ=spec:重さ|推し=points.0` の形式で書きます。
  - セル内の改行は、Excel の Alt+Enter でも `\n` でもかまいません。`hashtags` は空白で区切ります。
- 取り込むときにスキーマ検証を行い、エラーがあれば書き込みません。

---

## 5. デザイントークン

`tokens/tokens.json` が**唯一の定義元**です。`tokens/build/` は自動生成されるので、直接は編集しません。

| セクション | 内容 |
|---|---|
| `color.paper` / `ink` / `pigment` | クリーム地、墨色、顔料（コバルト・バイオレット・オレンジ・バーミリオン・ピンク・ティール・イエロー・ブラック・ホワイト） |
| `palette.aurora` | オーロラのプリセットごとの配色と、3色ドットの組み合わせ |
| `font.family` | 役割ごとに Adobe Fonts の名前と、同梱の代替フォント |
| `type` | 文字スタイル（`displayWord` `jpLead` `headlineHeavy` など）。CSS では `.t-display-word` のようなクラス名になります |
| `space` / `layout` | 余白、左右マージン（72px）、罫線、ドット、商品画像の最大サイズ |
| `canvas` | カルーセル 1080×1350、リール 1080×1920（安全エリア：上220px・下380px） |
| `texture` / `motion` | 粒子感の強さ、動画用の fps・イージング・尺（第2フェーズで使用） |
| `brand` | コレクション名、アカウント名、PR 表記の文言、誘導文、販売先、Amazon アソシエイトの表記、標準のハッシュタグ |

**アカウントを作成したら**、`brand.handle`（`@your_account`）と `brand.collection` を書き換えて `npm run all` を実行してください。

生成されるファイル：

- `tokens.css`：CSS 変数（`--c-pigment-cobalt` など）と文字スタイルのクラス
- `tokens.ts`：動画（Remotion / Node）用
- `tokens.ase`：Photoshop / Illustrator / Premiere の「スウォッチを読み込み」で同じ色を使える
- `ffmpeg.json`：ffmpeg でテロップを入れるときの色とフォントのパス
- `tokens.js`：見本ボード用

---

## 6. 商品画像の背景除去

1. 元写真を `assets/products/raw/<商品ID>.jpg` に置き、`data/products.json` の `image` に書きます。
2. `npm run cutout` を実行すると、`assets/products/cutout/<商品ID>.png` に切り抜き画像ができます。
   - 背景を除いたあと、小さなゴミの除去、縁に残った背景色の除去、余白の切り詰めを自動で行います。
3. `docs/previews/cutout-qa.jpg` で仕上がりを確認します（元写真／クリーム地に合成／黒地に合成／アルファマスク）。

**モデルの自動選択**（初回実行時に `.cache/models/` へダウンロードします）

| モデル | 使う条件 | 処理時間（1枚） | ピークメモリ | 品質（モックでの IoU） |
|---|---|---|---|---|
| birefnet-general | 空きメモリが 10GB 以上のとき | 約25秒 | 約8GB | 0.996〜0.998 |
| isnet-general-use | 空きメモリが足りないとき、または birefnet が失敗したとき | 約3秒 | 約1GB | 0.995〜0.998 |

- メモリ 16GB の Mac では、ほかのアプリを閉じていれば birefnet が使われます。
- 商品1点ごとに別プロセスで処理するため、複数の商品を続けて処理してもメモリは増え続けません。
- モデルを固定したい場合は `npm run cutout -- --model isnet-general-use` のように指定するか、環境変数 `REMBG_MODEL` を使います。

### 品質が足りないとき：Photoshop との連携

白い製品が白い背景に溶け込む写真、細いケーブル、映り込みの強い金属などでは、Photoshop で仕上げます。

- `npm run ps:remove-bg`
  - ダイアログで写真を複数選ぶと、Photoshop の「背景を削除」でマスクを作り、余白を切り詰めて `assets/products/manual/<商品ID>.png` に保存します。
- 細部を手直ししたい場合
  1. Photoshop で「選択とマスク」などを使って仕上げます。
  2. `npm run ps:export` を実行すると、開いているドキュメントを同じ場所に書き出します。
- **`assets/products/manual/` に置いた画像は、自動の切り抜きより常に優先されます。**
- ファイル名は商品IDにそろえてください（例：`raw/hair-dryer.jpg` → `manual/hair-dryer.png`）。
- これらのスクリプトは、Photoshop のメニュー「ファイル > スクリプト > 参照…」から `scripts/photoshop/*.jsx` を選んでも実行できます。
- ※ この2つの `.jsx` は、Photoshop がない環境で書いたため実機での動作確認ができていません。初回は数枚で試してください。

---

## 7. テンプレートの差し替え・追加

```
templates/
  layouts/base.njk            全ページ共通の土台（tokens.css と base.css を読み込む）
  partials/masthead.njk       左上のコレクション名・PR、右上の号数またはページ番号
  partials/dots.njk           右下の3色ドット
  a-cover.njk                 A案 表紙
  a-detail.njk                A案 商品詳細
  a-compare.njk               A案 比較
  a-summary.njk               A案 まとめ（INDEX・プロフィールへの誘導・PR表記）
  b-reel-cover.njk            B案 リールカバー
  b-layouts/scatter-a.json    B案のストローク配置プリセット
  styles/base.css             レイアウト（数値はできるだけトークンの CSS 変数を使う）
captions/caption.njk          キャプションの定型文
```

### 見た目を変える

- **色・フォント・文字サイズ・余白**：`tokens/tokens.json` を編集して `npm run tokens` を実行します。すべてのテンプレートに反映されます。
- **レイアウト**：`templates/styles/base.css` のテンプレートごとのブロック（`/* ---- A: cover ---- */` など）を編集します。
- **作業の流れ**：`npm run preview -- data/posts/post-01-morning.json --only cover` を動かしておくと、保存のたびに `out/` が更新されます。
  - レンダリングされた HTML は `.cache/html/<投稿ID>/` にあります。Chrome で開くと、デベロッパーツールで要素を調べられます。

### テンプレートを差し替える・増やす

1. 例えば `templates/a-cover.njk` をコピーして `templates/a-cover-v2.njk` を作ります。
2. `pipeline/build.mjs` の `slidesFor()` で、どのテンプレートを使うかを指定します（ページの順番もここで決まります）。
3. テンプレートの中では、次の変数が使えます。

| 変数 | 内容 |
|---|---|
| `post` / `cover` / `compare` / `summary` / `reel` | 投稿データ |
| `items` | 商品データ（`cutout` に切り抜き画像のパスが入る）の配列 |
| `hero` / `item` / `itemNo` | 表紙の商品／詳細ページの商品とその番号 |
| `T` / `brand` | トークン全体／`tokens.brand` |
| `dots` / `priceNote` / `compareRows` / `pageNo` | 3色ドット、価格注記、比較表の行、ページ番号（「02 / 06」） |
| `canvas` | `{ name, width, height }` |

4. フィルター：`pad2`（7 → 07）、`yen`（24800 → ¥24,800）、`nl2br`（改行を `<br>` に）、`kebab`
5. 日本語は必ず HTML のテキストとしてフォントで組みます。画像生成AIに文字を描かせることはしません。

### 背景アセットを差し替える

- **オーロラ**：`generators/presets/aurora.json` で `seed` や配色（`stops`）を変え、`npm run assets:aurora` を実行します。
  - お試しなら `.venv/bin/python generators/aurora.py --seed 99 dawn` で別名ファイルとして出力できます。
  - 形状は `generators/aurora.py` の `shape_strands()` に追加します。
  - 新しいプリセットを作ったら、`tokens.json` の `palette.aurora` にドットの配色も追加し、`data/schema/post.schema.json` の `aurora` の選択肢にも加えます。
- **絵の具ストローク**：`generators/presets/paint.json`（色の組み合わせ・長さ・太さ・角度・シード）を変えて `npm run assets:paint` を実行します。
  - Firefly や Photoshop で作った透過 PNG を、`assets/paint/s01.png` などと**同じ名前で上書き**すれば、そのまま差し替えられます。
- **B案の配置**：`templates/b-layouts/scatter-a.json` を複製して編集し、投稿の `reel.layout` で指定します。
  - 各スロットは位置・長辺の大きさ・回転・前面か背面か（`z`）を持ちます。
  - `anchor: "headTop"` を付けると、見出しの上端を基準に配置されます。

---

## 8. PR表記（ステマ規制への対応）

景品表示法のステルスマーケティング規制（2023年10月施行）に沿って、広告であることを一目で分かる位置に表示します。

| 場所 | 表示 |
|---|---|
| 表紙（A案） | 左上、コレクション番号の横に枠付きの「PR」 |
| まとめページ | 最下部に「PR」と「本投稿はアフィリエイト広告（PR）を含みます」、価格の注記 |
| リールカバー（B案） | サブコピーの行の右端に「PR」（UI に隠れず、プロフィール一覧でも切り取られない位置） |
| キャプション | **1行目**に【PR】表記（「…続きを読む」で折りたたまれる前に見える）。末尾に Amazon アソシエイトの表記 |

文言は `tokens.brand`（`prLabel` `prNotice` `priceNote` `amazonDisclosure`）で変更できます。

---

## 9. 書き出しの仕様と Instagram へ投稿するときの注意

- PNG・sRGB・等倍。カルーセルは 1080×1350（4:5）、リールカバーは 1080×1920（9:16）
- リールカバーの重要な要素は、プロフィール一覧で切り取られる範囲（中央の 1080×1350〜1440）と、再生中の UI に重ならない範囲に収めています。
  - 確認用の画像：`docs/previews/step4-reel-safezones.jpg`
- 価格は投稿時点の参考価格として扱い、`priceDate` を必ず更新してください。

## 10. ディレクトリ構成

```
ig-pipeline/
  tokens/            tokens.json（唯一の定義元）と build/（自動生成）
  templates/         Nunjucks テンプレート・CSS・B案の配置プリセット
  captions/          キャプションの定型文
  data/              products.json / posts/*.json / schema/ / csv/
  assets/
    fonts/fallback/  同梱の OFL フォント（LICENSES.md）
    aurora/          オーロラ背景（2160×2700）
    paint/           絵の具ストローク（透過 PNG・2倍解像度）
    products/        raw/（元写真） cutout/（rembg） manual/（Photoshop・優先） mock/（サンプルの正解画像）
  generators/        aurora.py / paint.py / mock_products.py と presets/
  pipeline/          build / shot / validate / csv / cutout / preview
  scripts/           build-tokens.mjs / contact_sheet.py / photoshop/
  references/        デザインの参考画像
  docs/              previews/（各ステップの確認画像） phase2-video.md
  samples/           ダミー3件の生成結果（JPEG）
  out/               生成物（Git の管理対象外）
```

## 11. 第2フェーズ（リール動画）

設計方針は [`docs/phase2-video.md`](docs/phase2-video.md) にまとめています。
推奨は「静止画と同じ HTML テンプレートで透過テロップを書き出し、ffmpeg で合成する」方式で、仕上げを Premiere で行う構成です。デザイントークン（`tokens.ts` / `ffmpeg.json` / `tokens.ase`）は、すでに動画と共有できる形で出力しています。

## 12. トラブルシューティング

| 症状 | 対処 |
|---|---|
| `--fonts` の結果が代替フォントになる | Creative Cloud でフォントをアクティベートし、Chromium を再起動します（`npm run build` をもう一度実行） |
| `cut-out missing for …` | `npm run cutout` を実行します |
| 背景除去の途中でプロセスが終了する | メモリ不足です。自動で isnet に切り替えて再実行しますが、`--model isnet-general-use` で固定することもできます |
| スキーマのエラー | 表示されたパス（例：`/cover/aurora`）の値を直します。使える値も表示されます |
| リールの見出しが小さい | 1行が長すぎます。`\n` で改行位置を調整します（一番長い行が横幅いっぱいになるよう自動で調整しています） |
| ドライヤーなど横長の商品が小さく見える | 商品データに `displayHeight` を指定します。幅は `tokens.layout.productMaxWidth`（600px）が上限です |

## ライセンス

- 同梱フォント：SIL Open Font License 1.1（`assets/fonts/fallback/LICENSES.md`）
- 使用しているライブラリ：Playwright（Apache-2.0）、Nunjucks（BSD-2）、Ajv（MIT）、rembg（MIT）、numpy / scipy / Pillow（BSD 系）、onnxruntime（MIT）
- 背景アセットとモック画像は、このリポジトリのスクリプトで生成したものです。

---

## 13. リサーチ層（投稿案と原稿データを作る）

描画エンジンの前段で、最新情報を調べて「投稿案」と「原稿データ」を作ります。描画は既存エンジンに任せます。
使い方は [`docs/research-quickstart.md`](docs/research-quickstart.md)、設計と承認済みの方針は [`docs/research-layer-plan.md`](docs/research-layer-plan.md)、
Claude Code が守るルールは [`CLAUDE.md`](CLAUDE.md) にあります。

```
/research（Claude Code）→ research/runs/<実行ID>/ideas.md
   → npm run research:approve -- <実行ID> I01   ← あなたが端末で承認
   → /research-draft I01 → research:draft（原稿＋チェック）→ research:install（data/ へ）
   → npm run build（既存エンジンで描画）
```

| コマンド | 内容 |
|---|---|
| `npm run research:rakuten [-- <カテゴリ>] [--fixture]` | 楽天のランキング・検索を取得（`--fixture` はテスト用データ、`--check-setup` で設定確認、`--ping` で接続テスト） |
| `npm run research:evidence -- new <実行ID> <商品ID> [--from <カテゴリ>:<順位>]` | 出典ファイルの雛形（`validate` で形式確認） |
| `npm run research:calendar [-- check / snapshot <実行ID>]` | セール暦（`research/calendar.json`）の一覧・検査・実行ごとの控え |
| `npm run research:competitors -- add / check / summary` | 競合の投稿の「型」の記録表（`research/competitors/log.csv`）。記録は `/competitor-log` で |
| `npm run research:ideas -- render <実行ID>` | 投稿案リスト `ideas.md` を作る（期限切れ・古い価格・NG表現で止まる） |
| `npm run research:approve -- <実行ID> I01 I03` | **オーナーが端末で実行する承認**（`status` で確認） |
| `npm run research:draft -- <実行ID> <案ID>` | 承認済みの案から原稿データを作ってチェック |
| `npm run research:install -- <実行ID> <案ID>` | チェックを通った原稿を data/ に取り込む |
| `npm run research:lint [-- data/posts/x.json]` | 表現チェック（薬機法・景表法・使用感） |
| `npm run research:sample [-- --clean]` | テスト用データで流れを試す／片付ける |

- 設定：`research/config.json`（カテゴリと優先順・楽天の接続先・鮮度の上限 72 時間）、表現ルール：`research/compliance.json`
- 楽天のキーは `.env`（`.env.example` を参照。Git には上がりません）
- 出典ファイル（`research/schema/evidence.schema.json`）に、すべての値の取得元 URL と取得日時、通常価格とセール価格・期間、画像の取得元を記録します。
  既存の入力スキーマは変更していません（セール期間は `priceDate` に入ります）。
- 定期実行（週1回・投稿案リストの作成まで）：`zsh scripts/schedule/install-weekly.sh`（詳細は docs/research-quickstart.md の E）
- 承認の代行は、ルール（CLAUDE.md）に加えて、プロジェクトの Claude Code 設定（`.claude/settings.json` の deny）でも禁止しています。
