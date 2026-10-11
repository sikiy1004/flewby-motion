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

// Diagram on columns 5–11.
const LEFT = colX(5);
const WIDTH = span(7);
const CENTER = LEFT + WIDTH / 2;
const BOX = {w: 200, h: 76, y: 300};
const PEOPLE_Y = 540;
const R = 44;
const people = Array.from({length: 5}).map((_, i) => LEFT + (WIDTH / 5) * (i + 0.5));
const TRACED = 3;

const T = {number: 24, people: 140, box: 200, links: 218, trace: 262, limit: 305, premise: 383};

export const Scene02: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const trace = useProgress(T.trace, 24, EASE.inOut);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			{/* Left: the number. */}
			<Block col={0} top={196}>
				<Counter value={C.number} delay={T.number} size={480} color={COLORS.red} />
			</Block>
			<Block col={0} top={640}>
				<div style={{display: 'flex', alignItems: 'baseline', gap: 18}}>
					<FadeUp delay={T.number + 16}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 56, color: COLORS.black}}>{C.unit}</span>
					</FadeUp>
					<Label delay={T.number + 22} size={16} color="#6E6E6A">
						{C.unitEn}
					</Label>
				</div>
			</Block>

			<Block col={5} top={168}>
				<Heading size={64} delay={12}>
					{C.heading}
				</Heading>
			</Block>

			{/* Statement → five people. With five, a statement is hard to keep unattributed. */}
			<Canvas>
				<DrawRect x={CENTER - BOX.w / 2} y={BOX.y} w={BOX.w} h={BOX.h} delay={T.box} duration={24} width={3} />
				{people.map((cx, i) => {
					const traced = i === TRACED;
					const fade = traced ? 1 : interpolate(trace, [0, 1], [1, 0.25]);
					return (
						<DrawLine
							key={cx}
							x1={CENTER}
							y1={BOX.y + BOX.h}
							x2={cx}
							y2={PEOPLE_Y - R - 8}
							delay={T.links + i * 4}
							duration={22}
							width={traced ? 3 : 2}
							color={traced ? interpolateColor(trace) : COLORS.black}
							opacity={fade}
						/>
					);
				})}
				{people.map((cx, i) => {
					const p = interpolate(frame, [T.people + i * 6, T.people + i * 6 + 16], [0, 1], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
						easing: EASE.out,
					});
					const traced = i === TRACED;
					return (
						<g key={cx} opacity={p} transform={`translate(${cx} ${PEOPLE_Y}) scale(${0.6 + 0.4 * p})`}>
							<circle r={R} fill={COLORS.black} fillOpacity={traced ? trace : 0} stroke={COLORS.black} strokeWidth={3} />
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
				<FadeUp delay={T.box + 14} distance={8}>
					<Txt size={34} weight={700}>
						{C.statement}
					</Txt>
				</FadeUp>
			</div>

			{/* The limit, stated plainly. */}
			<Block col={5} top={650}>
				<div style={{display: 'flex', alignItems: 'center', gap: 16}}>
					<div style={{width: 14, height: 14, background: COLORS.red, opacity: useProgress(T.limit, 12)}} />
					<Label delay={T.limit} color={COLORS.red} size={16}>
						{C.limitLabel}
					</Label>
				</div>
				<div style={{marginTop: 18}}>
					<MaskReveal delay={T.limit + 6}>
						<Txt size={60} weight={800}>
							{C.limit}
						</Txt>
					</MaskReveal>
				</div>
				<div style={{marginTop: 6}}>
					<FadeUp delay={T.premise}>
						<Txt size={30} color="#55554F">
							{C.premise}
						</Txt>
					</FadeUp>
				</div>
			</Block>
		</SceneFrame>
	);
};

const interpolateColor = (p: number) => (p > 0.5 ? COLORS.red : COLORS.black);
