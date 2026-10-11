import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine, DrawPath} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene01;

// Diagram geometry (px). Origin box spans columns 0–1.
const ORIGIN = {x: colX(0), y: 505, w: span(2), h: 120};
const MID_Y = ORIGIN.y + ORIGIN.h / 2;
const BRANCH_X = colX(3);
const TRACK_Y = [450, 680];
const NODE_X = colX(4) + 22;
const LABEL_X = colX(4) + 70;
const TRACK_START = NODE_X + 24;
const TRACK_END = colX(11) + 118;

// Timing (frames) — follows the narration cues.
const T = {origin: 40, stem: 70, branch: 100, a: 180, b: 258, split: 370, why: 470};

export const Scene01: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const originP = useProgress(T.origin, 24);
	const cross = useProgress(T.split + 30, 16);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={168}>
				<Heading size={80} delay={14}>
					{C.heading}
				</Heading>
			</Block>
			<Block col={0} top={286}>
				<FadeUp delay={34}>
					<Txt size={30} color="#55554F">
						{C.lead}
					</Txt>
				</FadeUp>
			</Block>

			{/* Origin: the single request. */}
			<div
				style={{
					position: 'absolute',
					left: ORIGIN.x,
					top: ORIGIN.y,
					width: ORIGIN.w,
					height: ORIGIN.h,
					background: COLORS.black,
					clipPath: `inset(0 ${(1 - originP) * 100}% 0 0)`,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
				}}
			>
				<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 44, color: COLORS.offWhite, letterSpacing: '0.1em'}}>{C.origin}</span>
			</div>

			<Canvas>
				<DrawLine x1={ORIGIN.x + ORIGIN.w} y1={MID_Y} x2={BRANCH_X} y2={MID_Y} delay={T.stem} duration={20} width={3} />
				{TRACK_Y.map((y, i) => (
					<DrawPath key={y} d={`M ${BRANCH_X} ${MID_Y} V ${y} H ${NODE_X - 24}`} delay={T.branch + i * 8} duration={26} width={3} />
				))}
				<DrawLine x1={TRACK_START} y1={TRACK_Y[0]} x2={TRACK_END} y2={TRACK_Y[0]} delay={T.a + 2} duration={50} width={3} />
				<DrawLine x1={TRACK_START} y1={TRACK_Y[1]} x2={TRACK_END} y2={TRACK_Y[1]} delay={T.b + 2} duration={50} width={3} />
				{/* A would-be merge of the two tracks, drawn then struck out. */}
				<DrawLine x1={TRACK_END - 60} y1={TRACK_Y[0] + 16} x2={TRACK_END - 60} y2={TRACK_Y[1] - 16} delay={T.split} duration={24} color={COLORS.gray} width={3} dashed />
				<g opacity={cross} transform={`translate(${TRACK_END - 60} ${(TRACK_Y[0] + TRACK_Y[1]) / 2})`}>
					<line x1={-26 * cross} y1={-26 * cross} x2={26 * cross} y2={26 * cross} stroke={COLORS.red} strokeWidth={6} />
					<line x1={26 * cross} y1={-26 * cross} x2={-26 * cross} y2={26 * cross} stroke={COLORS.red} strokeWidth={6} />
				</g>
			</Canvas>

			{C.tracks.map((t, i) => {
				const start = i === 0 ? T.a : T.b;
				const node = interpolate(frame, [start - 6, start + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.out});
				return (
					<React.Fragment key={t.key}>
						<div
							style={{
								position: 'absolute',
								left: NODE_X - 24,
								top: TRACK_Y[i] - 24,
								width: 48,
								height: 48,
								borderRadius: 24,
								background: COLORS.black,
								transform: `scale(${node})`,
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
								fontFamily: FONTS.en,
								fontWeight: 800,
								fontSize: 22,
								color: COLORS.offWhite,
							}}
						>
							{t.key}
						</div>
						<div style={{position: 'absolute', left: LABEL_X, top: TRACK_Y[i] - 78}}>
							<MaskReveal delay={start + 4}>
								<Txt size={48} weight={800}>
									{t.jp}
								</Txt>
							</MaskReveal>
						</div>
						<div style={{position: 'absolute', left: LABEL_X, top: TRACK_Y[i] + 20}}>
							<Label delay={start + 12} size={15} color="#6E6E6A">
								{t.en}
							</Label>
						</div>
					</React.Fragment>
				);
			})}

			<Block col={4} top={TRACK_Y[1] + 92} style={{marginLeft: LABEL_X - colX(4)}}>
				<FadeUp delay={T.why}>
					<div style={{display: 'flex', alignItems: 'center', gap: 24}}>
						<Label delay={T.why} color={COLORS.red} size={16}>
							{C.whyLabel}
						</Label>
						<Txt size={28}>{C.why}</Txt>
					</div>
				</FadeUp>
			</Block>
		</SceneFrame>
	);
};
