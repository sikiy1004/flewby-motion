import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine} from '../components/AnimatedLine';
import {Counter} from '../components/Counter';
import {SceneFrame} from '../components/Grid';
import {FadeUp, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY, DOC_DATE} from '../data/scenes';
import {COLORS, COL_W, EASE, FONTS, GRID, VIDEO, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene00;

// Premises appear with the narration (frames).
const PREMISE_AT = [50, 90, 140, 215];

export const Scene00: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const square = useProgress(8, 16);

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
					<div style={titleStyle}>{C.titleLines[0]}</div>
				</MaskReveal>
				<MaskReveal delay={34} duration={28}>
					<div style={titleStyle}>{C.titleLines[1]}</div>
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

			{/* The memo's premise line, set as a four-column register. */}
			<AbsoluteFill>
				{C.premises.map((p, i) => {
					const t = interpolate(frame, [PREMISE_AT[i], PREMISE_AT[i] + 20], [0, 1], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
						easing: EASE.out,
					});
					const last = i === C.premises.length - 1;
					return (
						<div
							key={p.label}
							style={{
								position: 'absolute',
								left: colX(i * 3),
								top: 652,
								width: span(3),
								opacity: t,
								transform: `translateY(${(1 - t) * 12}px)`,
							}}
						>
							<div style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 14, letterSpacing: '0.18em', color: last ? COLORS.red : COLORS.gray}}>
								{String(i + 1).padStart(2, '0')} — {p.label}
							</div>
							<div style={{marginTop: 14}}>
								<Txt size={26} weight={last ? 700 : 500} color={COLORS.offWhite} width={span(3) - 24} lineHeight={1.55}>
									{p.text}
								</Txt>
							</div>
						</div>
					);
				})}
			</AbsoluteFill>

			<div style={{position: 'absolute', right: GRID.marginX, top: 176, opacity: square}}>
				<span style={{fontFamily: FONTS.en, fontWeight: 500, fontSize: 16, letterSpacing: '0.08em', color: COLORS.gray}}>{DOC_DATE}</span>
			</div>
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
