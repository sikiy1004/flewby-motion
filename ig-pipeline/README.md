# ig-pipeline — 美容×ガジェット Instagram 投稿デザイン自動生成

原稿データ（JSON / CSV）→ HTML/CSS テンプレート → PNG を生成するパイプラインです。
※ 作業中です（現在 ステップ1：トークン・フォント・背景アセット）。詳しい README はステップ6で完成させます。

## セットアップ（macOS）

```bash
cd ig-pipeline
npm install
npx playwright install chromium
python3 -m venv .venv && .venv/bin/pip install numpy pillow scipy
```

Adobe Fonts：Creative Cloud で次のフォントをアクティベートしておきます。
未アクティベートでも、同梱の OFL フォントで自動的に代替して描画されます。

| 役割 | Adobe Fonts | 代替（同梱 OFL） |
|---|---|---|
| 英字ディスプレイ | Cormorant Garamond | Cormorant Garamond |
| 和文明朝 | 貂明朝 | Zen Old Mincho |
| 和文極太ゴシック（B案） | 源ノ角ゴシック JP | Noto Sans JP（同一デザイン） |
| ラベル | — | Inter |

## コマンド

| コマンド | 内容 |
|---|---|
| `npm run tokens` | `tokens/tokens.json` から CSS / TS / ASE / ffmpeg 用 JSON を生成 |
| `npm run assets` | オーロラ背景と絵の具ストロークを再生成（シード固定で同一結果） |
| `npm run board` | トークンとアセットの確認ボードを `docs/previews/` に出力 |

`FONT_MODE=fallback` を付けると Adobe Fonts を使わず同梱フォントだけで描画します。
`node pipeline/shot.mjs <html> <png> --fonts` で、実際に使われたフォント名を表示できます（Adobe Fonts が効いているかの確認用）。

## デザイントークン

`tokens/tokens.json` が唯一の定義元です。`tokens/build/` 以下は自動生成なので直接編集しません。

- `tokens.css` … 静止画テンプレート用 CSS 変数と `.t-*` 文字スタイル
- `tokens.ts` … 第2フェーズの動画（Remotion / Node）用
- `tokens.ase` … Photoshop / Illustrator / Premiere のスウォッチに読み込み
- `ffmpeg.json` … ffmpeg でテロップを入れるときの色とフォントのパス

## 背景アセット

- `generators/presets/aurora.json`：オーロラ 6 種（dawn / shift / radiance / ember / tide / mist）。`seed` を変えると別のバリエーションになります（`--seed 99` で試し出し）
- `generators/presets/paint.json`：インパストのストローク 14 種（RGBA の透過 PNG）
- Firefly や Photoshop で作った素材を `assets/paint/` に同じ名前で置けば差し替えられます
