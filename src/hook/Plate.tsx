import React from 'react';
import {AbsoluteFill, Easing, Img, OffthreadVideo, interpolate, random, staticFile, useCurrentFrame} from 'remotion';
import {ASSET_PATHS, CUTS, FOOTAGE_TRIM, HOOK, SCREEN_TRACK, TIMING, type AssetAvailability, type Quad} from './config';
import {quadAt, quadCenter, quadToMatrix3d} from './geometry';
import {InstagramScreen, SCREEN} from './InstagramScreen';

export type PlateKind = 'wide' | 'closeup';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;
const CX = HOOK.width / 2;
const CY = HOOK.height / 2;

/** Camera as (scale, focus point in plate coords). The focus point is placed at frame center. */
const cameraAt = (kind: PlateKind, frame: number, quad: Quad) => {
	const [qx, qy] = quadCenter(quad);
	if (kind === 'wide') {
		// CUT01: slow dolly-in from the first frame. CUT02: smooth zoom onto the phone into the match cut.
		const s =
			frame < CUTS.cut01.to
				? interpolate(frame, [0, CUTS.cut01.to], [1, 1.06])
				: interpolate(frame, [CUTS.cut01.to, TIMING.matchCut], [1.06, 3.2], {...clamp, easing: Easing.in(Easing.quad)});
		const k = (s - 1) / 2.2;
		return {s, fx: CX + (qx - CX) * k, fy: CY + (qy - CY) * k};
	}
	// Close-up: keep a slow push, then push into the screen until the player fills the frame.
	const width = (quad[1][0] - quad[0][0] + quad[2][0] - quad[3][0]) / 2;
	const fill = HOOK.width / width;
	const base = interpolate(frame, [TIMING.matchCut, TIMING.pushFrom], [1, 1.035], clamp);
	const p = interpolate(frame, [TIMING.pushFrom, TIMING.pushTo], [0, 1], {...clamp, easing: Easing.bezier(0.45, 0, 0.2, 1)});
	const s = base + (fill - base) * p;
	return {s, fx: CX + (qx - CX) * p, fy: CY + (qy - CY) * p};
};

const expandQuad = (q: Quad, k: number): Quad => {
	const [cx, cy] = quadCenter(q);
	return q.map(([x, y]) => [cx + (x - cx) * k, cy + (y - cy) * k]) as Quad;
};

/**
 * Stand-in plate so the timing can be reviewed before the AI footage exists.
 * Uses the Susukino crossing photo as the defocused background when it is in public/hook.
 */
const PlaceholderPlate: React.FC<{kind: PlateKind; quad: Quad; hasBackground: boolean}> = ({kind, quad, hasBackground}) => {
	const lights = Array.from({length: 26}, (_, i) => ({
		x: random(`x${i}`) * HOOK.width,
		y: random(`y${i}`) * HOOK.height * 0.75,
		r: 30 + random(`r${i}`) * 110,
		hue: [330, 285, 200, 25, 350][i % 5],
		a: 0.18 + random(`a${i}`) * 0.3,
	}));
	const body = expandQuad(quad, kind === 'wide' ? 1.08 : 1.05);
	return (
		<AbsoluteFill style={{background: 'radial-gradient(120% 80% at 50% 30%, #1b1420 0%, #0b0a0f 60%, #050507 100%)'}}>
			{hasBackground ? (
				// Focus is on the phone: the crossing stays soft, and goes to pure bokeh in the close-up.
				<AbsoluteFill style={{filter: `blur(${kind === 'wide' ? 7 : 22}px) brightness(0.8) saturate(1.05)`, transform: 'scale(1.04)'}}>
					<Img src={staticFile(ASSET_PATHS.background)} style={{width: HOOK.width, height: HOOK.height, objectFit: 'cover'}} />
				</AbsoluteFill>
			) : null}
			<AbsoluteFill style={{filter: 'blur(18px)', display: hasBackground ? 'none' : undefined}}>
				{lights.map((l, i) => (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: l.x - l.r,
							top: l.y - l.r,
							width: l.r * 2,
							height: l.r * 2,
							borderRadius: '50%',
							background: `hsla(${l.hue}, 85%, 60%, ${l.a})`,
						}}
					/>
				))}
			</AbsoluteFill>
			{kind === 'wide' ? (
				// Rough shoulder / hair mass seen from behind, out of focus.
				<div
					style={{
						position: 'absolute',
						left: -260,
						top: 980,
						width: 820,
						height: 1200,
						borderRadius: '45% 55% 0 0',
						background: 'linear-gradient(160deg, #19151a, #070608)',
						filter: 'blur(10px)',
					}}
				/>
			) : null}
			<div
				style={{
					position: 'absolute',
					left: 0,
					top: 0,
					width: SCREEN.w,
					height: SCREEN.h,
					borderRadius: 150,
					background: '#0d0d0f',
					boxShadow: 'inset 0 0 0 6px #2a2a2e',
					transformOrigin: '0 0',
					transform: quadToMatrix3d(SCREEN.w, SCREEN.h, body),
				}}
			/>
			<div
				style={{
					position: 'absolute',
					left: 32,
					top: 32,
					padding: '8px 14px',
					background: 'rgba(0,0,0,0.6)',
					color: '#bbb',
					font: '500 22px "Inter", sans-serif',
					letterSpacing: 1,
				}}
			>
				PLACEHOLDER · public/{kind === 'wide' ? ASSET_PATHS.wide : ASSET_PATHS.closeup}
			</div>
		</AbsoluteFill>
	);
};

