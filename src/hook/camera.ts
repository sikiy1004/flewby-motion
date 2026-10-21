import {Easing} from 'remotion';
import {HOOK, TIMING, type Quad} from './config';
import {quadCenter} from './geometry';

// Camera move modelled like a real dolly / zoom:
// - scale is animated in log space, so equal steps read as equal speed (no "rubber band" feel);
// - velocity is continuous everywhere, including across the match cut, where the close-up
//   picks up the wide shot's speed and then settles (ease-in on the wide, ease-out on the close-up);
// - a little handheld drift sits on top.

const CX = HOOK.width / 2;
const CY = HOOK.height / 2;

/** Slow forward creep present from the very first frame (log-scale units per frame). */
const DRIFT = 0.0012;
/** Wide shot: the zoom onto the phone eases in from here and is still moving at the match cut. */
const ZOOM_FROM = 38;
const WIDE_END_SCALE = 3.2;
/** Close-up: extra push after the cut, decaying with this time constant (frames). */
const SETTLE_AMOUNT = Math.log(1.06);
const SETTLE_TAU = 16;
const CLOSE_DRIFT = 0.00025;

/** Cubic Hermite from 0 to 1 with start/end slopes m0/m1 (in units of the interval). */
const hermite = (x: number, m0: number, m1: number) => {
	const t = Math.min(1, Math.max(0, x));
	const t2 = t * t;
	const t3 = t2 * t;
	return (t3 - 2 * t2 + t) * m0 + (-2 * t3 + 3 * t2) + (t3 - t2) * m1;
};

const ZOOM_LEN = TIMING.matchCut - ZOOM_FROM;
const ZOOM_LOG = Math.log(WIDE_END_SCALE) - DRIFT * TIMING.matchCut;
// End slope chosen so the wide shot leaves the cut at the close-up's starting speed.
const CUT_SPEED = SETTLE_AMOUNT / SETTLE_TAU + CLOSE_DRIFT;
const ZOOM_END_SLOPE = ((CUT_SPEED - DRIFT) * ZOOM_LEN) / ZOOM_LOG;

const wideLogScale = (f: number) => DRIFT * f + ZOOM_LOG * hermite((f - ZOOM_FROM) / ZOOM_LEN, 0, ZOOM_END_SLOPE);

const closeLogScale = (f: number) => {
	const t = Math.max(0, f - TIMING.matchCut);
	return SETTLE_AMOUNT * (1 - Math.exp(-t / SETTLE_TAU)) + CLOSE_DRIFT * t;
};

const pushEase = Easing.bezier(0.42, 0, 0.22, 1);

export type Camera = {s: number; fx: number; fy: number};

/** Scale and focus point (plate coords placed at frame center) for a global frame. */
export const cameraAt = (kind: 'wide' | 'closeup', frame: number, quad: Quad): Camera => {
	const [qx, qy] = quadCenter(quad);
	if (kind === 'wide') {
		const log = wideLogScale(frame);
		const k = log / Math.log(WIDE_END_SCALE);
		return {s: Math.exp(log), fx: CX + (qx - CX) * k, fy: CY + (qy - CY) * k};
	}
	// Close-up: settle, then a smooth push into the screen until the player fills the frame.
	const width = (quad[1][0] - quad[0][0] + quad[2][0] - quad[3][0]) / 2;
	const fill = HOOK.width / width;
	const base = Math.exp(closeLogScale(Math.min(frame, TIMING.pushFrom)));
	const p = pushEase(Math.min(1, Math.max(0, (frame - TIMING.pushFrom) / (TIMING.pushTo - TIMING.pushFrom))));
	const s = base * Math.pow(fill / base, p);
	return {s, fx: CX + (qx - CX) * p, fy: CY + (qy - CY) * p};
};

/** Smooth pseudo-random handheld drift: a few incommensurate sines per axis. */
const wobble = (f: number, seed: number) =>
	0.55 * Math.sin(f * 0.093 + seed) + 0.3 * Math.sin(f * 0.211 + seed * 2.3) + 0.15 * Math.sin(f * 0.47 + seed * 4.1);

/** Handheld offset in output pixels / degrees. Overscan in Plate hides the moving edges. */
export const handheldAt = (frame: number) => ({
	x: 3.2 * wobble(frame, 1.7),
	y: 2.6 * wobble(frame, 4.2),
	rot: 0.1 * wobble(frame, 7.9),
});

export const HANDHELD_OVERSCAN = 1.012;
