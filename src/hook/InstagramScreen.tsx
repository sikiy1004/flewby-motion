import React from 'react';
import {Easing, Img, interpolate, staticFile} from 'remotion';
import {ASSET_PATHS, COPY, TIMING, type AssetAvailability} from './config';

// Screen is laid out in iPhone points (390×844) and rendered at 3× so text stays sharp
// while the camera pushes in on the composited screen.
export const SCREEN = {w: 1170, h: 2532} as const;
const u = (pt: number) => pt * 3;

const IG = {
	bg: '#000000',
	fg: '#F5F5F5',
	sub: '#A8A8A8',
	field: '#262626',
	rule: '#262626',
	blue: '#0095F6',
	font: '-apple-system, "Inter", "Noto Sans JP", sans-serif',
} as const;

const ease = Easing.bezier(0.25, 0.1, 0.25, 1);
const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** Layout of the sponsored post's media, in screen px. The tap lands at its center. */
const RESULTS_TOP = u(102);
const MEDIA = {x: 0, y: u(292), w: SCREEN.w, h: u(390 * 1.25)} as const;
export const TAP_POINT = {x: MEDIA.x + MEDIA.w * 0.52, y: MEDIA.y + MEDIA.h * 0.55};

/** The main ad sits full-width (9:16) inside the 9:19.5 screen, vertically centered. */
export const VIEWER_VIDEO = {
	x: 0,
	y: (SCREEN.h - (SCREEN.w * 16) / 9) / 2,
	w: SCREEN.w,
	h: (SCREEN.w * 16) / 9,
} as const;

const Placeholder: React.FC<{label: string; path: string; style?: React.CSSProperties}> = ({
	label,
	path,
	style,
}) => (
	<div
		style={{
			position: 'absolute',
			inset: 0,
			background: 'repeating-linear-gradient(135deg, #1d1d1d 0 24px, #232323 24px 48px)',
			display: 'flex',
			flexDirection: 'column',
			alignItems: 'center',
			justifyContent: 'center',
			gap: u(6),
			color: '#8a8a8a',
			fontFamily: IG.font,
			textAlign: 'center',
			...style,
		}}
	>
		<div style={{fontSize: u(15), fontWeight: 700, letterSpacing: u(1)}}>{label}</div>
		<div style={{fontSize: u(11)}}>public/{path}</div>
	</div>
);

const Avatar: React.FC<{size: number; assets: AssetAvailability; ring?: boolean}> = ({size, assets, ring}) => (
	<div
		style={{
			width: size,
			height: size,
			borderRadius: '50%',
			padding: ring ? u(2) : 0,
			background: ring ? 'linear-gradient(45deg, #FEDA75, #FA7E1E, #D62976, #962FBF)' : 'transparent',
			flexShrink: 0,
		}}
	>
		<div
			style={{
				width: '100%',
				height: '100%',
				borderRadius: '50%',
				background: '#F2F0EA',
				border: ring ? `${u(2)}px solid ${IG.bg}` : 'none',
				boxSizing: 'border-box',
				overflow: 'hidden',
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'center',
			}}
		>
			{assets.logo ? (
				<Img src={staticFile(ASSET_PATHS.logo)} style={{width: '78%', height: '78%', objectFit: 'contain'}} />
			) : (
				<span style={{fontFamily: IG.font, fontSize: size * 0.22, color: '#555', fontWeight: 700}}>LOGO</span>
			)}
		</div>
	</div>
);

const StatusBar: React.FC = () => (
	<div
		style={{
			height: u(54),
			display: 'flex',
			alignItems: 'center',
			justifyContent: 'space-between',
			padding: `${u(6)}px ${u(32)}px 0`,
			color: IG.fg,
			fontFamily: IG.font,
			fontSize: u(16),
			fontWeight: 600,
		}}
	>
		<span>{COPY.statusTime}</span>
		<svg width={u(68)} height={u(13)} viewBox="0 0 68 13">
			{[0, 1, 2, 3].map((i) => (
				<rect key={i} x={i * 5} y={9 - i * 3} width={3.2} height={3 + i * 3} rx={0.8} fill={IG.fg} />
			))}
			<path d="M30 4.5a9 9 0 0 1 12 0M32.4 7.2a5.4 5.4 0 0 1 7.2 0" stroke={IG.fg} strokeWidth={1.6} fill="none" strokeLinecap="round" />
			<circle cx={36} cy={10.2} r={1.4} fill={IG.fg} />
			<rect x={44} y={1} width={21} height={11} rx={3} stroke={IG.sub} strokeWidth={1} fill="none" />
			<rect x={46} y={3} width={13} height={7} rx={1.5} fill={IG.fg} />
			<rect x={66} y={4.5} width={1.5} height={4} rx={0.7} fill={IG.sub} />
		</svg>
	</div>
);

