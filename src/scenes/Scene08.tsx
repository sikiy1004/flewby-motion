import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {Canvas, DrawLine, DrawPath, DrawRect} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY, SCENES} from '../data/scenes';
import {COLORS, EASE, FONTS, GRID, VIDEO, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene08;

const BOX_Y = 330;
const BOX_H = 156;
const MID = BOX_Y + BOX_H / 2;
const B1 = {x: colX(0), w: span(4)};
const B2 = {x: colX(5), w: span(2)};
const B3 = {x: colX(8), w: span(4)};
const SAFETY_Y = 600;

const T = {result: 84, anxiety: 198, shift: 226, safeguard: 330, end: 390};

const Arrow: React.FC<{x1: number; x2: number; y: number; delay: number; color?: string}> = ({x1, x2, y, delay, color = COLORS.black}) => (
	<>
		<DrawLine x1={x1} y1={y} x2={x2} y2={y} delay={delay} duration={16} width={3} color={color} />
		<DrawPath d={`M ${x2 - 14} ${y - 12} L ${x2} ${y} L ${x2 - 14} ${y + 12}`} delay={delay + 14} duration={6} width={3} color={color} />
	</>
);

export const Scene08: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();
	const anxiety = useProgress(T.anxiety, 22);
	const end = useProgress(T.end, 26, EASE.inOut);
	const fadeOut = interpolate(frame, [durationInFrames - 24, durationInFrames - 1], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={160}>
				<Heading size={80} delay={10}>
					{C.heading}
				</Heading>
			</Block>

			<Canvas>
				<DrawRect x={B1.x} y={BOX_Y} w={B1.w} h={BOX_H} delay={T.result - 8} duration={28} width={3} />
				<Arrow x1={B1.x + B1.w + 16} x2={B2.x - 16} y={MID} delay={T.anxiety - 18} />
				<Arrow x1={B2.x + B2.w + 16} x2={B3.x - 16} y={MID} delay={T.shift} color={COLORS.red} />
				<DrawRect x={B3.x} y={BOX_Y} w={B3.w} h={BOX_H} delay={T.shift + 10} duration={28} width={3} dashed />
				{/* The safeguard line. */}
				<DrawLine x1={GRID.marginX} y1={SAFETY_Y} x2={VIDEO.width - GRID.marginX} y2={SAFETY_Y} delay={T.safeguard} duration={34} width={6} color={COLORS.red} />
			</Canvas>

			{/* 1 — the hearing result. */}
			<div style={{position: 'absolute', left: B1.x + 32, top: BOX_Y + 28}}>
				<Label delay={T.result} size={13} color="#6E6E6A">
					{C.resultLabel}
				</Label>
				<div style={{marginTop: 14}}>
					<FadeUp delay={T.result + 6} distance={8}>
						<Txt size={22} color="#55554F">
							{C.resultCaption}
						</Txt>
					</FadeUp>
				</div>
				<MaskReveal delay={T.result + 12}>
					<Txt size={36} weight={800}>
						{C.result}
					</Txt>
				</MaskReveal>
			</div>

			{/* 2 — the CEO's anxiety. */}
			<div
				style={{
					position: 'absolute',
					left: B2.x,
					top: BOX_Y,
					width: B2.w,
					height: BOX_H,
					background: COLORS.black,
					clipPath: `inset(0 ${(1 - anxiety) * 100}% 0 0)`,
					display: 'flex',
					flexDirection: 'column',
					justifyContent: 'center',
					paddingLeft: 28,
					boxSizing: 'border-box',
				}}
			>
				<Label delay={T.anxiety + 8} size={12} color={COLORS.gray}>
					{C.anxietyLabel}
				</Label>
				<div style={{marginTop: 12}}>
					<Txt size={34} weight={800} color={COLORS.offWhite}>
						{C.anxiety}
					</Txt>
				</div>
			</div>

			{/* 3 — what it shifts into. */}
			<div style={{position: 'absolute', left: B2.x + B2.w + 22, top: MID - 46}}>
				<FadeUp delay={T.shift + 8} distance={6}>
					<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 19, color: COLORS.red, whiteSpace: 'nowrap'}}>{C.shiftLabel}</span>
				</FadeUp>
			</div>
			<div style={{position: 'absolute', left: B3.x + 24, top: MID - 24}}>
				<MaskReveal delay={T.shift + 22}>
					<Txt size={27} weight={800}>
						{C.shifted}
					</Txt>
				</MaskReveal>
			</div>

			{/* The safeguard. */}
			<Block col={0} top={SAFETY_Y + 34}>
				<div style={{display: 'flex', alignItems: 'center', gap: 16}}>
					<Label delay={T.safeguard + 10} size={15} color={COLORS.red}>
						{C.safeguardLabel}
					</Label>
					<FadeUp delay={T.safeguard + 14} distance={6}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 18, color: COLORS.red}}>予防線</span>
					</FadeUp>
				</div>
				<div style={{marginTop: 18}}>
					<MaskReveal delay={T.safeguard + 16} duration={28}>
						<Txt size={38} weight={800}>
							{C.safeguard}
						</Txt>
					</MaskReveal>
				</div>
			</Block>

			{/* Closing panel. */}
			<AbsoluteFill style={{background: COLORS.black, clipPath: `inset(0 ${(1 - end) * 100}% 0 0)`}}>
				<AbsoluteFill style={{opacity: fadeOut}}>
					<div style={{position: 'absolute', left: GRID.marginX, top: 236, display: 'flex', alignItems: 'center', gap: 18}}>
						<div style={{width: 18, height: 18, background: COLORS.red}} />
						<Label delay={T.end + 16} size={18} color={COLORS.offWhite}>
							{C.endKicker}
						</Label>
					</div>
					<div style={{position: 'absolute', left: GRID.marginX, top: 300}}>
						<MaskReveal delay={T.end + 20} duration={26}>
							<div style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 96, color: COLORS.offWhite, letterSpacing: '0.01em', whiteSpace: 'nowrap'}}>
								{C.endTitle}
							</div>
						</MaskReveal>
					</div>
					<div style={{position: 'absolute', right: GRID.marginX, top: 236}}>
						<FadeUp delay={T.end + 24}>
							<span style={{fontFamily: FONTS.en, fontWeight: 500, fontSize: 16, letterSpacing: '0.08em', color: COLORS.gray}}>{C.endDate}</span>
						</FadeUp>
					</div>
					<Canvas>
						<DrawLine x1={GRID.marginX} y1={470} x2={VIDEO.width - GRID.marginX} y2={470} delay={T.end + 30} duration={30} color={COLORS.offWhite} width={2} />
					</Canvas>
					{SCENES.filter((s) => s.chapter).map((s, i) => (
						<div key={s.id} style={{position: 'absolute', left: colX((i % 4) * 3), top: 520 + Math.floor(i / 4) * 56}}>
							<FadeUp delay={T.end + 38 + i * 4} distance={8}>
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
