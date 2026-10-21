# flew by｜Instagram 広告 冒頭フック「WHERE TO NEXT?」

本編広告の前に挿入する 6.5 秒（195 フレーム）の導入映像。
1080×1920 / 30fps / H.264。コンポジション ID は `FlewbyHook`、実装は `src/hook/`。

## カット割り（`src/hook/config.ts` の `CUTS` / `TIMING`）

| カット | 秒 | フレーム | 内容 |
|---|---|---|---|
| CUT01 | 0–1.5 | 0–45 | 後方斜め45°・やや高い位置。スマホは最初から画面内。カメラは 1.00→1.06 でゆっくり前進 |
| CUT02 | 1.5–3.5 | 45–105 | スマホへ滑らかにズーム（1.06→3.2）→ 72f で手元接写にマッチカット。76–98f で「すすきの バー」を入力 |
| CUT03 | 3.5–5.5 | 105–165 | 106f で検索結果。「shisha cafe bar flew by」のアカウントと広告投稿（実店舗写真）。**150f でタップ** |
| CUT04 | 5.5–6.5 | 165–195 | 158–170f で広告の再生画面へ遷移（一時停止・0:00）。170–188f で画面へ寄り、180–188f で本編 1 フレーム目にクロスフェード。188–195f は本編 1 フレーム目そのもの |

テロップ・派手なトランジションは入れていません。画面内の UI と文字はすべて React で描画しています。

## 必要な素材

`public/hook/` に置くと自動で読み込まれ、無いものは縞模様のプレースホルダーになります（プレビュー・書き出しは止まりません）。
`scripts/prepare-hook-assets.sh` を通すと、サイズ・fps・形式を揃えて所定のファイル名で配置します。

| ファイル | 内容 | 入手元 |
|---|---|---|
| `flewby_logo.png` | ロゴ（透過） | Drive「flew byデザインデータ / flew by ロゴ透過.png」 |
| `store_photo.jpg` | 広告投稿に出す実店舗写真 | Drive「MKT02421.jpg」 |
| `main_ad_first_frame.jpg` | 本編広告の 1 フレーム目 | Drive「flew by 動画 / flewby１０月広告動画文字入り.mp4」から `--main-ad` で自動抽出 |
| `susukino_crossing.jpg` | すすきの交差点の夜景（ニッカの看板・時計塔）を 9:16 に切り出した背景。AI 映像が届くまでのプレビュー背景、AI 生成時の背景参照 | 支給写真から `--bg-x 0.27 --background` で作成（配置済み） |
| `cut01_wide.mp4` | CUT01–02 の引き（AI 生成） | 下記プロンプト |
| `cut02_closeup.mp4` | CUT02–04 の手元接写（AI 生成） | 下記プロンプト |
| `cut02_hand_fg.webm` | 任意：接写から指・手だけを切り抜いたアルファ付き動画 | 接写素材をロトスコープ |

店舗の写真・動画・ロゴは実素材のみを使用し、AI での再生成はしません。

```bash
bash scripts/prepare-hook-assets.sh \
  --logo    "flew by ロゴ透過.png" \
  --store   "MKT02421.jpg" \
  --main-ad "flewby１０月広告動画文字入り.mp4" \
  --wide    cut01_wide.mp4 \
  --closeup cut02_closeup.mp4
```

## AI 生成映像のプロンプト

スマホの画面は後から Remotion で合成するので、**画面は真っ黒（消灯）またはグリーン一色**で生成します。画面の 4 隅がはっきり見えることが重要です。

### 背景：すすきの交差点（ニッカの看板・COCONO SUSUKINO）

背景は「すすきの交差点の夜。ニッカの看板と COCONO SUSUKINO がボケて写っている」状態にします。

- **使用する背景写真**：支給のすすきの交差点の写真（640×427）から、ニッカの看板と時計塔が入るように 9:16 で切り出した `public/hook/susukino_crossing.jpg` を使います。元の解像度が低いため 1080×1920 では粗くなりますが、ピントはスマホに合わせて背景はボカすので、ボケた背景としては十分使えます。
- **実写の写真を起点にする（推奨）**：AI に看板やビルをゼロから描かせると、ニッカの看板の人物やロゴ、ビルの外観が崩れ、「似ているけれど違う」看板になります。看板もビルも実在するので、交差点を実際に撮った夜の写真を **image-to-video の開始フレーム（または参照画像）** として渡し、女性と手元だけを生成します。Drive「Tontuからすすきのまで」の写真に交差点が写っているものがあれば、それが候補になります。無ければ、女性の肩越しの高さと向きで交差点を 1 枚撮ってください。
- **構図**：CUT01 で背景が見えるのは最初の約 1.5 秒だけです。後方斜め 45°・やや高い位置は保ったまま、カメラの下向きの角度を浅くし、**画面の上 4 割に交差点の看板が入る**ようにします。スマホと手は画面の下半分に置きます。CUT02 以降は画面に寄るので、交差点のネオンは色のついたボケとして残る程度で十分です。
- **ピント**：ピントはスマホに合わせ、看板とビルはボケさせます。形と色で「すすきの交差点だ」と分かれば十分で、看板の文字やロゴを読ませる必要はありません。
- **権利面の注意**：ニッカの看板は他社の商標、COCONO SUSUKINO は商業施設の名称です。街の風景として背景にボケて写るのが目安です。看板を主役に見せる、ロゴを読める大きさで写す、お酒の広告として提携しているように見える、といった使い方は避けてください。広告審査や権利の判断が気になる場合は、出稿前にご確認ください。

**cut01_wide（約 3 秒、9:16）** — 交差点の写真を開始フレームにして生成する