const SearchField: React.FC<{frame: number}> = ({frame}) => {
	const chars = Array.from(COPY.query);
	const shown = Math.round(interpolate(frame, [TIMING.typeFrom, TIMING.typeTo], [0, chars.length], clamp));
	const typing = frame < TIMING.resultsIn;
	const caretOn = typing && Math.floor(frame / 8) % 2 === 0;
	return (
		<div style={{display: 'flex', alignItems: 'center', gap: u(12), padding: `${u(4)}px ${u(16)}px ${u(8)}px`}}>
			<svg width={u(24)} height={u(24)} viewBox="0 0 24 24">
				<path d="M15 4l-8 8 8 8" stroke={IG.fg} strokeWidth={2.2} fill="none" strokeLinecap="round" strokeLinejoin="round" />
			</svg>
			<div
				style={{
					flex: 1,
					height: u(36),
					borderRadius: u(10),
					background: IG.field,
					display: 'flex',
					alignItems: 'center',
					gap: u(8),
					padding: `0 ${u(12)}px`,
					fontFamily: IG.font,
					fontSize: u(16),
					color: IG.fg,
				}}
			>
				<svg width={u(16)} height={u(16)} viewBox="0 0 16 16">
					<circle cx={7} cy={7} r={5.2} stroke={IG.sub} strokeWidth={1.6} fill="none" />
					<path d="M11 11l3.5 3.5" stroke={IG.sub} strokeWidth={1.6} strokeLinecap="round" />
				</svg>
				<span style={{whiteSpace: 'pre'}}>{chars.slice(0, shown).join('')}</span>
				<span style={{width: u(2), height: u(20), background: IG.blue, marginLeft: -u(6), opacity: caretOn ? 1 : 0}} />
			</div>
		</div>
	);
};

const Tabs: React.FC = () => {
	const tabs = ['上位検索結果', 'アカウント', '音声', 'タグ', 'スポット'];
	return (
		<div style={{display: 'flex', borderBottom: `1px solid ${IG.rule}`, fontFamily: IG.font, fontSize: u(14)}}>
			{tabs.map((t, i) => (
				<div
					key={t}
					style={{
						padding: `${u(11)}px ${u(14)}px`,
						color: i === 0 ? IG.fg : IG.sub,
						fontWeight: i === 0 ? 600 : 500,
						borderBottom: i === 0 ? `${u(1)}px solid ${IG.fg}` : 'none',
						whiteSpace: 'nowrap',
					}}
				>
					{t}
				</div>
			))}
		</div>
	);
};

const NameBlock: React.FC<{sub: string}> = ({sub}) => (
	<div style={{fontFamily: IG.font, lineHeight: 1.25, minWidth: 0}}>
		<div style={{color: IG.fg, fontSize: u(14), fontWeight: 600}}>{COPY.handle ?? COPY.storeName}</div>
		<div style={{color: IG.sub, fontSize: u(13)}}>{sub}</div>
	</div>
);

const Icon: React.FC<{d: string}> = ({d}) => (
	<svg width={u(24)} height={u(24)} viewBox="0 0 24 24">
		<path d={d} stroke={IG.fg} strokeWidth={1.8} fill="none" strokeLinejoin="round" strokeLinecap="round" />
	</svg>
);

