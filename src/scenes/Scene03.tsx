import React from 'react';
import {interpolate} from 'remotion';
import {Canvas, DrawLine, DrawRect} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene03;

const BOX = {x: colX(0), y: 372, w: span(5), h: 268};
const INTERVIEW = {x: colX(8), y: BOX.y, w: span(4), h: BOX.h};
const MID_Y = BOX.y + BOX.h / 2;
const BARRIER_X = colX(6) + 60;

const T = {interview: 70, box: 140, hold: 250, arrow: 312, barrier: 340, barrierText: 352};

export const Scene03: React.FC<SceneProps> = ({meta, showGrid}) => {
	const interview = useProgress(T.interview, 26);
	const hold = useProgress(T.hold, 18);
	const dim = interpolate(hold, [0, 1], [1, 0.4]);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={168}>
				<Heading size={72} delay={12}>
					{C.heading}
				</Heading>
			</Block>

			<Canvas>
				<DrawRect x={BOX.x} y={BOX.y} w={BOX.w} h={BOX.h} delay={T.box} duration={36} width={3} dashed />
				{/* The hypothesis heads toward the interview and is stopped at the barrier. */}
				<DrawLine x1={BOX.x + BOX.w + 24} y1={MID_Y} x2={BARRIER_X - 28} y2={MID_Y} delay={T.arrow} duration={22} width={3} color={COLORS.gray} />
				<DrawLine x1={BARRIER_X} y1={BOX.y - 20} x2={BARRIER_X} y2={BOX.y + BOX.h + 20} delay={T.barrier} duration={20} width={6} color={COLORS.red} />
			</Canvas>

			{/* Hypothesis (dashed = not established). */}
			<div style={{position: 'absolute', left: BOX.x + 44, top: BOX.y + 44, opacity: dim}}>
				<div style={{display: 'flex', alignItems: 'center', gap: 16}}>
					<Label delay={T.box + 10} size={16} color="#6E6E6A">
						{C.hypothesisLabel}
					</Label>
					<FadeUp delay={T.box + 16} distance={6}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 20, color: COLORS.black, border: `2px solid ${COLORS.black}`, padding: '0 10px'}}>
							{C.hypothesisTag}
						</span>
					</FadeUp>
				</div>
				<div style={{marginTop: 46}}>
					<MaskReveal delay={T.box + 18}>
						<Txt size={60} weight={800}>
							{C.hypothesis}
						</Txt>
					</MaskReveal>
				</div>
			</div>

			{/* ON HOLD tag pinned to the box corner. */}
			<div
				style={{
					position: 'absolute',
					left: BOX.x + BOX.w - 220,
					top: BOX.y + BOX.h - 34,
					width: 220,
					height: 68,
					background: COLORS.black,
					clipPath: `inset(0 ${(1 - hold) * 100}% 0 0)`,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
					gap: 16,
				}}
			>
				<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 30, color: COLORS.offWhite}}>{C.hold}</span>
				<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 14, letterSpacing: '0.16em', color: COLORS.gray}}>{C.holdLabel}</span>
			</div>

			{/* The interview itself. */}
			<div
				style={{
					position: 'absolute',
					left: INTERVIEW.x,
					top: INTERVIEW.y,
					width: INTERVIEW.w,
					height: INTERVIEW.h,
					background: COLORS.black,
					clipPath: `inset(0 0 0 ${(1 - interview) * 100}%)`,
				}}
			>
				<div style={{position: 'absolute', left: 44, top: 44}}>
					<Label delay={T.interview + 12} size={16} color={COLORS.gray}>
						{C.interviewLabel}
					</Label>
				</div>
				<div style={{position: 'absolute', left: 44, top: 108}}>
					<MaskReveal delay={T.interview + 16}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 60, color: COLORS.offWhite}}>{C.interview}</span>
					</MaskReveal>
				</div>
			</div>

			<div style={{position: 'absolute', left: BARRIER_X - 3, top: BOX.y + BOX.h + 56, display: 'flex', alignItems: 'center', gap: 18}}>
				<MaskReveal delay={T.barrierText}>
					<Txt size={40} weight={800}>
						{C.barrier}
					</Txt>
				</MaskReveal>
			</div>
		</SceneFrame>
	);
};
