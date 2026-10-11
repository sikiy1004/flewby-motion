import {Easing} from 'remotion';

// ── Color tokens (brief §2). RED is reserved for key numbers, warnings and emphasis.
export const COLORS = {
	black: '#111111',
	offWhite: '#F2F0EA',
	red: '#E63935',
	gray: '#B8B8B3',
} as const;

export type Tone = 'light' | 'dark';

export const toneColors = (tone: Tone) =>
	tone === 'light'
		? {bg: COLORS.offWhite, fg: COLORS.black, sub: '#6E6E6A', rule: COLORS.gray}
		: {bg: COLORS.black, fg: COLORS.offWhite, sub: COLORS.gray, rule: '#3A3A38'};

export const FONTS = {
	jp: '"Noto Sans JP", sans-serif',
	en: '"Inter", "Noto Sans JP", sans-serif',
} as const;

// ── Swiss grid: 12 columns inside 120px side margins.
export const VIDEO = {width: 1920, height: 1080, fps: 30} as const;

export const GRID = {
	columns: 12,
	marginX: 120,
	gutter: 24,
	headerY: 64,
	headerRuleY: 112,
	contentTop: 168,
	contentBottom: 860,
	subtitleY: 924,
} as const;

export const COL_W =
	(VIDEO.width - GRID.marginX * 2 - GRID.gutter * (GRID.columns - 1)) / GRID.columns;

/** Left x of column `n` (0-based). */
export const colX = (n: number) => GRID.marginX + n * (COL_W + GRID.gutter);
/** Width of a span of `n` columns including inner gutters. */
export const span = (n: number) => n * COL_W + (n - 1) * GRID.gutter;

// ── Motion: calm, regular, no bounce.
export const EASE = {
	out: Easing.bezier(0.16, 1, 0.3, 1),
	inOut: Easing.bezier(0.65, 0, 0.35, 1),
	line: Easing.bezier(0.45, 0, 0.2, 1),
} as const;

/** Spring preset with high damping so nothing overshoots. */
export const CALM_SPRING = {damping: 200, mass: 0.8, stiffness: 120} as const;