const StoreMedia: React.FC<{assets: AssetAvailability}> = ({assets}) =>
	assets.storePhoto ? (
		<Img src={staticFile(ASSET_PATHS.storePhoto)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
	) : (
		<Placeholder label="STORE PHOTO" path={ASSET_PATHS.storePhoto} />
	);

const Results: React.FC<{frame: number; assets: AssetAvailability}> = ({frame, assets}) => {
	const t = interpolate(frame, [TIMING.resultsIn, TIMING.resultsIn + 8], [0, 1], {...clamp, easing: ease});
	const press = interpolate(frame, [TIMING.tap - 2, TIMING.tap, TIMING.tapRelease, TIMING.tapRelease + 4], [0, 1, 1, 0], clamp);
	const ripple = interpolate(frame, [TIMING.tap, TIMING.tap + 12], [0, 1], {...clamp, easing: Easing.out(Easing.quad)});
	return (
		<div style={{position: 'absolute', left: 0, right: 0, top: RESULTS_TOP, bottom: 0, opacity: t, transform: `translateY(${(1 - t) * u(10)}px)`}}>
			<Tabs />
			{/* Account result */}
			<div style={{display: 'flex', alignItems: 'center', gap: u(12), padding: `${u(10)}px ${u(16)}px`}}>
				<Avatar size={u(44)} assets={assets} ring />
				<NameBlock sub={COPY.handle ? COPY.storeName : COPY.category} />
			</div>
			{/* Sponsored post */}
			<div style={{position: 'absolute', left: 0, right: 0, top: MEDIA.y - u(54) - RESULTS_TOP}}>
				<div style={{display: 'flex', alignItems: 'center', gap: u(10), height: u(54), padding: `0 ${u(14)}px`}}>
					<Avatar size={u(32)} assets={assets} />
					<NameBlock sub={COPY.sponsored} />
					<div style={{flex: 1}} />
					<span style={{color: IG.fg, fontSize: u(18), fontFamily: IG.font, letterSpacing: u(1)}}>···</span>
				</div>
				<div style={{position: 'relative', width: MEDIA.w, height: MEDIA.h, overflow: 'hidden', background: '#111'}}>
					<StoreMedia assets={assets} />
					<div style={{position: 'absolute', inset: 0, background: `rgba(0,0,0,${press * 0.18})`}} />
					<div
						style={{
							position: 'absolute',
							left: TAP_POINT.x - MEDIA.x,
							top: TAP_POINT.y - MEDIA.y,
							width: u(120),
							height: u(120),
							marginLeft: -u(60),
							marginTop: -u(60),
							borderRadius: '50%',
							background: 'rgba(255,255,255,0.35)',
							transform: `scale(${ripple})`,
							opacity: ripple > 0 ? (1 - ripple) * 0.6 : 0,
						}}
					/>
				</div>
				<div
					style={{
						display: 'flex',
						justifyContent: 'space-between',
						alignItems: 'center',
						height: u(44),
						padding: `0 ${u(14)}px`,
						borderBottom: `1px solid ${IG.rule}`,
						fontFamily: IG.font,
						fontSize: u(14),
						fontWeight: 600,
						color: IG.fg,
					}}
				>
					<span>{COPY.cta}</span>
					<svg width={u(16)} height={u(16)} viewBox="0 0 16 16">
						<path d="M6 3l5 5-5 5" stroke={IG.fg} strokeWidth={1.8} fill="none" strokeLinecap="round" />
					</svg>
				</div>
				<div style={{display: 'flex', gap: u(16), padding: `${u(10)}px ${u(14)}px`}}>
					<Icon d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z" />
					<Icon d="M20 12a8 8 0 1 1-3.2-6.4A8 8 0 0 1 20 12zM20 12l1 7-5-2.5" />
					<Icon d="M21 4L10 14M21 4l-7 17-4-7-7-4z" />
				</div>
			</div>
		</div>
	);
};

const Viewer: React.FC<{frame: number; assets: AssetAvailability}> = ({frame, assets}) => {
	const t = interpolate(frame, [TIMING.viewerOpen, TIMING.viewerOpened], [0, 1], {
		...clamp,
		easing: Easing.bezier(0.2, 0, 0, 1),
	});
	if (t <= 0) return null;
	const from = {x: MEDIA.x, y: MEDIA.y, w: MEDIA.w, h: MEDIA.h};
	const to = VIEWER_VIDEO;
	const r = {
		x: from.x + (to.x - from.x) * t,
		y: from.y + (to.y - from.y) * t,
		w: from.w + (to.w - from.w) * t,
		h: from.h + (to.h - from.h) * t,
	};
	const chrome = interpolate(frame, [TIMING.viewerOpened - 4, TIMING.viewerOpened + 4], [0, 1], clamp);
	return (
		<div style={{position: 'absolute', inset: 0, background: `rgba(0,0,0,${t})`}}>
			<div style={{position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, overflow: 'hidden'}}>
				{/* Crossfade the tapped store photo into the main ad's first frame as the player opens. */}
				<div style={{position: 'absolute', inset: 0, opacity: 1 - t}}>
					<StoreMedia assets={assets} />
				</div>
				<div style={{position: 'absolute', inset: 0, opacity: t}}>
					{assets.mainAdFirstFrame ? (
						<Img src={staticFile(ASSET_PATHS.mainAdFirstFrame)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
					) : (
						<Placeholder label="MAIN AD · FRAME 1" path={ASSET_PATHS.mainAdFirstFrame} />
					)}
				</div>
			</div>
			{/* Player chrome: paused at 0:00, about to play. */}
			<div style={{position: 'absolute', inset: 0, opacity: chrome, fontFamily: IG.font, color: IG.fg}}>
				<div style={{position: 'absolute', left: u(16), right: u(16), top: u(58), height: u(2), background: 'rgba(255,255,255,0.35)'}} />
				<div style={{position: 'absolute', left: u(16), bottom: u(64), display: 'flex', alignItems: 'center', gap: u(10)}}>
					<Avatar size={u(32)} assets={assets} />
					<NameBlock sub={COPY.sponsored} />
				</div>
				<div
					style={{
						position: 'absolute',
						left: u(16),
						right: u(16),
						bottom: u(16),
						height: u(36),
						borderRadius: u(8),
						background: 'rgba(255,255,255,0.16)',
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
						fontSize: u(14),
						fontWeight: 600,
					}}
				>
					{COPY.cta}
				</div>
			</div>
		</div>
	);
};

/** The phone screen at a given global frame. Rendered flat at SCREEN size; Plate warps it. */
export const InstagramScreen: React.FC<{frame: number; assets: AssetAvailability}> = ({frame, assets}) => (
	<div style={{position: 'relative', width: SCREEN.w, height: SCREEN.h, background: IG.bg, overflow: 'hidden'}}>
		<StatusBar />
		<SearchField frame={frame} />
		<Results frame={frame} assets={assets} />
		<Viewer frame={frame} assets={assets} />
	</div>
);
