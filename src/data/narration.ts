import type {SceneId} from './scenes';

// Narration script + subtitle timing, managed per scene.
//
// public/audio/narration.wav is expected to be ONE continuous file aligned to the
// 165-second timeline. Each scene plays the slice [start, end] of its own window.
// If a recorded take is offset, set `fileOffsetSec` to the second inside
// narration.wav where this scene's narration actually begins.
//
// Subtitle cues are distributed across [start, end] by character count. To pin a
// cue manually, give it `from`/`to` (seconds, relative to the scene start).

export type Cue = string | {text: string; from: number; to: number};

export type SceneNarration = {
	sceneId: SceneId;
	/** Narration start, seconds from scene start. */
	start: number;
	/** Narration end, seconds from scene start. */
	end: number;
	/** Where this segment starts inside narration.wav. Defaults to the scene's global start + `start`. */
	fileOffsetSec?: number;
	cues: Cue[];
};

export const NARRATION: SceneNarration[] = [
	{
		sceneId: 'scene00',
		start: 1.6,
		end: 10.8,
		cues: [
			'5人規模のベンチャー企業で、',
			'外部顧問が従業員面談を行うための設計メモ。',
			'その要点を、順に整理します。',
		],
	},
	{
		sceneId: 'scene01',
		start: 1.2,
		end: 18.6,
		cues: [
			'最初のポイントは、依頼を二本に分けることです。',
			'ひとつは、従業員面談。',
			'もうひとつは、社長自身の不安。',
			'この二つを一つの依頼にまとめず、',
			'それぞれ別の線として扱います。',
		],
	},
	{
		sceneId: 'scene02',
		start: 1.0,
		end: 15.8,
		cues: [
			'次に、5人という規模がもたらす制約です。',
			'人数の少ない組織では、',
			'誰が話したのかを伏せきることが難しい。',
			'匿名化には、限界があります。',
			'その前提に立って、面談を設計します。',
		],
	},
	{
		sceneId: 'scene03',
		start: 1.0,
		end: 15.8,
		cues: [
			'三つ目は、性別に関する構図の扱いです。',
			'性別による構図があるという見立ては、',
			'あくまで仮説として保留します。',
			'先入観として、面談に持ち込まないことが重要です。',
		],
	},
	{
		sceneId: 'scene04',
		start: 1.2,
		end: 20.4,
		cues: [
			'四つ目は、問いの立て方です。',
			'問いの主語を、人ではなく、',
			'プロセスに置きます。',
			'「誰が」ではなく、',
			'「どの流れの中で」起きたのかを尋ねる。',
			'個人ではなく、仕事の進め方に焦点を当てます。',
		],
	},
	{
		sceneId: 'scene05',
		start: 1.2,
		end: 28.4,
		cues: [
			'面談の冒頭では、',
			'あらかじめ用意した説明を読み上げます。',
			'説明すべき項目は、七つ。',
			'なかでも重要なのが、記録の扱いです。',
			'面談記録は、会社に渡しません。',
			'例外として扱うのは、',
			'生命の危険と、法令違反。',
			'この二つに限られます。',
		],
	},
	{
		sceneId: 'scene06',
		start: 1.0,
		end: 16.6,
		cues: [
			'面談の前には、',
			'三つの外部資源を確保しておきます。',
			'また原資料には、',
			'2028年4月1日の',
			'ストレスチェック義務化が記載されています。',
		],
	},
	{
		sceneId: 'scene07',
		start: 1.0,
		end: 10.8,
		cues: [
			'あわせて、資料には推奨文献が挙げられています。',
			'書名と著者は、原資料の表記のまま示します。',
		],
	},
	{
		sceneId: 'scene08',
		start: 1.0,
		end: 15.6,
		cues: [
			'最後に、事故の予防線です。',
			'面談の結果が、想定と異なった場合。',
			'そのリスクへの対策を、事前に定めておきます。',
			{text: '外部顧問・従業員面談 設計メモ。', from: 11.4, to: 13.9},
			{text: '以上です。', from: 14.2, to: 15.6},
		],
	},
];

export type TimedCue = {text: string; from: number; to: number};

const GAP_SEC = 0.25;

/**
 * Resolve cue timings (seconds, relative to scene start). Plain-string cues share
 * the time from `start` up to the first pinned cue (or `end`), by character count.
 */
export const timedCues = (n: SceneNarration): TimedCue[] => {
	const pinned = n.cues.filter((c): c is TimedCue => typeof c !== 'string');
	const plain = n.cues.filter((c): c is string => typeof c === 'string');
	const autoEnd = pinned.length > 0 ? Math.min(...pinned.map((c) => c.from)) - GAP_SEC : n.end;
	const totalChars = plain.reduce((a, c) => a + c.length, 0);
	const window = autoEnd - n.start - GAP_SEC * (plain.length - 1);
	let t = n.start;
	return n.cues.map((c) => {
		if (typeof c !== 'string') {
			return c;
		}
		const len = (c.length / totalChars) * window;
		const cue = {text: c, from: t, to: t + len};
		t += len + GAP_SEC;
		return cue;
	});
};

export const narrationFor = (id: SceneId) => NARRATION.find((n) => n.sceneId === id);
