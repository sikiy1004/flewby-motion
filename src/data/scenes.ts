// Scene timing and on-screen text. All copy shown in the video lives here.
//
// Accuracy rule (brief §8): every string below is taken from the source memo
// 「外部顧問・従業員面談 設計メモ」(作成 2026-09-18). Wording is shortened only where
// the logic is kept; facts, titles, authors and dates are reproduced as written.

export const FPS = 30;
/** Overlap between neighbouring scenes. Scenes are padded so every scene still starts on its nominal second. */
export const TRANSITION_FRAMES = 20;

export type SceneId =
	| 'scene00'
	| 'scene01'
	| 'scene02'
	| 'scene03'
	| 'scene04'
	| 'scene05'
	| 'scene06'
	| 'scene07'
	| 'scene08';

export type SceneMeta = {
	id: SceneId;
	/** Chapter number shown in the header ("01"…"08"); the opening has none. */
	chapter: string | null;
	durationSec: number;
	label: string;
	title: string;
	tone: 'light' | 'dark';
	/** Optional tone change partway through the scene (seconds from scene start), e.g. the closing panel. */
	toneShift?: {at: number; tone: 'light' | 'dark'};
};

export const SCENES: SceneMeta[] = [
	{id: 'scene00', chapter: null, durationSec: 12, label: 'OPENING', title: 'オープニング', tone: 'dark'},
	{id: 'scene01', chapter: '01', durationSec: 20, label: 'TWO TRACKS', title: '依頼を二本に分ける', tone: 'light'},
	{id: 'scene02', chapter: '02', durationSec: 17, label: 'SCALE CONSTRAINT', title: '5人規模の制約', tone: 'light'},
	{id: 'scene03', chapter: '03', durationSec: 17, label: 'HYPOTHESIS ON HOLD', title: '性別の構図は仮説として保留する', tone: 'light'},
	{id: 'scene04', chapter: '04', durationSec: 22, label: 'PROCESS AS SUBJECT', title: '問いは人でなくプロセスを主語に', tone: 'light'},
	{id: 'scene05', chapter: '05', durationSec: 30, label: 'OPENING STATEMENT', title: '冒頭で読み上げる説明', tone: 'light'},
	{id: 'scene06', chapter: '06', durationSec: 18, label: 'SECURE IN ADVANCE', title: '事前に確保するもの', tone: 'light'},
	{id: 'scene07', chapter: '07', durationSec: 12, label: 'READING', title: '読むもの（優先順）', tone: 'light'},
	{id: 'scene08', chapter: '08', durationSec: 17, label: 'SAFEGUARD', title: '事故の予防線', tone: 'light', toneShift: {at: 13.9, tone: 'dark'}},
];

export const DOC_TITLE = '外部顧問・従業員面談 設計メモ';
export const DOC_DATE = '作成 2026-09-18';
export const TOTAL_CHAPTERS = '08';

const sceneStartSec = (id: SceneId) => {
	let t = 0;
	for (const s of SCENES) {
		if (s.id === id) {
			return t;
		}
		t += s.durationSec;
	}
	throw new Error(`Unknown scene ${id}`);
};

/** Global start frame of a scene on the final timeline. */
export const sceneStartFrame = (id: SceneId) => Math.round(sceneStartSec(id) * FPS);

export const TOTAL_SEC = SCENES.reduce((a, s) => a + s.durationSec, 0);
export const TOTAL_FRAMES = Math.round(TOTAL_SEC * FPS);

// ── On-screen copy ─────────────────────────────────────────────────────────

