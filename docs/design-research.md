# デザインリサーチとリニューアル方針（2026-11）

「AIで作ったシンプルすぎるデザイン」を脱するために、伸びている競合・2026年のSNSデザイン/動画編集トレンドを調べ、カルーセルと動画を作り直した記録です。

## 1. リサーチの範囲と限界

- Web検索で、2026年のカルーセル/リール編集トレンド記事、美容インフルエンサー・美容メディアのランキング記事を調査。
- **Instagram 本体や個別アカウントの投稿・再生数は、この実行環境のネットワーク制限で直接閲覧できませんでした**（instagram.com ほか一部サイトが接続不可）。そのため、個別アカウントの数値比較ではなく「上位アカウント・メディアに共通するフォーマット」を抽出しています。
- 記事中の数値（保存率など）は出典ごとに差が大きく、独立検証されたものではありません。最終的には自アカウントのインサイトで検証します（システムの Thompson Sampling が自動で行います）。

## 2. わかったこと

### 伸びているアカウント・メディアの傾向
| 観察 | 出典 |
|---|---|
| 美容ジャンルのフォロワー上位には、個人インフルエンサーに加えて EMME・shabon・美的など**メディア型アカウント**が並ぶ（＝「雑誌・編集部」っぽい見せ方が強い） | [美容インフルエンサーランキング（2026年9月）](https://influencer.tri-as.co.jp/ranking/beauty.html) |
| 美容家電は単価が高く、購入前に SNS のレビューを深く参考にされやすい | [美容家電のインフルエンサータイアップ事例](https://find-model.jp/insta-lab/influencers-pr-beauty-appliances-2024/) |
| 美容家電メーカー公式（パナソニックビューティ、ヤーマン等）は、映える画像とリールでのストーリーテリングが中心 | [美容家電の公式アカウント](https://find-model.jp/insta-lab/instagram-beauty-appliances-accounts/) |
| 比較メディアは「ランキング＋採点＋選び方」で構成（例: mybest、美的のベスコス） | [mybest 美容家電ランキング](https://my-best.com/13411)、[美的 美容家電](https://www.biteki.com/2094786/) |

### カルーセルのトレンド（2026）
- **1枚1メッセージ・大きな文字・最後に「保存する理由」**、配色を統一してプロフィール一覧で揃える（[Ceeev](https://ceeev.co.jp/blog/instagram-carousel-guide-2026/)、[slooooth](https://media.slooooth.com/instagram-carousel/)、[neworder](https://www.neworder.co.jp/2026/10/08/instagram-carousel-howto/)）
- 表紙は「目次」として設計し、スワイプさせる（同上）
- **AIっぽい均質さへの反動として、手描き線・紙の質感・コラージュ・雑誌風レイアウト**が流行（[kaerunokuni 2026デザイントレンド](https://kaeru555.com/)、[ISSOH](https://www.issoh.co.jp/column/details/1893/)）
- 海外でも **エディトリアル（雑誌）・セリフ体の大きな数字・スクラップブック/手書きメモ・紙テクスチャ** が上昇トレンド（[Slidy](https://slidycreator.com/blog/instagram-carousel-trends/)、[whaaat.ai](https://www.whaaat.ai/blog/instagram-carousel-trends-2026-12-formats-blowing-up-right-now)、[Scrolo](https://scrolo.app/blog/top-trending-instagram-carousel-design-ideas-in-2026)）
- フォントは見出し・本文の2系統に絞る、3色程度に絞る（[namaste-design](https://namaste-design.com/blog/instagram-feed-design-basics/)）

### リール編集のトレンド（2026）
- **冒頭1〜3秒で結論・強いテロップ・画面の変化**（[cocomarke](https://www.cocomarke.com/blog/instagram-reels-growth-guide-2026/)、[マーケティングワン](https://marketingone.co.jp/instagram-reels-cvr-creative-guide-2026/)）
- **音声オフでも分かる焼き込みテロップは必須**（[convertaudiototext](https://convertaudiototext.com/ja/blog/captioning-for-tiktok-instagram)、マーケティングワン）
- **2〜3秒ごとのカット切り替え**、評価軸は視聴維持率と保存・シェア（[gyaku-ten](https://gyaku-ten.jp/column/instagram-20260710)、cocomarke）
- 結果を先に見せる構成（ランキングならカウントダウン）

## 3. 新デザイン「BIKADEN Note」

| 方針 | 実装 |
|---|---|
| メディア型・雑誌っぽさ | 毎枚に誌名ヘッダー「BIKADEN Note vol.042」＋罫線、セリフ体（DM Serif Display）の大きな数字・価格 |
| AIっぽさの排除（手触り） | 方眼ノート＋紙ノイズの背景、マスキングテープ、手書き文字（Klee One）、手描き矢印、付箋、ゴム印風スタンプ |
| 比較アカウントの定番 | **◎○△の比較表**、**データスコア（100点）**、**レーダーチャート**、「結論：タイプ別に選ぶなら」 |
| 写真なしでも寂しくない | ジャンル別の**自作イラスト（SVG）**とアイコン。権利フリー |
| 保存させる設計 | 表紙に「保存版」、最後に「保存して見返して」＋「保存はここから」の手書き誘導 |
| 統一感 | 配色テーマ4種（kraft / rose / sage / noir）。成績で自動選択 |

数字（価格・順位・口コミ・スコア・◎○△）は**すべて楽天の実データから計算**し、AIには作らせません。データスコアは「レビュー評価40%・口コミ数30%・価格20%・機能数10%」の独自指標で、画像内に算出方法を明記しています。

### 動画（Remotion で作り直し）
| 時間 | 演出 |
|---|---|
| 0〜0.5秒 | 見出しが文節ごとにポップ→蛍光マーカーが走る、「保存版」スタンプが落ちる（効果音） |
| 冒頭〜 | 上部に**ストーリーズ風の進行バー**（最後まで見る動機） |
| 商品ごと（約4〜6秒） | 斜めワイプで切り替え→順位の大きな数字→イラスト回転イン→商品名タイプライター→**価格カウントアップ**→星が満ちる→◎○△がポン→**スコアのリングが伸びる**→途中でズームパンチ（擬似カット） |
| ランキング | **3位→2位→1位のカウントダウン** |
| 字幕 | 白文字＋太フチ、数字・キーワードは黄色、読み上げ中の文節が跳ねる（VOICEVOX の発話タイミングに同期） |
| 音 | 120BPM のビート入り BGM（自動生成・権利フリー、ナレーション中は自動で下げる）、ワイプ/ポップ/インパクト効果音、-14 LUFS に正規化 |

## 4. さらに伸ばすための次の一手（任意）
1. **商品画像の使用**：最も効果が大きいのは実物写真です。楽天・各ASPの素材利用規約を確認できたら `content.use_product_images: true`。
2. **BGM**：Instagram のトレンド音源は API 投稿では使えないため、商用可の人気系 BGM を `assets/bgm/` に入れると雰囲気が上がります。
3. **Pexels キー**：冒頭の背景に実写の縦動画が入り、より「人の生活感」が出ます。
4. 運用 1〜2 か月後、保存率の高いテーマ・フックに自動で寄っていくので、週次レポートを見て新しいテンプレートを足していくのがおすすめです。
