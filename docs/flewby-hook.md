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
| `store_photo.jpg` | 広告投稿に出す実店舗写真 | Drive「家からflewby散歩」等の実写写真から 1 枚 |
| `main_ad_first_frame.jpg` | 本編広告の 1 フレーム目 | Drive「flew by 動画 / flewby１０月広告動画（文字入り）.mp4」から `--main-ad` で自動抽出 |
| `cut01_wide.mp4` | CUT01–02 の引き（AI 生成） | 下記プロンプト |
| `cut02_closeup.mp4` | CUT02–04 の手元接写（AI 生成） | 下記プロンプト |
| `cut02_hand_fg.webm` | 任意：接写から指・手だけを切り抜いたアルファ付き動画 | 接写素材をロトスコープ |

店舗の写真・動画・ロゴは実素材のみを使用し、AI での再生成はしません。

```bash
bash scripts/prepare-hook-assets.sh \
  --logo    "flew by ロゴ透過.png" \
  --store   "家からflewby散歩MKT02714.jpg" \
  --main-ad "flewby１０月広告動画文字入り.mp4" \
  --wide    cut01_wide.mp4 \
  --closeup cut02_closeup.mp4
```

## AI 生成映像のプロンプト

スマホの画面は後から Remotion で合成するので、**画面は真っ黒（消灯）またはグリーン一色**で生成します。画面の 4 隅がはっきり見えることが重要です。

**cut01_wide（約 3 秒、9:16）**

> Cinematic realism, DSLR photo look, 50mm lens, natural shallow depth of field. Night in Susukino, Sapporo: wet street, realistic neon signs softly out of focus. A young woman seen from behind at a 45-degree angle, camera slightly above her shoulder, looking down at a smartphone held in both hands; the phone is clearly visible in frame from the first frame, its screen plain black. Natural skin and hair detail, subtle film grain, dark but natural color grade. Camera slowly dollies forward toward the phone. No text, no logos.

**cut02_closeup（約 4.5 秒、9:16）**

> Same woman, same lighting and color grade. Over-the-shoulder close-up of her hands holding the smartphone; the phone fills most of the frame, screen plain black with visible corners. At about 2.6 seconds her index finger taps once in the middle-lower part of the screen and lifts. Slow subtle push-in. 50mm look, shallow depth of field, neon bokeh behind, subtle film grain. No text, no UI.

## 合成の調整

1. **画面の 4 隅**：`SCREEN_TRACK` に素材内フレームごとの 4 隅（左上・右上・右下・左下、1080×1920 座標）を入れます。間は線形補間です。Studio で Props の `showTrackingGuide: true` にすると水色の枠が出るので、実際の画面の縁に合うまで値を調整します。カメラが動く素材なら、キーフレームを数点増やします（AE / Mocha などのコーナーピン値をそのまま転記できます）。
2. **タップの同期**：接写素材で指が画面に触れるフレームが `TIMING.tap`（150f＝接写の 78f 目）に来るよう、`FOOTAGE_TRIM.closeup` で素材の開始位置をずらします。押下の暗転・波紋・効果音はすべて `TIMING.tap` 基準で動きます。
3. **指を画面の上に出す**：合成した画面は素材の上に載るため、そのままだと指が画面に隠れます。接写素材から手・指を切り抜いたアルファ付き動画を `--hand` で入れると、画面の上に重なります。
4. **本編との接続**：最後の 7 フレーム（188–194f）は本編 1 フレーム目の静止画だけで、グレイン・周辺減光も 0 にしています。本編をそのまま後ろにつなげば継ぎ目なく再生が始まります。

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

- Instagram のユーザーネームは未確定のため表示していません（`COPY.handle` に入れると表示されます）。
- `out/flewby-hook-preview.mp4` は AI 映像・店舗写真・本編フレームが未配置の状態の確認用です（プレースホルダー表示）。
