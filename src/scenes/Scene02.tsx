import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine, DrawRect} from '../components/AnimatedLine';
import {Counter} from '../components/Counter';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene02;

// Diagram on columns 5–11: one statement, five people, one of them identifiable.
const LEFT = colX(5);
const WIDTH = span(7);
const CENTER = LEFT + WIDTH / 2;
const BOX = {w: 160, h: 62, y: 276};
const PEOPLE_Y = 428;
const R = 34;
const people = Array.from({length: 5}).map((_, i) => LEFT + (WIDTH / 5) * (i + 0.5));
const TRACED = 3;

const T = {number: 18, people: 30, box: 44, links: 56, trace: 96, limit: 40, promise: 129, response: [235, 363]};

export const Scene02: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const trace = useProgress(T.trace, 24, EASE.inOut);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			{/* Left: the number. */}
			<Block col={0} top={190}>
				<Counter value={C.number} delay={T.number} size={420} color={COLORS.red} />
			</Block>
			<Block col={0} top={568}>
				<div style={{display: 'flex', alignItems: 'baseline', gap: 18}}>
					<FadeUp delay={T.number + 16}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 52, color: COLORS.black}}>{C.unit}</span>
					</FadeUp>
					<Label delay={T.number + 22} size={16} color="#6E6E6A">
						{C.unitEn}
					</Label>
				</div>
			</Block>

			<Block col={5} top={160}>
				<Heading size={60} delay={10}>
					{C.heading}
				</Heading>
			</Block>

			<Canvas>
				<DrawRect x={CENTER - BOX.w / 2} y={BOX.y} w={BOX.w} h={BOX.h} delay={T.box} duration={20} width={3} />
				{people.map((cx, i) => {
					const traced = i === TRACED;
					return (
						<DrawLine
							key={cx}
							x1={CENTER}
							y1={BOX.y + BOX.h}
							x2={cx}
							y2={PEOPLE_Y - R - 6}
							delay={T.links + i * 3}
							duration={20}
							width={traced ? 3 : 2}
							color={traced && trace > 0.5 ? COLORS.red : COLORS.black}
							opacity={traced ? 1 : interpolate(trace, [0, 1], [1, 0.2])}
						/>
					);
				})}
				{people.map((cx, i) => {
					const p = interpolate(frame, [T.people + i * 4, T.people + i * 4 + 14], [0, 1], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
						easing: EASE.out,
					});
					return (
						<g key={cx} opacity={p} transform={`translate(${cx} ${PEOPLE_Y}) scale(${0.6 + 0.4 * p})`}>
							<circle r={R} fill={COLORS.black} fillOpacity={i === TRACED ? trace : 0} stroke={COLORS.black} strokeWidth={3} />
						</g>
					);
				})}
			</Canvas>
			<div
				style={{
					position: 'absolute',
					left: CENTER - BOX.w / 2,
					top: BOX.y,
					width: BOX.w,
					height: BOX.h,
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'center',
				}}
			>
				<FadeUp delay={T.box + 10} distance={6}>
					<Txt size={28} weight={700}>
						{C.statement}
					</Txt>
				</FadeUp>
			</div>

			{/* The constraint, stated as the memo states it. */}
			<Block col={5} top={510}>
				<div style={{display: 'flex', alignItems: 'center', gap: 14}}>
					<div style={{width: 14, height: 14, background: COLORS.red, opacity: useProgress(T.limit, 12)}} />
					<Label delay={T.limit} color={COLORS.red} size={15}>
						{C.limitLabel}
					</Label>
				</div>
				<div style={{marginTop: 12}}>
					<MaskReveal delay={T.limit + 6}>
						<Txt size={54} weight={800}>
							{C.limit}
						</Txt>
					</MaskReveal>
				</div>
				<div style={{marginTop: 2}}>
					<FadeUp delay={T.promise}>
						<Txt size={27} color="#55554F">
							{C.promise}
						</Txt>
					</FadeUp>
				</div>
			</Block>

			{/* What follows from it. */}
			<Canvas>
				<DrawLine x1={colX(5)} y1={692} x2={colX(11) + span(1)} y2={692} delay={T.response[0] - 16} duration={28} width={2} />
			</Canvas>
			<Block col={5} top={712}>
				{C.responses.map((r, i) => (
					<FadeUp key={r} delay={T.response[i]} style={{display: 'flex', gap: 18, marginBottom: 12}}>
						<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 24, lineHeight: 1.5, color: COLORS.red}}>→</span>
						<Txt size={25} weight={700} width={span(7) - 44} lineHeight={1.5}>
							{r}
						</Txt>
					</FadeUp>
				))}
			</Block>
		</SceneFrame>
	);
};
