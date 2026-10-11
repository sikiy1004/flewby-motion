import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine} from '../components/AnimatedLine';
import {Counter} from '../components/Counter';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene05;

const LIST_TOP = 286;
const ROW_H = 76;
const LIST_X = colX(3);
const LIST_W = span(9);

// Each item enters as the narration reaches it (frames, from narration cues).
const ITEM_AT = [130, 238, 325, 407, 542, 681, 781];
const T = {count: 30, rules: 60};

export const Scene05: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const active = ITEM_AT.reduce((acc, at, i) => (frame >= at ? i : acc), -1);
	// The marker steps down one row each time a new item is read.
	const barY = ITEM_AT.slice(1).reduce(
		(acc, at) => acc + interpolate(frame, [at, at + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.inOut}),
		0,
	);
	const barIn = useProgress(ITEM_AT[0], 10);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={160}>
				<Heading size={64} delay={10}>
					{C.heading}
				</Heading>
			</Block>

			{/* Count. */}
			<Block col={0} top={LIST_TOP + 4}>
				<Counter value={C.count} delay={T.count} countFrames={24} size={280} color={COLORS.red} />
				<div style={{display: 'flex', alignItems: 'baseline', gap: 14, marginTop: 16}}>
					<FadeUp delay={T.count + 14}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 40}}>{C.countUnit}</span>
					</FadeUp>
					<Label delay={T.count + 20} size={15} color="#6E6E6A">
						{C.countLabel}
					</Label>
				</div>
				<div style={{marginTop: 34}}>
					<MaskReveal delay={T.count + 30}>
						<span style={{display: 'inline-block', background: COLORS.black, color: COLORS.offWhite, fontFamily: FONTS.jp, fontWeight: 700, fontSize: 22, padding: '8px 16px', letterSpacing: '0.06em'}}>
							{C.sameText}
						</span>
					</MaskReveal>
				</div>
			</Block>

			{/* The seven items, ruled like a table. */}
			<Canvas>
				<DrawLine x1={LIST_X} y1={LIST_TOP} x2={LIST_X + LIST_W} y2={LIST_TOP} delay={T.rules} duration={26} width={2} />
				{C.items.map((_, i) => (
					<DrawLine
						key={i}
						x1={LIST_X}
						y1={LIST_TOP + ROW_H * (i + 1)}
						x2={LIST_X + LIST_W}
						y2={LIST_TOP + ROW_H * (i + 1)}
						delay={T.rules + 6 + i * 5}
						duration={22}
						width={1}
						color={COLORS.gray}
					/>
				))}
			</Canvas>

			{/* Reading position. */}
			<div
				style={{
					position: 'absolute',
					left: LIST_X,
					top: LIST_TOP + ROW_H * barY + 16,
					width: 6,
					height: ROW_H - 32,
					background: COLORS.red,
					opacity: barIn,
				}}
			/>

			{C.items.map((item, i) => {
				const shown = useProgress(ITEM_AT[i], 18);
				const isActive = i === active;
				return (
					<div
						key={item.text}
						style={{
							position: 'absolute',
							left: LIST_X + 30,
							top: LIST_TOP + ROW_H * i,
							height: ROW_H,
							display: 'flex',
							alignItems: 'center',
							gap: 26,
							opacity: shown,
							transform: `translateX(${(1 - shown) * -14}px)`,
						}}
					>
						<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 22, width: 30, color: item.key ? COLORS.red : COLORS.black}}>
							{String(i + 1).padStart(2, '0')}
						</span>
						<Txt size={27} weight={item.key || isActive ? 700 : 500} color={isActive || item.key ? COLORS.black : '#55554F'}>
							{item.text}
						</Txt>
						{item.note ? (
							<Txt size={20} color="#6E6E6A" style={{marginLeft: 4}}>
								{`（${item.note}）`}
							</Txt>
						) : null}
					</div>
				);
			})}
		</SceneFrame>
	);
};
