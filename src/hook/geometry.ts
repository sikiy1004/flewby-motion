import {staticFile} from 'remotion';
import {ASSET_PATHS, type AssetAvailability, type AssetKey, type Quad, type TrackKey} from './config';

/** Probe public/ for each asset slot so missing files fall back to placeholders. */
export const detectHookAssets = async (): Promise<AssetAvailability> => {
	const keys = Object.keys(ASSET_PATHS) as AssetKey[];
	const found = await Promise.all(
		keys.map(async (k) => {
			try {
				const res = await fetch(staticFile(ASSET_PATHS[k]), {method: 'HEAD'});
				const type = res.headers.get('content-type') ?? '';
				return res.ok && !type.includes('text/html');
			} catch {
				return false;
			}
		}),
	);
	return Object.fromEntries(keys.map((k, i) => [k, found[i]])) as AssetAvailability;
};

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Linear interpolation between tracked corner keyframes. */
export const quadAt = (track: TrackKey[], frame: number): Quad => {
	if (frame <= track[0].frame) return track[0].quad;
	const last = track[track.length - 1];
	if (frame >= last.frame) return last.quad;
	const i = track.findIndex((k) => k.frame > frame);
	const a = track[i - 1];
	const b = track[i];
	const t = (frame - a.frame) / (b.frame - a.frame);
	return a.quad.map((p, j) => [lerp(p[0], b.quad[j][0], t), lerp(p[1], b.quad[j][1], t)]) as Quad;
};

export const quadCenter = (q: Quad): [number, number] => [
	(q[0][0] + q[1][0] + q[2][0] + q[3][0]) / 4,
	(q[0][1] + q[1][1] + q[2][1] + q[3][1]) / 4,
];

/**
 * CSS matrix3d that maps the rect (0,0)-(w,h) onto quad (TL, TR, BR, BL).
 * Standard square-to-quad projective mapping (Heckbert).
 */
export const quadToMatrix3d = (w: number, h: number, q: Quad): string => {
	const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
	const dx1 = x1 - x2;
	const dx2 = x3 - x2;
	const dy1 = y1 - y2;
	const dy2 = y3 - y2;
	const sx = x0 - x1 + x2 - x3;
	const sy = y0 - y1 + y2 - y3;
	const den = dx1 * dy2 - dx2 * dy1;
	const g = (sx * dy2 - dx2 * sy) / den;
	const hh = (dx1 * sy - sx * dy1) / den;
	const a = x1 - x0 + g * x1;
	const b = x3 - x0 + hh * x3;
	const d = y1 - y0 + g * y1;
	const e = y3 - y0 + hh * y3;
	// Unit square → quad, pre-scaled by 1/w, 1/h. Column-major for matrix3d.
	const m = [a / w, d / w, 0, g / w, b / h, e / h, 0, hh / h, 0, 0, 1, 0, x0, y0, 0, 1];
	return `matrix3d(${m.map((v) => v.toFixed(10)).join(',')})`;
};
