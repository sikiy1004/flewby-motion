import type {SceneId} from './scenes';

// Audio file slots. Missing files are detected at load time and simply skipped,
// so the video previews and renders without any audio present.
export const AUDIO_FILES = {
	narration: 'audio/narration.wav',
	bgm: 'audio/bgm.mp3',
	sfx: {
		click: 'audio/sfx/click.wav',
		line: 'audio/sfx/line.wav',
		impact: 'audio/sfx/impact.wav',
		slide: 'audio/sfx/slide.wav',
	},
} as const;

export type SfxType = keyof typeof AUDIO_FILES.sfx;

// Mix levels: SFX and BGM stay well under the narration.
export const MIX = {
	narration: 1,
	bgm: 0.14,
	bgmDucked: 0.07,
	sfx: {click: 0.22, line: 0.16, impact: 0.3, slide: 0.18} as Record<SfxType, number>,
	fadeSec: 2,
};

/** SFX cues, seconds from scene start. Kept in sync with the scene animations. */
export const SFX_CUES: Record<SceneId, Array<{at: number; type: SfxType}>> = {
	scene00: [
		{at: 0.0, type: 'line'},
		{at: 0.3, type: 'click'},
		{at: 1.67, type: 'click'},
		{at: 1.95, type: 'impact'},
		{at: 2.8, type: 'line'},
		{at: 3.0, type: 'click'},
		{at: 4.67, type: 'click'},
		{at: 7.17, type: 'click'},
	],
	scene01: [
		{at: 0.0, type: 'slide'},
		{at: 1.0, type: 'click'},
		{at: 1.67, type: 'line'},
		{at: 3.33, type: 'click'},
		{at: 7.03, type: 'click'},
		{at: 10.0, type: 'line'},
		{at: 14.87, type: 'impact'},
	],
	scene02: [
		{at: 0.0, type: 'slide'},
		{at: 0.6, type: 'impact'},
		{at: 1.0, type: 'click'},
		{at: 1.9, type: 'line'},
		{at: 3.2, type: 'click'},
		{at: 7.3, type: 'line'},
		{at: 7.83, type: 'click'},
		{at: 12.1, type: 'click'},
	],
	scene03: [
		{at: 0.0, type: 'slide'},
		{at: 0.8, type: 'line'},
		{at: 2.4, type: 'slide'},
		{at: 4.0, type: 'click'},
		{at: 5.67, type: 'click'},
		{at: 8.5, type: 'click'},
		{at: 11.9, type: 'impact'},
	],
	scene04: [
		{at: 0.0, type: 'slide'},
		{at: 1.07, type: 'line'},
		{at: 4.6, type: 'click'},
		{at: 5.47, type: 'line'},
		{at: 10.23, type: 'click'},
		{at: 11.1, type: 'line'},
		{at: 16.67, type: 'click'},
		{at: 17.53, type: 'line'},
	],
	scene05: [
		{at: 0.0, type: 'slide'},
		{at: 1.0, type: 'impact'},
		{at: 2.0, type: 'line'},
		{at: 4.33, type: 'click'},
		{at: 7.93, type: 'click'},
		{at: 10.83, type: 'impact'},
		{at: 13.57, type: 'click'},
		{at: 18.07, type: 'impact'},
		{at: 22.7, type: 'click'},
		{at: 26.03, type: 'click'},
	],
	scene06: [
		{at: 0.0, type: 'slide'},
		{at: 1.0, type: 'impact'},
		{at: 3.0, type: 'line'},
		{at: 8.93, type: 'line'},
		{at: 9.6, type: 'impact'},
		{at: 13.77, type: 'line'},
	],
	scene07: [
		{at: 0.0, type: 'slide'},
		{at: 1.0, type: 'line'},
		{at: 1.33, type: 'click'},
		{at: 1.6, type: 'click'},
		{at: 1.87, type: 'click'},
		{at: 2.13, type: 'click'},
		{at: 2.4, type: 'click'},
		{at: 3.03, type: 'impact'},
	],
	scene08: [
		{at: 0.0, type: 'slide'},
		{at: 2.53, type: 'line'},
		{at: 2.8, type: 'click'},
		{at: 6.0, type: 'line'},
		{at: 6.6, type: 'click'},
		{at: 7.53, type: 'line'},
		{at: 11.0, type: 'impact'},
		{at: 13.0, type: 'slide'},
	],
};