export const Plate: React.FC<{
	kind: PlateKind;
	offset: number;
	assets: AssetAvailability;
	showTrackingGuide?: boolean;
}> = ({kind, offset, assets, showTrackingGuide}) => {
	const local = useCurrentFrame();
	const frame = local + offset;
	const quad = quadAt(SCREEN_TRACK[kind], local);
	const {s, fx, fy} = cameraAt(kind, frame, quad);
	const hasFootage = assets[kind];
	// Shallow DOF: the plate softens slightly as the camera closes in on the screen.
	const plateBlur = kind === 'closeup' ? interpolate(frame, [TIMING.pushFrom, TIMING.pushTo], [0, 6], clamp) : 0;

	return (
		<AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
			<AbsoluteFill style={{transformOrigin: '0 0', transform: `translate(${CX}px, ${CY}px) scale(${s}) translate(${-fx}px, ${-fy}px)`}}>
				<AbsoluteFill style={{filter: `contrast(1.06) saturate(0.9) brightness(0.94) blur(${plateBlur}px)`}}>
					{hasFootage ? (
						<OffthreadVideo
							src={staticFile(ASSET_PATHS[kind])}
							startFrom={FOOTAGE_TRIM[kind]}
							muted
							style={{width: HOOK.width, height: HOOK.height, objectFit: 'cover'}}
						/>
					) : (
						<PlaceholderPlate kind={kind} quad={quad} hasBackground={assets.background} />
					)}
				</AbsoluteFill>
				{/* Phone screen composited onto the tracked corners; it rides the same camera transform. */}
				<div
					style={{
						position: 'absolute',
						left: 0,
						top: 0,
						width: SCREEN.w,
						height: SCREEN.h,
						transformOrigin: '0 0',
						transform: quadToMatrix3d(SCREEN.w, SCREEN.h, quad),
						borderRadius: 120,
						overflow: 'hidden',
						filter: 'brightness(0.97)',
					}}
				>
					<InstagramScreen frame={frame} assets={assets} />
					{/* Faint glass sheen so the UI sits in the plate rather than on top of it. */}
					<div style={{position: 'absolute', inset: 0, background: 'linear-gradient(155deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 38%)'}} />
				</div>
				{kind === 'closeup' && assets.handForeground ? (
					<AbsoluteFill style={{filter: `contrast(1.06) saturate(0.9) brightness(0.94) blur(${plateBlur}px)`}}>
						<OffthreadVideo
							src={staticFile(ASSET_PATHS.handForeground)}
							startFrom={FOOTAGE_TRIM.closeup}
							transparent
							muted
							style={{width: HOOK.width, height: HOOK.height, objectFit: 'cover'}}
						/>
					</AbsoluteFill>
				) : null}
				{showTrackingGuide ? (
					<svg width={HOOK.width} height={HOOK.height} style={{position: 'absolute', left: 0, top: 0}}>
						<polygon points={quad.map((p) => p.join(',')).join(' ')} fill="none" stroke="#00E5FF" strokeWidth={3} />
						{quad.map((p, i) => (
							<circle key={i} cx={p[0]} cy={p[1]} r={8} fill="#00E5FF" />
						))}
					</svg>
				) : null}
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
