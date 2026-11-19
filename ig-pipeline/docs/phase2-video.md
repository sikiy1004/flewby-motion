# 第2フェーズ設計メモ：リール動画のテロップ・編集の自動化

今回（第1フェーズ）は設計方針の記録のみです。静止画と動画が同じデザイントークンを共有できるよう、
第1フェーズの時点で次のものを用意してあります。

| 用意済みのもの | 場所 | 動画での使い道 |
|---|---|---|
| デザイントークン（唯一の定義元） | `tokens/tokens.json` | 色・フォント・文字サイズ・余白・**モーション**（fps / イージング / 尺）を共有 |
| TypeScript 版トークン | `tokens/build/tokens.ts` | Remotion / Node で動画を組むとき `import { tokens }` で読む |
| ffmpeg 用トークン | `tokens/build/ffmpeg.json` | `drawtext` の色（0xRRGGBB）とフォントファイルのパス |
| Adobe スウォッチ | `tokens/build/tokens.ase` | Premiere / After Effects のスウォッチに読み込み、手作業の編集でも同じ色を使う |
| リール用キャンバスと安全エリア | `tokens.canvas.reel`（1080×1920、上220px / 下380px） | テロップを UI に隠れない位置へ置く |
| HTML テンプレート → 画像の仕組み | `pipeline/shot.mjs` | 背景を透過させたテロップ PNG の書き出しにそのまま流用できる |
| 背景アセット（オーロラ / 絵の具） | `assets/aurora`, `assets/paint` | 動画の背景や、場面転換の素材として使う |

## 方式の比較

| 方式 | 長所 | 短所 | 費用 |
|---|---|---|---|
| **A. HTML テロップ＋ffmpeg 合成（推奨）** | 静止画と**同じテンプレート・フォント・組版**でテロップを作れる。完全に自動化でき、Mac でもクラウドでも動く | 凝ったアニメーションは不得意（フェード・スライド・マスク程度） | 無料（OSS のみ） |
| B. Premiere Pro テンプレート（MOGRT） | 手作業で微調整しやすい。Premiere の作業に乗れる | テキストの流し込みを自動化するには手間がかかる（CSV 読み込みには拡張機能や ExtendScript が必要） | CC 契約内 |
| C. Remotion（React で動画を作る） | アニメーションの表現力が高い。`tokens.ts` をそのまま使える | 会社規模によっては**有料ライセンス**が必要（個人と社員3名以下の会社は無料） | 条件付き |

### 推奨構成：A を基本にし、仕上げは Premiere で行う

```
data/reels/<id>.json        尺・テロップ（開始秒・終了秒・文言）・使う素材の指定
        │
        ├─ templates/video/telop-*.njk   HTML テロップ（tokens.css を共有）
        │      └─ shot.mjs（omitBackground）→ 透過 PNG を1テロップ1枚
        │
        └─ pipeline/video.mjs
               ffmpeg -i 素材.mp4 -i telop01.png … 
                 -filter_complex "overlay=enable='between(t,1.0,3.4)'…, fade…"
               → out/<id>/reel.mp4（1080×1920 / 30fps / H.264 / AAC）
               → 同時に Premiere 用の XML（FCPXML）を書き出し、手直しできるようにする
```

- アニメーションの尺とイージングは `tokens.motion`（in 0.6秒 / hold 2.4秒 / out 0.4秒、`editorial` イージング）で統一します。
- テロップの書体は、A案の明朝・英字セリフ、または B案の極太ゴシックを `tokens.type` から選びます。
- 日本語テロップは必ずフォントで組みます（画像生成AIに文字を描かせない、という静止画と同じルールです）。
- リールカバー（`reel-cover.png`）は、動画の最初の1フレーム、またはアップロード時のカバー画像として使います。

## 第2フェーズで追加する予定のもの

1. `data/schema/reel.schema.json` とサンプル
2. `templates/video/`（下部テロップ、章タイトル、価格フラッシュ、CTA エンドカード）
3. `pipeline/video.mjs`（ffmpeg の合成処理。字幕の SRT も出力）
4. `scripts/premiere/`（書き出した FCPXML の読み込み手順。ASE と MOGRT の設定手順）
