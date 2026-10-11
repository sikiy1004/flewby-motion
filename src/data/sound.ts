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
		{at: 1.95, type: 'impact'},
		{at: 2.8, type: 'line'},
		{at: 4.35, type: 'click'},
	],
	scene01: [
		{at: 0.0, type: 'slide'},
		{at: 1.35, type: 'click'},
		{at: 2.35, type: 'line'},
		{at: 3.35, type: 'line'},
		{at: 6.0, type: 'click'},
		{at: 8.6, type: 'click'},
		{at: 12.35, type: 'line'},
		{at: 13.35, type: 'impact'},
	],
	scene02: [
		{at: 0.0, type: 'slide'},
		{at: 0.8, type: 'impact'},
		{at: 4.67, type: 'click'},
		{at: 6.67, type: 'line'},
		{at: 8.75, type: 'click'},
		{at: 10.17, type: 'impact'},
	],
	scene03: [
		{at: 0.0, type: 'slide'},
		{at: 2.35, type: 'slide'},
		{at: 4.67, type: 'line'},
		{at: 8.35, type: 'click'},
		{at: 10.4, type: 'line'},
		{at: 11.35, type: 'impact'},
	],
	scene04: [
		{at: 0.0, type: 'slide'},
		{at: 1.67, type: 'click'},
		{at: 4.67, type: 'line'},
		{at: 6.67, type: 'line'},
		{at: 7.15, type: 'click'},
		{at: 10.6, type: 'line'},
		{at: 11.67, type: 'click'},
	],
	scene05: [
		{at: 0.0, type: 'slide'},
		{at: 3.15, type: 'line'},
		{at: 8.25, type: 'impact'},
		{at: 11.4, type: 'slide'},
		{at: 16.05, type: 'click'},
		{at: 19.9, type: 'click'},
		{at: 22.57, type: 'impact'},
	],
	scene06: [
		{at: 0.0, type: 'slide'},
		{at: 1.35, type: 'impact'},
		{at: 2.87, type: 'line'},
		{at: 7.07, type: 'line'},
		{at: 9.17, type: 'impact'},
		{at: 11.75, type: 'click'},
	],
	scene07: [
		{at: 0.0, type: 'slide'},
		{at: 2.0, type: 'click'},
		{at: 2.6, type: 'click'},
		{at: 3.2, type: 'click'},
		{at: 6.25, type: 'click'},
	],
	scene08: [
		{at: 0.0, type: 'slide'},
		{at: 3.35, type: 'line'},
		{at: 5.0, type: 'impact'},
		{at: 6.85, type: 'line'},
		{at: 9.87, type: 'slide'},
	],
};
