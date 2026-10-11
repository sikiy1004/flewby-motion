# 外部顧問・従業員面談 設計メモ — 解説動画（Remotion）

Swiss International Typographic Style をベースにした、約 165 秒の日本語解説動画です。
Remotion / React / TypeScript で構成し、1920×1080・30fps・H.264 MP4 で書き出します。

画面テキストとナレーションは、原資料「外部顧問・従業員面談 設計メモ」（作成 2026-09-18）の記載に基づいています。

## シーン構成

| # | ファイル | 尺 | 内容 |
|---|---|---|---|
| 00 | `src/scenes/Scene00.tsx` | 12s | オープニング（タイトル・前提4点） |
| 01 | `src/scenes/Scene01.tsx` | 20s | 依頼を二本に分ける（本線／副線 × 相手・目的・注意、分ける理由） |
| 02 | `src/scenes/Scene02.tsx` | 17s | 5人規模の制約（匿名化は原理的に不可能 → 提案に変換・本人確認） |
| 03 | `src/scenes/Scene03.tsx` | 17s | 性別の構図は仮説として保留する（problematization・クイーンビー現象・構造要因） |
| 04 | `src/scenes/Scene04.tsx` | 22s | 問いは人でなくプロセスを主語に（× → ○ の3組） |
| 05 | `src/scenes/Scene05.tsx` | 30s | 冒頭で読み上げる説明（7項目、読み上げ位置を表示） |
| 06 | `src/scenes/Scene06.tsx` | 18s | 事前に確保するもの（地さんぽ・ストレスチェック義務化・あかるい職場応援団） |
| 07 | `src/scenes/Scene07.tsx` | 12s | 読むもの（優先順の5点） |
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
    Typography.tsx      マスク出現・字間アニメーション・本文テキスト
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

- 文言は原資料からの転記・要約のみで、資料にない事実は加えていません。
- 匿名化は「原理的に不可能」と原資料どおりに表記しています。
- 例外は「生命の危険と法令違反のみ。その場合も本人に先に伝える」のまま扱っています。
- 「記録は手元保管、会社には渡さない」は原文どおりです。
- 性別の構図は「仮説として保留する」もので、確定事項として扱っていません。
- ストレスチェック50人未満義務化（2028年4月1日施行）は原資料の記載のまま示しています。
- 書名・著者・巻号・ページは原資料の表記のままです。
