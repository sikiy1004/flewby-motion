import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine, DrawRect} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene03;

const BOX = {x: colX(0), y: 290, w: span(5), h: 190};
const NOTE_Y = [290, 392];
const STRUCT_Y = 548;
const RISK_Y = 690;

const T = {box: 24, hold: 72, notes: [120, 170], structure: 255, risk: 357, check: 410};

export const Scene03: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const hold = useProgress(T.hold, 18);
	const dim = interpolate(hold, [0, 1], [1, 0.4]);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={160}>
				<Heading size={64} delay={10}>
					{C.heading}
				</Heading>
			</Block>

			{/* Hypothesis — dashed, because it is not established. */}
			<Canvas>
				<DrawRect x={BOX.x} y={BOX.y} w={BOX.w} h={BOX.h} delay={T.box} duration={30} width={3} dashed />
				{NOTE_Y.map((y, i) => (
					<DrawLine key={y} x1={colX(6)} y1={y} x2={colX(6)} y2={y + 78} delay={T.notes[i]} duration={14} width={3} color={COLORS.gray} />
				))}
			</Canvas>
			<div style={{position: 'absolute', left: BOX.x + 40, top: BOX.y + 36, opacity: dim}}>
				<div style={{display: 'flex', alignItems: 'center', gap: 14}}>
					<Label delay={T.box + 8} size={15} color="#6E6E6A">
						{C.hypothesisLabel}
					</Label>
					<FadeUp delay={T.box + 14} distance={6}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 18, color: COLORS.black, border: `2px solid ${COLORS.black}`, padding: '0 10px'}}>
							{C.hypothesisTag}
						</span>
					</FadeUp>
				</div>
				<div style={{marginTop: 26}}>
					<MaskReveal delay={T.box + 16}>
						<Txt size={56} weight={800}>
							{C.hypothesis}
						</Txt>
					</MaskReveal>
				</div>
			</div>
			<div
				style={{
					position: 'absolute',
					left: BOX.x + BOX.w - 210,
					top: BOX.y + BOX.h - 32,
					width: 210,
					height: 64,
					background: COLORS.black,
					clipPath: `inset(0 ${(1 - hold) * 100}% 0 0)`,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
					gap: 14,
				}}
			>
				<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 28, color: COLORS.offWhite}}>{C.hold}</span>
				<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 13, letterSpacing: '0.16em', color: COLORS.gray}}>{C.holdLabel}</span>
			</div>

			{/* Why it stays a hypothesis. */}
			{C.notes.map((n, i) => (
				<div key={n.label} style={{position: 'absolute', left: colX(6) + 28, top: NOTE_Y[i] + 2}}>
					<Label delay={T.notes[i]} size={14} color="#6E6E6A">
						{n.label}
					</Label>
					<div style={{marginTop: 12}}>
						<MaskReveal delay={T.notes[i] + 6}>
							<Txt size={25} weight={500}>
								{n.text}
							</Txt>
						</MaskReveal>
					</div>
				</div>
			))}

			{/* Structural factors alone explain the anxiety. */}
			<Block col={0} top={STRUCT_Y}>
				<Label delay={T.structure} size={14} color="#6E6E6A">
					{C.structureLabel}
				</Label>
				<div style={{display: 'flex', alignItems: 'center', gap: 12, marginTop: 16}}>
					{C.structure.map((s, i) => {
						const p = interpolate(frame, [T.structure + 6 + i * 8, T.structure + 22 + i * 8], [0, 1], {
							extrapolateLeft: 'clamp',
							extrapolateRight: 'clamp',
							easing: EASE.out,
						});
						return (
							<div
								key={s}
								style={{
									height: 60,
									padding: '0 24px',
									display: 'flex',
									alignItems: 'center',
									background: COLORS.black,
									clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`,
								}}
							>
								<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 26, color: COLORS.offWhite, whiteSpace: 'nowrap'}}>{s}</span>
							</div>
						);
					})}
					<FadeUp delay={T.structure + 40} style={{marginLeft: 20}}>
						<Txt size={27} weight={700}>
							{`→ ${C.structureNote}`}
						</Txt>
					</FadeUp>
				</div>
			</Block>

			{/* The risk of entering with the hypothesis, and how to check it. */}
			<Block col={0} top={RISK_Y}>
				<div style={{display: 'flex', alignItems: 'center', gap: 20}}>
					<div style={{width: 8, height: 44, background: COLORS.red, transform: `scaleY(${useProgress(T.risk - 4, 12)})`}} />
					<MaskReveal delay={T.risk}>
						<Txt size={34} weight={800}>
							{C.risk}
						</Txt>
					</MaskReveal>
				</div>
				<div style={{marginTop: 14, marginLeft: 28}}>
					<FadeUp delay={T.check}>
						<Txt size={26} color="#55554F">
							{C.check}
						</Txt>
					</FadeUp>
				</div>
			</Block>
		</SceneFrame>
	);
};