export const COPY = {
	scene00: {
		kicker: 'EXTERNAL ADVISOR × EMPLOYEE INTERVIEW',
		titleLines: ['外部顧問・従業員面談', '設計メモ'],
		scaleNumber: 5,
		scaleUnit: '人規模',
		scaleLabel: 'PERSONS',
		premises: [
			{label: 'SCALE', text: '5人規模ベンチャー'},
			{label: 'FORMAT', text: '全員に個別面談'},
			{label: 'NOMINAL', text: '名目は組織課題のヒアリング'},
			{label: 'ACTUAL MOTIVE', text: '実際の動機は社長が従業員との関係に感じている不安'},
		],
	},
	scene01: {
		heading: '依頼を二本に分ける',
		origin: '依頼',
		fields: ['相手', '目的', '注意'],
		tracks: [
			{key: '本線', en: 'MAIN', cells: ['従業員5人', '仕組み上の課題の把握', '社長の不安の話を持ち込まない']},
			{key: '副線', en: 'SUB', cells: ['社長', '不安そのものを扱う', 'おまけ扱いにしない']},
		],
		reasons: [
			'一本化すると、従業員が「探りに来た」と察した時点で本音が出なくなる。',
			'副線を契約に明記しておくことが、「聞いた話を社長に流す」圧力から自分を守る盾になる。',
		],
	},
	scene02: {
		heading: '5人規模の制約',
		number: 5,
		unit: '人',
		unitEn: 'PERSONS',
		statement: '発言',
		limitLabel: 'ANONYMITY',
		limit: '匿名化は原理的に不可能',
		promise: '「傾向だけ返します」は守れない約束になる。',
		responseLabel: 'THEREFORE',
		responses: [
			'報告は個人の発言ではなく「こういう仕組みを入れませんか」という提案に変換して出す。',
			'特定されうる部分は事前に本人へ見せて可否を確認。',
		],
	},
	scene03: {
		heading: '性別の構図は、仮説として保留する',
		hypothesisLabel: 'HYPOTHESIS',
		hypothesisTag: '仮説',
		hypothesis: '性別の構図',
		holdLabel: 'ON HOLD',
		hold: '保留',
		notes: [
			{label: 'PROBLEMATIZATION', text: '同内容の対立でも、当事者が女性同士だと観察者が深刻視しやすい。'},
			{label: 'QUEEN BEE', text: 'クイーンビー現象も女性の特性ではなく格差の産物とされる。'},
		],
		structureLabel: 'STRUCTURE',
		structure: ['5人', '逃げ場なし', '社長の判断が全員の生活に直結'],
		structureNote: '構造要因だけでも不安は説明がつく。',
		risk: '仮説を持って入ると、発言をその物語に沿って読んでしまう。',
		check: '副線で「いつから意識したか」を検証する。',
	},
	scene04: {
		heading: '問いは、人でなくプロセスを主語に',
		badLabel: 'PERSON AS SUBJECT',
		goodLabel: 'PROCESS AS SUBJECT',
		pairs: [
			{bad: '「社長との関係は」', good: '「判断に迷って手が止まった場面は。誰にどう確認した」'},
			{bad: '「不満はあるか」', good: '「1つだけルールを変えられるなら何を変えるか」'},
			{bad: '「働きやすいか」', good: '「やり直しになった仕事は。何が分かっていれば防げたか」'},
		],
	},
	scene05: {
		heading: '冒頭で読み上げる説明',
		count: 7,
		countLabel: 'ITEMS',
		countUnit: '項目',
		sameText: '全員に同一文面',
		items: [
			{text: '自分の立場と社長との関係を、自分から開示する'},
			{text: '目的は仕組みの把握であり、評価ではない'},
			{text: '記録は手元保管、会社には渡さない', key: true},
			{text: '報告は提案の形。特定されうる箇所は本人に見せて可否を確認する'},
			{text: '例外は生命の危険と法令違反のみ。その場合も本人に先に伝える', key: true},
			{text: '「パス」可。パスしたことも誰にも伝わらない'},
			{text: '最後に「気になる点はありますか」と必ず聞く', note: 'ここで出る質問が警戒の所在を示す'},
		] as Array<{text: string; key?: boolean; note?: string}>,
	},
	scene06: {
		heading: '事前に確保するもの',
		count: 3,
		countLabel: 'SECURE BEFORE THE INTERVIEWS',
		resources: [
			{
				title: '地域産業保健センター（地さんぽ）',
				body: '50人未満は無料。産業医不在の会社で医療につなぐ受け皿。面談開始前に連絡してルートを通す。',
				url: 'kokoro.mhlw.go.jp/health-center/',
			},
			{
				title: 'ストレスチェック50人未満義務化',
				date: '2028.04.01',
				dateNote: '施行',
				body: '小規模事業場向けマニュアル・モデル規程が公開済み。今作る仕組みをこの枠に接続すれば後で作り直さずに済む。',
			},
			{
				title: 'あかるい職場応援団',
				body: '相談受付票・行為者聞き取り票の様式を手元に。',
				url: 'no-harassment.mhlw.go.jp/download/',
			},
		] as Array<{title: string; body: string; url?: string; date?: string; dateNote?: string}>,
	},
	scene07: {
		heading: '読むもの',
		headingEn: 'READING — IN ORDER OF PRIORITY',
		order: '優先順',
		books: [
			{author: 'Peter Block', title: '『Flawless Consulting』', detail: 'contracting の章', note: '最優先', top: true},
			{author: 'Amy Edmondson', title: '『恐れのない組織』', note: '結果を社長に返すときの共通言語'},
			{author: 'Edgar Schein', title: '『問いかける技術』', note: '誘導尋問を避けるための確認用'},
			{author: '', title: '『心理職のための産業保健入門』', detail: '（金剛出版）第I部・第7章'},
			{author: 'Sheppard & Aquino (2017)', title: 'Journal of Management 43, 691-715', note: '自分用の解毒剤'},
		] as Array<{author: string; title: string; detail?: string; note?: string; top?: boolean}>,
	},
	scene08: {
		heading: '事故の予防線',
		resultLabel: 'HEARING RESULT',
		result: '「思ったほど問題なし」',
		resultCaption: 'ヒアリング結果が',
		anxietyLabel: "CEO'S ANXIETY",
		anxiety: '社長の不安',
		shiftLabel: '転移しやすい',
		shifted: '「本音を話してくれていないのでは」',
		safeguardLabel: 'SAFEGUARD',
		safeguard: '副線の初回で、その結果が出たらどう受け止めるかを先に握っておく。',
		endKicker: 'END',
		endTitle: DOC_TITLE,
		endDate: DOC_DATE,
	},
} as const;