> Cinematic realism, DSLR photo look, 50mm lens, natural shallow depth of field. Night at the Susukino crossing in Sapporo, keep the background exactly as in the reference photo: the large illuminated whisky billboard and the modern COCONO SUSUKINO building stay in the upper part of the frame, softly out of focus, wet asphalt reflecting the neon. In the foreground a young woman seen from behind at a 45-degree angle, camera slightly above her shoulder and tilted only slightly down, looking at a smartphone held in both hands in the lower half of the frame; the phone is clearly visible from the first frame, its screen plain black. Natural skin and hair detail, subtle film grain, dark but natural color grade. Camera slowly dollies forward toward the phone. Do not add or change any text or signs.

**cut02_closeup（約 4.5 秒、9:16）**

> Same woman, same location, lighting and color grade. Over-the-shoulder close-up of her hands holding the smartphone; the phone fills most of the frame, screen plain black with visible corners. Behind her, the Susukino crossing neon is heavily defocused into warm and colored bokeh. At about 2.6 seconds her index finger taps once in the middle-lower part of the screen and lifts. Slow subtle push-in. 50mm look, shallow depth of field, subtle film grain. No text, no UI.

## 静止画 1 枚で作る（現在の構成）

`public/hook/woman_still.jpg`（肩越しにスマホを見ている女性の静止画、`--still` で配置）があり、動画素材（`cut01_wide.mp4` / `cut02_closeup.mp4`）が無い場合は、この 1 枚から引き → スマホへの寄り → 画面への寄りまでをカメラワークで作ります。

- カメラ：0–1.5 秒はゆっくり前進、1.5–2.8 秒で滑らかにスマホへ寄る（約 3.4 倍）、その後わずかに前進を続け、5.7–6.3 秒で画面に寄り切って本編 1 フレーム目へ。1 枚の写真なのでカットの切り替えはありません。
- 画面：写真のスマホ画面（ガラス部分）の 4 隅 `STILL.quad` に合わせて合成。
- 手前のもの：肩・右手・左手の指は `STILL.matte` の範囲を写真から切り抜いて画面の上に重ねるので、画面の下側は自然に肩に隠れます。
- タップ：写真なので指は動きません。押した瞬間の暗転と波紋、タップ音で表現しています。
- 画質：元の写真が 1000×1573 のため、寄ったときに手や袖はやや柔らかくなります（画面の UI はプログラム描画なので鮮明）。同じ写真の高解像度版（横 2000px 以上）があれば差し替えるだけで改善します。写真を差し替えて構図が変わった場合は `STILL.quad` / `STILL.matte` / `STILL.focus` を合わせ直します。

## 合成の調整

1. **画面の 4 隅**：`SCREEN_TRACK` に素材内フレームごとの 4 隅（左上・右上・右下・左下、1080×1920 座標）を入れます。間は線形補間です。Studio で Props の `showTrackingGuide: true` にすると水色の枠が出るので、実際の画面の縁に合うまで値を調整します。カメラが動く素材なら、キーフレームを数点増やします（AE / Mocha などのコーナーピン値をそのまま転記できます）。
2. **タップの同期**：接写素材で指が画面に触れるフレームが `TIMING.tap`（150f＝接写の 78f 目）に来るよう、`FOOTAGE_TRIM.closeup` で素材の開始位置をずらします。押下の暗転・波紋・効果音はすべて `TIMING.tap` 基準で動きます。
3. **指を画面の上に出す**：合成した画面は素材の上に載るため、そのままだと指が画面に隠れます。接写素材から手・指を切り抜いたアルファ付き動画を `--hand` で入れると、画面の上に重なります。
4. **本編との接続**：最後の 7 フレーム（188–194f）は本編 1 フレーム目の静止画だけで、グレイン・周辺減光も 0 にしています。本編をそのまま後ろにつなげば継ぎ目なく再生が始まります。

## VS Code だけで作業する場合

必要なのは **VS Code・Node.js（v18 以上）・Git** の 3 つです。ffmpeg は Remotion に同梱されているものを使うので、別に入れる必要はありません（`scripts/prepare-hook-assets.sh` は ffmpeg が無ければ自動で同梱版に切り替えます）。

1. VS Code の「ソース管理」→「リポジトリのクローン」で `https://github.com/sikiy1004/flewby-motion.git` を開き、左下のブランチ名から `claude/clever-edison-ld32bt` に切り替える。
2. メニュー「ターミナル」→「新しいターミナル」を開き、`npm install`。
   - **Windows** はターミナル右上の「∨」から **Git Bash** を選ぶ（素材準備スクリプトが bash のため）。
3. 素材を取り込む：`npm run hook:assets -- --logo … --store … --main-ad … --wide … --closeup …`
4. `npm run dev` → ブラウザで Studio が開くので、`FlewbyHook` を選んで確認・調整（`src/hook/config.ts` を VS Code で編集すると即座にプレビューに反映）。
5. `npm run hook:render` → `out/flewby-hook.mp4`。

## プレビュー・書き出し

```bash
npm run dev            # Studio で FlewbyHook を選択
npm run hook:render    # out/flewby-hook.mp4（H.264 / CRF 18 / yuv420p）
```

本編との接続確認（フックの最終フレームと本編冒頭を連結）：

```bash
ffmpeg -i out/flewby-hook.mp4 -i flewby１０月広告動画文字入り.mp4 \
  -filter_complex "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1[m];[0:v][m]concat=n=2:v=1:a=0" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p out/flewby-hook-joined.mp4
```

## 未確定事項

- Instagram のユーザーネームは `flewby.sapporo`（`COPY.handle`）。検索結果では 1 行目にユーザーネーム、2 行目に店名「shisha cafe bar flew by」を表示します。
- `out/flewby-hook-preview.mp4` は AI 映像・店舗写真・本編フレームが未配置の状態の確認用です（プレースホルダー表示）。
