// Scene timing and on-screen text. All copy shown in the video lives here.
//
// Accuracy rule (brief §8): only wording that is grounded in the source memo
// (外部顧問_従業員面談_設計メモ.pdf) may appear. Anything that must be transcribed
// from the PDF and is not yet available is wrapped with PDF(), which renders as a
// visibly marked gray placeholder. Replace PDF("…") with the original wording.

export const PDF_MARK = '［PDF｜';
export const PDF = (what: string) => `${PDF_MARK}${what}］`;
export const isPdfPlaceholder = (text: string) => text.startsWith(PDF_MARK);

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
	{id: 'scene03', chapter: '03', durationSec: 17, label: 'HYPOTHESIS ON HOLD', title: '性別の構図は仮説として保留', tone: 'light'},
	{id: 'scene04', chapter: '04', durationSec: 22, label: 'PROCESS AS SUBJECT', title: '問いは人でなくプロセスを主語に', tone: 'light'},
	{id: 'scene05', chapter: '05', durationSec: 30, label: 'OPENING STATEMENT', title: '冒頭で読み上げる説明', tone: 'light'},
	{id: 'scene06', chapter: '06', durationSec: 18, label: 'SECURE IN ADVANCE', title: '事前に確保するもの', tone: 'light'},
	{id: 'scene07', chapter: '07', durationSec: 12, label: 'READING', title: '読むもの', tone: 'light'},
	{id: 'scene08', chapter: '08', durationSec: 17, label: 'SAFEGUARDS', title: '事故の予防線', tone: 'light', toneShift: {at: 10.8, tone: 'dark'}},
];

export const DOC_TITLE = '外部顧問・従業員面談 設計メモ';
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
		titleLines: ['外部顧問・', '従業員面談', '設計メモ'],
		subtitle: '5人規模のベンチャー企業における、面談設計の要点',
		scaleNumber: 5,
		scaleUnit: '人規模',
		scaleLabel: 'PERSONS',
	},
	scene01: {
		heading: '依頼を二本に分ける',
		lead: '一つの依頼にまとめず、別々の線として扱う。',
		origin: '依頼',
		tracks: [
			{key: 'A', jp: '従業員面談', en: 'EMPLOYEE INTERVIEWS'},
			{key: 'B', jp: '社長の不安', en: "THE CEO'S CONCERNS"},
		],
		whyLabel: 'WHY',
		why: PDF('二本立てで扱う理由'),
	},
	scene02: {
		heading: '5人規模の制約',
		number: 5,
		unit: '人',
		unitEn: 'PERSONS',
		statement: '発言',
		limitLabel: 'LIMIT OF ANONYMITY',
		limit: '匿名化には限界がある',
		premise: 'その前提に立って、面談を設計する。',
	},
	scene03: {
		heading: '性別の構図は、仮説として保留',
		hypothesisLabel: 'HYPOTHESIS',
		hypothesis: '性別による構図',
		hypothesisTag: '仮説',
		holdLabel: 'ON HOLD',
		hold: '保留',
		interviewLabel: 'INTERVIEW',
		interview: '面談',
		barrier: '先入観として持ち込まない',
	},
	scene04: {
		heading: '問いは、人でなくプロセスを主語に',
		person: {label: 'SUBJECT : PERSON', jp: '主語＝人'},
		process: {label: 'SUBJECT : PROCESS', jp: '主語＝プロセス', steps: ['01', '02', '03', '04']},
		phraseFrom: '「誰が」',
		phraseTo: '「どの流れの中で」',
		focus: '個人ではなく、仕事の進め方に焦点を当てる。',
	},
	scene05: {
		heading: '冒頭で読み上げる説明',
		count: 7,
		countLabel: 'ITEMS',
		countUnit: '項目',
		items: [
			PDF('説明項目 1'),
			PDF('説明項目 2'),
			PDF('説明項目 3'),
			PDF('説明項目 4'),
			PDF('説明項目 5'),
			PDF('説明項目 6'),
			PDF('説明項目 7'),
		],
		recordLabel: 'RECORDS',
		recordLines: ['面談記録は', '会社に渡さない'],
		exceptionLabel: 'EXCEPTIONS',
		exceptions: ['生命の危険', '法令違反'],
		exceptionNote: '例外はこの2つのみ',
	},
	scene06: {
		heading: '事前に確保するもの',
		count: 3,
		countLabel: 'EXTERNAL RESOURCES',
		resources: [PDF('外部資源 1'), PDF('外部資源 2'), PDF('外部資源 3')],
		dateLabel: 'SOURCE NOTE',
		date: '2028.04.01',
		dateText: 'ストレスチェック義務化',
		dateNote: '原資料の記載による',
	},
	scene07: {
		heading: '読むもの',
		headingEn: 'RECOMMENDED READING',
		note: '書名・著者は原資料の表記のまま掲載',
		books: [
			{title: PDF('書名・論文名 1'), author: PDF('著者 1')},
			{title: PDF('書名・論文名 2'), author: PDF('著者 2')},
			{title: PDF('書名・論文名 3'), author: PDF('著者 3')},
		],
	},
	scene08: {
		heading: '事故の予防線',
		expected: '想定',
		expectedEn: 'EXPECTED',
		actual: '面談結果',
		actualEn: 'ACTUAL',
		gap: 'GAP',
		measuresLabel: 'COUNTERMEASURES',
		measures: [PDF('リスク対策 1'), PDF('リスク対策 2'), PDF('リスク対策 3')],
		endKicker: 'END',
		endTitle: DOC_TITLE,
	},
} as const;
