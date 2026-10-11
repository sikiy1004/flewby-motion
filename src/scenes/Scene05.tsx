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

const LIST_TOP = 300;
const ROW_H = 70;
const PANEL = {x: colX(8), y: LIST_TOP, w: span(4), h: ROW_H * 7};

const T = {rows: 104, count: 247, panel: 342, record: 481, exLabel: 597, ex: 677, note: 772};

export const Scene05: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const panel = useProgress(T.panel, 26, EASE.inOut);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={168}>
				<Heading size={72} delay={12}>
					{C.heading}
				</Heading>
			</Block>

			{/* Count. */}
			<Block col={0} top={LIST_TOP - 6}>
				<Counter value={C.count} delay={T.count} countFrames={30} size={300} color={COLORS.red} />
				<div style={{display: 'flex', alignItems: 'baseline', gap: 14, marginTop: 18}}>
					<FadeUp delay={T.count + 14}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 40}}>{C.countUnit}</span>
					</FadeUp>
					<Label delay={T.count + 20} size={15} color="#6E6E6A">
						{C.countLabel}
					</Label>
				</div>
			</Block>

			{/* The seven items, ruled like a table. */}
			<Canvas>
				<DrawLine x1={colX(3)} y1={LIST_TOP} x2={colX(7) + span(1)} y2={LIST_TOP} delay={T.rows - 10} duration={24} width={2} />
				{C.items.map((_, i) => (
					<DrawLine
						key={i}
						x1={colX(3)}
						y1={LIST_TOP + ROW_H * (i + 1)}
						x2={colX(7) + span(1)}
						y2={LIST_TOP + ROW_H * (i + 1)}
						delay={T.rows + i * 10}
						duration={22}
						width={1}
						color={COLORS.gray}
					/>
				))}
			</Canvas>
			{C.items.map((item, i) => {
				const p = interpolate(frame, [T.rows + 6 + i * 10, T.rows + 26 + i * 10], [0, 1], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
					easing: EASE.out,
				});
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							left: colX(3),
							top: LIST_TOP + ROW_H * i,
							height: ROW_H,
							display: 'flex',
							alignItems: 'center',
							gap: 28,
							opacity: p,
							transform: `translateX(${(1 - p) * -14}px)`,
						}}
					>
						<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 22, width: 32, color: COLORS.black}}>{String(i + 1).padStart(2, '0')}</span>
						<Txt size={28}>{item}</Txt>
					</div>
				);
			})}

			{/* Black panel: how records are handled. */}
			<div
				style={{
					position: 'absolute',
					left: PANEL.x,
					top: PANEL.y,
					width: PANEL.w,
					height: PANEL.h,
					background: COLORS.black,
					clipPath: `inset(0 0 0 ${(1 - panel) * 100}%)`,
					padding: 44,
					boxSizing: 'border-box',
				}}
			>
				<Label delay={T.panel + 16} size={15} color={COLORS.gray}>
					{C.recordLabel}
				</Label>
				<div style={{marginTop: 22}}>
					{C.recordLines.map((line, i) => (
						<MaskReveal key={line} delay={T.record + i * 8}>
							<div style={{fontFamily: FONTS.jp, fontWeight: 800, fontSize: 44, lineHeight: 1.32, color: COLORS.offWhite}}>{line}</div>
						</MaskReveal>
					))}
				</div>
				<div style={{height: 2, background: '#3A3A38', width: `${useProgress(T.exLabel - 12, 20, EASE.line) * 100}%`, marginTop: 26}} />
				<div style={{marginTop: 24}}>
					<Label delay={T.exLabel} size={15} color={COLORS.red}>
						{C.exceptionLabel}
					</Label>
				</div>
				<div style={{marginTop: 22, display: 'flex', flexDirection: 'column', gap: 12}}>
					{C.exceptions.map((ex, i) => (
						<FadeUp key={ex} delay={T.ex + i * 14} distance={10}>
							<div style={{display: 'flex', alignItems: 'center', gap: 18}}>
								<div style={{width: 14, height: 14, background: COLORS.red}} />
								<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 36, color: COLORS.offWhite}}>{ex}</span>
							</div>
						</FadeUp>
					))}
				</div>
				<div style={{marginTop: 16}}>
					<FadeUp delay={T.note}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 500, fontSize: 24, color: COLORS.gray, letterSpacing: '0.04em'}}>{C.exceptionNote}</span>
					</FadeUp>
				</div>
			</div>
		</SceneFrame>
	);
};
