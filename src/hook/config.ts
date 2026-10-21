// flew by — Instagram 冒頭フック「WHERE TO NEXT?」の設定。
// 尺・カット割り・素材パス・スマホ画面のトラッキング値はすべてここで調整する。

export const HOOK = {width: 1080, height: 1920, fps: 30} as const;

/** カット境界（フレーム）。6.5 秒 = 195 フレーム。 */
export const CUTS = {
	cut01: {from: 0, to: 45}, // 0–1.5s   後方斜め上から、ゆっくり前進
	cut02: {from: 45, to: 105}, // 1.5–3.5s スマホへズーム → 手元の接写へマッチカット、検索入力
	cut03: {from: 105, to: 165}, // 3.5–5.5s 検索結果に flew by、指でタップ
	cut04: {from: 165, to: 195}, // 5.5–6.5s 広告の再生画面へ遷移、再生直前で終了
} as const;

export const TOTAL_FRAMES = CUTS.cut04.to;

/** 主要タイミング（フレーム）。接写素材の指の動きはここに合わせて素材側をトリムする。 */
export const TIMING = {
	matchCut: 72, // 引きの素材 → 手元接写素材に切り替えるフレーム
	typeFrom: 76, // 「すすきの バー」入力開始
	typeTo: 98, // 入力完了
	resultsIn: 106, // 検索結果が表示される
	tap: 150, // 指が広告に触れるフレーム（＝タップの瞬間）
	tapRelease: 155,
	viewerOpen: 158, // 広告の再生画面が開き始める
	viewerOpened: 170,
	pushFrom: 170, // 画面へ寄り切って本編の 1 フレーム目に合わせる
	pushTo: 188,
	handoffFrom: 180, // 本編 1 フレーム目（フル画面）へのクロスフェード
	handoffTo: 188,
} as const;

/** public/ 以下の素材。未配置のものはプレースホルダー表示になる（書き出しは止まらない）。 */
export const ASSET_PATHS = {
	/** CUT01 用 AI 生成映像：女性を後方斜め45°・やや高い位置から。背景はすすきの交差点（上 4 割にボケた看板）。1080×1920 / 30fps。 */
	wide: 'hook/cut01_wide.mp4',
	/** CUT02–04 用 AI 生成映像：肩越しの手元接写。指が画面をタップする動作を含む。 */
	closeup: 'hook/cut02_closeup.mp4',
	/**
	 * 任意：接写素材から指・手だけを切り抜いたアルファ付き動画（WebM VP9 / ProRes 4444）。
	 * 合成した画面の上に重ね、指が画面に触れて見えるようにする。cut02_closeup.mp4 と同じ尺・トリム。
	 */
	handForeground: 'hook/cut02_hand_fg.webm',
	/** Drive「flew byデザインデータ / flew by ロゴ透過.png」 */
	logo: 'hook/flewby_logo.png',
	/** 実店舗の写真（Drive「MKT02421.jpg」）。AI 再生成は禁止。 */
	storePhoto: 'hook/store_photo.jpg',
	/** 本編広告「flewby１０月広告動画文字入り.mp4」の 1 フレーム目（scripts/prepare-hook-assets.sh で書き出す）。 */
	mainAdFirstFrame: 'hook/main_ad_first_frame.jpg',
} as const;

export type AssetKey = keyof typeof ASSET_PATHS;
export type AssetAvailability = Record<AssetKey, boolean>;

export const NO_ASSETS: AssetAvailability = {
	wide: false,
	closeup: false,
	handForeground: false,
	logo: false,
	storePhoto: false,
	mainAdFirstFrame: false,
};

/** 素材の再生開始位置（素材内のフレーム）。指のタップを TIMING.tap に合わせるために使う。 */
export const FOOTAGE_TRIM = {wide: 0, closeup: 0} as const;

// ── スマホ画面のトラッキング ──────────────────────────────────────────
// 素材（1080×1920）上の画面 4 隅 [左上, 右上, 右下, 左下] を、素材内のフレーム番号ごとに指定する。
// 間は線形補間。実素材を入れたら Studio の showTrackingGuide で重ねて確認し、値を合わせる。
export type Point = [number, number];
export type Quad = [Point, Point, Point, Point];
export type TrackKey = {frame: number; quad: Quad};

export const SCREEN_TRACK: {wide: TrackKey[]; closeup: TrackKey[]} = {
	wide: [
		{frame: 0, quad: [[452, 1046], [688, 1068], [700, 1500], [430, 1474]]},
		{frame: 72, quad: [[454, 1040], [690, 1060], [702, 1494], [432, 1468]]},
	],
	closeup: [
		{frame: 0, quad: [[112, 96], [972, 124], [990, 1876], [92, 1850]]},
		{frame: 123, quad: [[108, 92], [976, 118], [994, 1880], [88, 1856]]},
	],
};

// ── 画面上の文言（すべてプログラムで描画） ──────────────────────────────
export const COPY = {
	query: 'すすきの バー',
	storeName: 'shisha cafe bar flew by',
	/** Instagram のユーザーネーム（@ なしで表示するのが Instagram の表記）。 */
	handle: 'flewby.sapporo' as string | null,
	/** 店舗企画書の記載（業態・立地）に基づく。 */
	category: 'シーシャバー · 札幌 すすきの',
	sponsored: '広告',
	cta: '詳しくはこちら',
	statusTime: '22:47',
} as const;
