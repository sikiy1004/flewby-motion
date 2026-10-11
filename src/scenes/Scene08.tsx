import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Canvas, DrawLine, DrawPath} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY, SCENES} from '../data/scenes';
import {COLORS, EASE, FONTS, GRID, VIDEO, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene08;

const X0 = colX(0);
const X1 = colX(6) + span(1);
const BEND_X = colX(2);
const EXP_Y = 440;
const ACT_Y = 600;
const SAFETY_Y = 676;

const T = {expected: 100, actual: 112, gap: 150, safety: 205, measures: 216, end: 296};

export const Scene08: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const gap = useProgress(T.gap, 18);
	const end = useProgress(T.end, 26, EASE.inOut);
	const fadeOut = interpolate(frame, [durationInFrames - 24, durationInFrames - 1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={168}>
				<Heading size={80} delay={12}>
					{C.heading}
				</Heading>
			</Block>

			{/* Expected vs. actual: the two paths part ways. */}
			<Canvas>
				<circle cx={X0 + 8} cy={EXP_Y} r={8} fill={COLORS.black} opacity={useProgress(T.expected - 8, 10)} />
				<DrawLine x1={X0 + 8} y1={EXP_Y} x2={X1} y2={EXP_Y} delay={T.expected} duration={36} width={3} color={COLORS.gray} dashed />
				<DrawPath d={`M ${X0 + 8} ${EXP_Y} H ${BEND_X} L ${X1} ${ACT_Y}`} delay={T.actual} duration={40} width={4} />
				<g opacity={gap}>
					<line x1={X1 + 36} y1={EXP_Y} x2={X1 + 36} y2={EXP_Y + (ACT_Y - EXP_Y) * gap} stroke={COLORS.red} strokeWidth={4} />
					<line x1={X1 + 26} y1={EXP_Y} x2={X1 + 46} y2={EXP_Y} stroke={COLORS.red} strokeWidth={4} />
					<line x1={X1 + 26} y1={ACT_Y} x2={X1 + 46} y2={ACT_Y} stroke={COLORS.red} strokeWidth={4} opacity={gap > 0.95 ? 1 : 0} />
				</g>
				{/* The safeguard line, laid beneath the divergence. */}
				<DrawLine x1={X0} y1={SAFETY_Y} x2={X1 + 46} y2={SAFETY_Y} delay={T.safety} duration={34} width={6} color={COLORS.red} />
			</Canvas>

			<div style={{position: 'absolute', left: X1 - 220, top: EXP_Y - 54, width: 220, textAlign: 'right'}}>
				<FadeUp delay={T.expected + 24}>
					<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 28, color: '#6E6E6A'}}>{C.expected}</span>
					<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 13, letterSpacing: '0.16em', color: '#6E6E6A', marginLeft: 12}}>{C.expectedEn}</span>
				</FadeUp>
			</div>
			<div style={{position: 'absolute', left: X1 - 300, top: ACT_Y + 14, width: 300, textAlign: 'right'}}>
				<FadeUp delay={T.actual + 30}>
					<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 28, color: COLORS.black}}>{C.actual}</span>
					<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 13, letterSpacing: '0.16em', color: COLORS.black, marginLeft: 12}}>{C.actualEn}</span>
				</FadeUp>
			</div>
			<div style={{position: 'absolute', left: X1 + 64, top: (EXP_Y + ACT_Y) / 2 - 10}}>
				<Label delay={T.gap + 6} size={18} color={COLORS.red}>
					{C.gap}
				</Label>
			</div>

			{/* Countermeasures (to be transcribed from the memo). */}
			<Block col={8} top={EXP_Y - 40}>
				<Label delay={T.measures} size={15} color={COLORS.red}>
					{C.measuresLabel}
				</Label>
				<div style={{marginTop: 26, display: 'flex', flexDirection: 'column', gap: 22}}>
					{C.measures.map((m, i) => (
						<FadeUp key={i} delay={T.measures + 10 + i * 10}>
							<div style={{display: 'flex', alignItems: 'baseline', gap: 22}}>
								<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 22}}>{String(i + 1).padStart(2, '0')}</span>
								<Txt size={30}>{m}</Txt>
							</div>
						</FadeUp>
					))}
				</div>
			</Block>

			{/* Closing panel. */}
			<AbsoluteFill style={{background: COLORS.black, clipPath: `inset(0 ${(1 - end) * 100}% 0 0)`}}>
				<AbsoluteFill style={{opacity: fadeOut}}>
					<div style={{position: 'absolute', left: GRID.marginX, top: 236, display: 'flex', alignItems: 'center', gap: 18}}>
						<div style={{width: 18, height: 18, background: COLORS.red}} />
						<Label delay={T.end + 20} size={18} color={COLORS.offWhite}>
							{C.endKicker}
						</Label>
					</div>
					<div style={{position: 'absolute', left: GRID.marginX, top: 300}}>
						<MaskReveal delay={T.end + 26} duration={28}>
							<div style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 96, color: COLORS.offWhite, letterSpacing: '0.01em', whiteSpace: 'nowrap'}}>
								{C.endTitle}
							</div>
						</MaskReveal>
					</div>
					<Canvas>
						<DrawLine x1={GRID.marginX} y1={470} x2={VIDEO.width - GRID.marginX} y2={470} delay={T.end + 40} duration={34} color={COLORS.offWhite} width={2} />
					</Canvas>
					{SCENES.filter((s) => s.chapter).map((s, i) => (
						<div key={s.id} style={{position: 'absolute', left: colX((i % 4) * 3), top: 520 + Math.floor(i / 4) * 56, display: 'flex', alignItems: 'baseline', gap: 16}}>
							<FadeUp delay={T.end + 52 + i * 5} distance={8}>
								<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 18, color: COLORS.red, marginRight: 16}}>{s.chapter}</span>
								<span style={{fontFamily: FONTS.jp, fontWeight: 500, fontSize: 22, color: COLORS.gray, whiteSpace: 'nowrap'}}>{s.title}</span>
							</FadeUp>
						</div>
					))}
				</AbsoluteFill>
			</AbsoluteFill>
		</SceneFrame>
	);
};
