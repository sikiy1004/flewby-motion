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
		start: 1.4,
		end: 11.4,
		cues: [
			'5人規模のベンチャーで、全員に個別面談。',
			'名目は、組織課題のヒアリング。',
			'実際の動機は、社長が従業員との関係に感じている不安です。',
		],
	},
	{
		sceneId: 'scene01',
		start: 1.0,
		end: 19.2,
		cues: [
			'まず、依頼を二本に分けます。',
			'本線は従業員5人。仕組み上の課題を把握します。',
			'副線は社長。不安そのものを扱います。',
			'一本化すると、従業員が「探りに来た」と察した時点で本音が出なくなる。',
			'副線を契約に明記しておけば、それが自分を守る盾になります。',
		],
	},
	{
		sceneId: 'scene02',
		start: 0.9,
		end: 16.3,
		cues: [
			'5人規模では、匿名化は原理的に不可能です。',
			'「傾向だけ返します」は、守れない約束になる。',
			'報告は個人の発言ではなく、仕組みの提案に変換して出す。',
			'特定されうる部分は、事前に本人へ見せて可否を確認します。',
		],
	},
	{
		sceneId: 'scene03',
		start: 0.9,
		end: 16.3,
		cues: [
			'性別の構図は、仮説として保留します。',
			'同内容の対立でも、女性同士だと観察者が深刻視しやすい。',
			'構造要因だけでも、不安は説明がつきます。',
			'仮説を持って入ると、発言をその物語に沿って読んでしまう。',
		],
	},
	{
		sceneId: 'scene04',
		start: 1.0,
		end: 21.2,
		cues: [
			'問いは、人でなくプロセスを主語にします。',
			'「社長との関係は」ではなく、「判断に迷って手が止まった場面は」。',
			'「不満はあるか」ではなく、「1つだけルールを変えられるなら何を変えるか」。',
			'「働きやすいか」ではなく、「やり直しになった仕事は」。',
		],
	},
	{
		sceneId: 'scene05',
		start: 1.0,
		end: 29.4,
		cues: [
			'冒頭では、全員に同一の文面を読み上げます。',
			'自分の立場と社長との関係を、自分から開示する。',
			'目的は仕組みの把握で、評価ではない。',
			'記録は手元保管、会社には渡さない。',
			'報告は提案の形。特定されうる箇所は本人に見せて可否を確認。',
			'例外は生命の危険と法令違反のみ。その場合も本人に先に伝える。',
			'パスは可。パスしたことも誰にも伝わらない。',
			'最後に必ず、「気になる点はありますか」と聞く。',
		],
	},
	{
		sceneId: 'scene06',
		start: 1.0,
		end: 17.2,
		cues: [
			'事前に確保するものは、三つ。',
			'地域産業保健センター、地さんぽ。',
			'50人未満は無料。医療につなぐ受け皿です。',
			'ストレスチェックの50人未満義務化は、2028年4月1日施行。',
			'そして、あかるい職場応援団の様式を手元に。',
		],
	},
	{
		sceneId: 'scene07',
		start: 1.0,
		end: 11.2,
		cues: [
			'読むものは、優先順に五つ。',
			'最優先は、Peter Block『Flawless Consulting』。',
			'その contracting の章です。',
		],
	},
	{
		sceneId: 'scene08',
		start: 1.0,
		end: 15.8,
		cues: [
			'最後に、事故の予防線。',
			'ヒアリング結果が「思ったほど問題なし」だった場合、',
			'社長の不安は「本音を話してくれていないのでは」に転移しやすい。',
			'副線の初回で、その結果が出たらどう受け止めるかを先に握っておく。',
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
