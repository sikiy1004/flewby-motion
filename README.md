# 外部顧問・従業員面談 設計メモ — 解説動画（Remotion）

Swiss International Typographic Style をベースにした、約 165 秒の日本語解説動画です。
Remotion / React / TypeScript で構成し、1920×1080・30fps・H.264 MP4 で書き出します。

> **原資料（外部顧問_従業員面談_設計メモ.pdf）の転記待ち箇所があります。**
> PDF の原文が必要な箇所（冒頭説明の 7 項目、3 つの外部資源、推奨文献、リスク対策、二本立ての理由）は
> `src/data/scenes.ts` 内で `PDF("…")` と書かれており、画面上ではグレーの破線付き `［PDF｜…］` として表示されます。
> 原文に差し替えると、そのまま本番表示になります。

## シーン構成

| # | ファイル | 尺 | 内容 |
|---|---|---|---|
| 00 | `src/scenes/Scene00.tsx` | 12s | オープニング（タイトル・5人規模・目次） |
| 01 | `src/scenes/Scene01.tsx` | 20s | 依頼を二本に分ける（従業員面談／社長の不安） |
| 02 | `src/scenes/Scene02.tsx` | 17s | 5人規模の制約（匿名化の限界） |
| 03 | `src/scenes/Scene03.tsx` | 17s | 性別の構図は仮説として保留 |
| 04 | `src/scenes/Scene04.tsx` | 22s | 問いは人でなくプロセスを主語に |
| 05 | `src/scenes/Scene05.tsx` | 30s | 冒頭で読み上げる説明（7項目・記録の扱い・例外） |
| 06 | `src/scenes/Scene06.tsx` | 18s | 事前に確保するもの（3つの外部資源・2028年4月1日の記載） |
| 07 | `src/scenes/Scene07.tsx` | 12s | 読むもの（推奨文献） |
| 08 | `src/scenes/Scene08.tsx` | 17s | 事故の予防線・エンディング |

シーン間は 20 フレームのワイプでつなぎ、各シーンは公称秒数ちょうどに始まるよう調整しています（合計 165.0 秒 / 4950 フレーム）。

## ディレクトリ

```
src/
  Root.tsx              コンポジション登録（InterviewMemo + シーン単体）
  Video.tsx             9 シーンを TransitionSeries で統合、字幕・音声レイヤー
  theme.ts              カラー / フォント / 12 カラムグリッド / イージング
  fonts.ts              public/fonts のローカルフォントを読み込み
  scenes/Scene00–08.tsx 各シーン
  components/
    Typography.tsx      マスク出現・字間アニメーション・PDF プレースホルダー表示
    Grid.tsx            共通ページ枠（ヘッダー・罫線）とグリッドガイド
    AnimatedLine.tsx    strokeDasharray / strokeDashoffset による線描画
    Counter.tsx         遅れて出現する数字
    Transition.tsx      直線ワイプ（TransitionSeries 用）
    Subtitle.tsx        ナレーション同期字幕
    Sound.tsx           ナレーション / BGM / 効果音（ファイルが無ければ自動でスキップ）
  data/
    scenes.ts           シーン尺・画面テキスト（ここを編集すれば文言が変わる）
    narration.ts        ナレーション原稿・シーンごとの開始/終了位置・字幕
    sound.ts            音声ファイルのパス・音量・効果音タイミング
public/
  fonts/                Noto Sans JP / Inter（SIL OFL 1.1、ライセンス同梱）
  audio/narration.wav   ← ナレーションをここに置く（未配置でも動作）
  audio/bgm.mp3         ← BGM をここに置く（未配置でも動作）
  audio/sfx/*.wav       効果音（scripts/generate-sfx.sh で ffmpeg 合成）
```

## プレビュー

```bash
npm install
npm run dev          # Remotion Studio が http://localhost:3000 で起動
```

- `InterviewMemo` が本編、`Scenes/scene00`〜`scene08` が各シーン単体です。
- Studio の Props で `showGrid: true` にすると 12 カラムのグリッドガイドが表示されます。
- `showSubtitles: false` で字幕を非表示にできます。

## ナレーションの差し替え

1. 165 秒のタイムラインに合わせた 1 本の音声を `public/audio/narration.wav` として置きます。
   ファイルがあれば自動で読み込まれ、無ければ無音のままプレビュー・書き出しできます。
2. 原稿とタイミングは `src/data/narration.ts` で管理しています。
   - `start` / `end`：各シーン内でナレーションが始まる・終わる秒数（シーン先頭からの相対値）。
   - `fileOffsetSec`：収録音声の中でそのシーンの語りが始まる位置。音声がタイムラインとずれている場合に指定します。
   - `cues`：字幕。文字列だけなら `start`〜`end` に文字数比で自動配分、`{text, from, to}` で個別に固定できます。
3. 字幕の実際のタイミングは次で一覧できます（収録時の台本にも使えます）。

```bash
node scripts/print-cues.ts
```

BGM は `public/audio/bgm.mp3` に置くと再生され、ナレーション区間では自動で音量が下がります（`src/data/sound.ts` の `MIX`）。

## MP4 の書き出し

```bash
npm run render
# = remotion render InterviewMemo out/interview-memo.mp4 --codec=h264
```

Chrome Headless Shell をダウンロードできない環境では、ローカルのブラウザを指定します。

```bash
REMOTION_BROWSER=/path/to/headless_shell npm run render
```

出力先：`out/interview-memo.mp4`（1920×1080 / 30fps / H.264 / CRF 18 / yuv420p）

## 情報の正確性について

- 画面・ナレーションの文言は、制作指示書に明記された原資料の要点のみに基づいています。
- 匿名化できるとは表現せず、「匿名化には限界がある」としています。
- 例外は「生命の危険」「法令違反」の 2 つのみとし、追加していません。
- 「面談記録は会社に渡さない」は文言を変えずに扱っています。
- 2028年4月1日のストレスチェック義務化は「原資料の記載による」と明示しています。
- 書名・著者・各項目の原文は PDF から転記するまでプレースホルダーのままです。
