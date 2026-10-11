import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {DOC_TITLE, TOTAL_CHAPTERS, type SceneMeta} from '../data/scenes';
import {COL_W, EASE, FONTS, GRID, VIDEO, colX, toneColors, type Tone} from '../theme';

/** Column guides. Off by default; toggle `showGrid` in the composition props to inspect alignment. */
export const GridGuides: React.FC<{tone: Tone}> = ({tone}) => (
	<AbsoluteFill style={{pointerEvents: 'none'}}>
		{Array.from({length: GRID.columns}).map((_, i) => (
			<div
				key={i}
				style={{
					position: 'absolute',
					left: colX(i),
					top: 0,
					width: COL_W,
					height: VIDEO.height,
					background: tone === 'light' ? 'rgba(230,57,53,0.06)' : 'rgba(230,57,53,0.12)',
				}}
			/>
		))}
	</AbsoluteFill>
);

type FrameProps = {
	meta: SceneMeta;
	children: React.ReactNode;
	showGrid?: boolean;
	/** Hide the running header (e.g. on the opening title). */
	bare?: boolean;
};

/** Common page: background, running header with chapter index, and the content area. */
export const SceneFrame: React.FC<FrameProps> = ({meta, children, showGrid = false, bare = false}) => {
	const frame = useCurrentFrame();
	const c = toneColors(meta.tone);
	const rule = interpolate(frame, [4, 34], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.line});
	const head = interpolate(frame, [10, 30], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.out});

	return (
		<AbsoluteFill style={{background: c.bg}}>
			{showGrid ? <GridGuides tone={meta.tone} /> : null}
			{bare ? null : (
				<>
					<div
						style={{
							position: 'absolute',
							left: GRID.marginX,
							top: GRID.headerY,
							display: 'flex',
							alignItems: 'baseline',
							gap: 20,
							opacity: head,
							transform: `translateY(${(1 - head) * 8}px)`,
						}}
					>
						<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 22, color: c.fg, letterSpacing: '0.04em'}}>
							{meta.chapter}
						</span>
						<span style={{fontFamily: FONTS.en, fontWeight: 500, fontSize: 16, color: c.sub, letterSpacing: '0.08em'}}>
							/ {TOTAL_CHAPTERS}
						</span>
						<span
							style={{
								fontFamily: FONTS.en,
								fontWeight: 700,
								fontSize: 16,
								color: c.fg,
								letterSpacing: '0.18em',
								marginLeft: 28,
							}}
						>
							{meta.label}
						</span>
					</div>
					<div
						style={{
							position: 'absolute',
							right: GRID.marginX,
							top: GRID.headerY,
							fontFamily: FONTS.jp,
							fontWeight: 500,
							fontSize: 16,
							color: c.sub,
							letterSpacing: '0.08em',
							opacity: head,
						}}
					>
						{DOC_TITLE}
					</div>
					<div
						style={{
							position: 'absolute',
							left: GRID.marginX,
							top: GRID.headerRuleY,
							width: (VIDEO.width - GRID.marginX * 2) * rule,
							height: 2,
							background: c.fg,
						}}
					/>
				</>
			)}
			{children}
		</AbsoluteFill>
	);
};

/** Absolutely positioned block snapped to grid columns. */
export const Block: React.FC<{
	col: number;
	top: number;
	width?: number;
	children: React.ReactNode;
	style?: React.CSSProperties;
}> = ({col, top, width, children, style}) => (
	<div style={{position: 'absolute', left: colX(col), top, width, ...style}}>{children}</div>
);
