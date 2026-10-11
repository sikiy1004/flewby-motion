import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine, DrawPath, DrawRect} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene04;

const PANEL_TOP = 330;
const ICON_Y = 520;
const STEP = 96;
const STEPS_X0 = colX(5);
const STEP_GAP = (span(7) - STEP * 4) / 3;
const ARROW_Y = ICON_Y;
const PHRASE_Y = 690;

const T = {person: 50, strike: 140, arrow: 200, process: 214, from: 287, fromStrike: 318, to: 350, focus: 476};

export const Scene04: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const person = useProgress(T.person, 20);
	const personDim = interpolate(useProgress(T.strike, 20), [0, 1], [1, 0.35]);
	const personCx = colX(0) + span(4) / 2;

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={168}>
				<Heading size={72} delay={12}>
					{C.heading}
				</Heading>
			</Block>

			{/* Left: person as subject. */}
			<Block col={0} top={PANEL_TOP}>
				<Label delay={T.person} size={15} color="#6E6E6A">
					{C.person.label}
				</Label>
				<div style={{marginTop: 14, opacity: personDim}}>
					<MaskReveal delay={T.person + 6}>
						<Txt size={36} weight={700}>
							{C.person.jp}
						</Txt>
					</MaskReveal>
				</div>
			</Block>

			{/* Right: process as subject. */}
			<Block col={5} top={PANEL_TOP}>
				<Label delay={T.process} size={15} color="#6E6E6A">
					{C.process.label}
				</Label>
				<div style={{marginTop: 14}}>
					<MaskReveal delay={T.process + 6}>
						<Txt size={36} weight={700}>
							{C.process.jp}
						</Txt>
					</MaskReveal>
				</div>
			</Block>

			<Canvas>
				{/* Person glyph. */}
				<g opacity={person * personDim} transform={`translate(${personCx} ${ICON_Y})`}>
					<circle cx={0} cy={-34} r={30} fill="none" stroke={COLORS.black} strokeWidth={3} />
					<path d="M -56 70 V 40 Q -56 10 -26 10 H 26 Q 56 10 56 40 V 70" fill="none" stroke={COLORS.black} strokeWidth={3} />
				</g>
				<DrawLine x1={personCx - 110} y1={ICON_Y + 90} x2={personCx + 110} y2={ICON_Y - 90} delay={T.strike} duration={16} width={5} color={COLORS.red} />

				{/* Arrow: person → process. */}
				<DrawLine x1={colX(4) - 4} y1={ARROW_Y} x2={colX(5) - 28} y2={ARROW_Y} delay={T.arrow} duration={18} width={3} />
				<DrawPath d={`M ${colX(5) - 44} ${ARROW_Y - 14} L ${colX(5) - 28} ${ARROW_Y} L ${colX(5) - 44} ${ARROW_Y + 14}`} delay={T.arrow + 14} duration={8} width={3} />

				{/* Process: four steps joined in sequence. */}
				{C.process.steps.map((_, i) => {
					const x = STEPS_X0 + i * (STEP + STEP_GAP);
					return (
						<React.Fragment key={i}>
							<DrawRect x={x} y={ICON_Y - STEP / 2} w={STEP} h={STEP} delay={T.process + 10 + i * 12} duration={18} width={3} />
							{i < 3 ? (
								<DrawLine x1={x + STEP} y1={ICON_Y} x2={x + STEP + STEP_GAP} y2={ICON_Y} delay={T.process + 22 + i * 12} duration={14} width={3} />
							) : null}
						</React.Fragment>
					);
				})}
			</Canvas>
			{C.process.steps.map((n, i) => {
				const x = STEPS_X0 + i * (STEP + STEP_GAP);
				const p = interpolate(frame, [T.process + 20 + i * 12, T.process + 36 + i * 12], [0, 1], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
					easing: EASE.out,
				});
				return (
					<div
						key={n}
						style={{
							position: 'absolute',
							left: x,
							top: ICON_Y - STEP / 2,
							width: STEP,
							height: STEP,
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							fontFamily: FONTS.en,
							fontWeight: 800,
							fontSize: 28,
							color: COLORS.black,
							opacity: p,
						}}
					>
						{n}
					</div>
				);
			})}

			{/* Phrase contrast. */}
			<Block col={0} top={PHRASE_Y}>
				<div style={{position: 'relative', opacity: interpolate(useProgress(T.fromStrike, 16), [0, 1], [1, 0.45])}}>
					<FadeUp delay={T.from}>
						<Txt size={48} weight={700}>
							{C.phraseFrom}
						</Txt>
					</FadeUp>
					<div
						style={{
							position: 'absolute',
							left: 0,
							top: 38,
							height: 4,
							width: 200 * useProgress(T.fromStrike, 14, EASE.line),
							background: COLORS.red,
						}}
					/>
				</div>
			</Block>
			<Canvas>
				<DrawLine x1={colX(2) + 8} y1={PHRASE_Y + 38} x2={colX(3) - 40} y2={PHRASE_Y + 38} delay={T.to - 12} duration={14} width={3} />
				<DrawPath
					d={`M ${colX(3) - 56} ${PHRASE_Y + 24} L ${colX(3) - 40} ${PHRASE_Y + 38} L ${colX(3) - 56} ${PHRASE_Y + 52}`}
					delay={T.to}
					duration={8}
					width={3}
				/>
			</Canvas>
			<Block col={3} top={PHRASE_Y}>
				<MaskReveal delay={T.to}>
					<Txt size={48} weight={800}>
						{C.phraseTo}
					</Txt>
				</MaskReveal>
			</Block>
			<Block col={3} top={PHRASE_Y + 92}>
				<FadeUp delay={T.focus}>
					<Txt size={30} color="#55554F">
						{C.focus}
					</Txt>
				</FadeUp>
			</Block>
		</SceneFrame>
	);
};
