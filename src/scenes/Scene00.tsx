import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine} from '../components/AnimatedLine';
import {Counter} from '../components/Counter';
import {SceneFrame} from '../components/Grid';
import {FadeUp, Label, MaskReveal, useProgress} from '../components/Typography';
import {COPY, SCENES} from '../data/scenes';
import {COLORS, COL_W, EASE, FONTS, GRID, VIDEO, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene00;

export const Scene00: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const square = useProgress(8, 16);
	const chapters = SCENES.filter((s) => s.chapter);

	return (
		<SceneFrame meta={meta} showGrid={showGrid} bare>
			{/* Column edges draw down, then settle to a faint structure. */}
			<Canvas>
				{Array.from({length: GRID.columns + 1}).map((_, i) => {
					const x = i === GRID.columns ? colX(GRID.columns - 1) + COL_W : colX(i);
					return <DrawLine key={i} x1={x} y1={0} x2={x} y2={VIDEO.height} delay={i * 2} duration={30} color={COLORS.gray} width={1} opacity={0.12} />;
				})}
				<DrawLine x1={GRID.marginX} y1={618} x2={VIDEO.width - GRID.marginX} y2={618} delay={84} duration={34} color={COLORS.offWhite} width={2} />
			</Canvas>

			<div style={{position: 'absolute', left: colX(0), top: 176, display: 'flex', alignItems: 'center', gap: 20}}>
				<div style={{width: 18, height: 18, background: COLORS.red, transform: `scale(${square})`}} />
				<Label delay={10} color={COLORS.offWhite} size={18}>
					{C.kicker}
				</Label>
			</div>

			<div style={{position: 'absolute', left: colX(0), top: 262, width: span(9)}}>
				<MaskReveal delay={22} duration={28}>
					<div style={titleStyle}>
						{C.titleLines[0]}
						{C.titleLines[1]}
					</div>
				</MaskReveal>
				<MaskReveal delay={34} duration={28}>
					<div style={titleStyle}>{C.titleLines[2]}</div>
				</MaskReveal>
			</div>

			{/* The number arrives a beat after the title. */}
			<div style={{position: 'absolute', left: colX(9), top: 250, width: span(3)}}>
				<Counter value={C.scaleNumber} delay={58} size={330} color={COLORS.red} />
				<div style={{display: 'flex', alignItems: 'baseline', gap: 16, marginTop: 14}}>
					<FadeUp delay={74}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 36, color: COLORS.offWhite}}>{C.scaleUnit}</span>
					</FadeUp>
					<Label delay={80} color={COLORS.gray} size={16}>
						{C.scaleLabel}
					</Label>
				</div>
			</div>

			<FadeUp delay={98} style={{position: 'absolute', left: colX(0), top: 648}}>
				<span style={{fontFamily: FONTS.jp, fontWeight: 500, fontSize: 34, color: COLORS.offWhite, letterSpacing: '0.04em'}}>
					{C.subtitle}
				</span>
			</FadeUp>

			{/* Table of contents: eight chapters in a 4 × 2 grid. */}
			<AbsoluteFill>
				{chapters.map((s, i) => {
					const col = (i % 4) * 3;
					const row = Math.floor(i / 4);
					const p = interpolate(frame, [130 + i * 6, 150 + i * 6], [0, 1], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
						easing: EASE.out,
					});
					return (
						<div
							key={s.id}
							style={{
								position: 'absolute',
								left: colX(col),
								top: 738 + row * 52,
								width: span(3),
								display: 'flex',
								alignItems: 'baseline',
								gap: 16,
								opacity: p,
								transform: `translateX(${(1 - p) * -12}px)`,
							}}
						>
							<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 18, color: COLORS.red, letterSpacing: '0.04em'}}>{s.chapter}</span>
							<span style={{fontFamily: FONTS.jp, fontWeight: 500, fontSize: 21, color: COLORS.gray, whiteSpace: 'nowrap'}}>{s.title}</span>
						</div>
					);
				})}
			</AbsoluteFill>
		</SceneFrame>
	);
};

const titleStyle: React.CSSProperties = {
	fontFamily: FONTS.jp,
	fontWeight: 800,
	fontSize: 116,
	lineHeight: 1.2,
	letterSpacing: '0.01em',
	color: COLORS.offWhite,
	whiteSpace: 'nowrap',
};
