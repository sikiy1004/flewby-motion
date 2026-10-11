import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine, DrawPath} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, GRID, VIDEO, colX} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene07;

const ROW_TOP = 190;
const ROW_H = 118;
const ROWS_X = colX(4);
const AXIS_X = colX(3) + 40;

const T = {axis: 30, rows: 40, top: 91};

export const Scene07: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const top = useProgress(T.top, 16);
	const axisEnd = ROW_TOP + ROW_H * C.books.length - 30;

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={160}>
				<Heading size={80} delay={10}>
					{C.heading}
				</Heading>
			</Block>
			<Block col={0} top={280}>
				<Label delay={20} size={14} color="#6E6E6A">
					{C.headingEn}
				</Label>
			</Block>

			{/* Priority axis. */}
			<Canvas>
				<DrawLine x1={AXIS_X} y1={ROW_TOP + 20} x2={AXIS_X} y2={axisEnd} delay={T.axis} duration={40} width={2} />
				<DrawPath d={`M ${AXIS_X - 10} ${axisEnd - 14} L ${AXIS_X} ${axisEnd} L ${AXIS_X + 10} ${axisEnd - 14}`} delay={T.axis + 38} duration={8} width={2} />
				{C.books.map((_, i) => (
					<DrawLine
						key={i}
						x1={ROWS_X}
						y1={ROW_TOP + ROW_H * (i + 1) - 10}
						x2={VIDEO.width - GRID.marginX}
						y2={ROW_TOP + ROW_H * (i + 1) - 10}
						delay={T.rows + 8 + i * 8}
						duration={26}
						width={1}
						color={COLORS.gray}
					/>
				))}
			</Canvas>
			<div style={{position: 'absolute', left: AXIS_X - 70, top: ROW_TOP + 20, width: 52, textAlign: 'right'}}>
				<FadeUp delay={T.axis + 10}>
					<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 18, color: '#6E6E6A', writingMode: 'vertical-rl', letterSpacing: '0.3em'}}>{C.order}</span>
				</FadeUp>
			</div>

			{C.books.map((b, i) => {
				const p = interpolate(frame, [T.rows + i * 8, T.rows + 20 + i * 8], [0, 1], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
					easing: EASE.out,
				});
				const y = ROW_TOP + ROW_H * i;
				return (
					<div
						key={b.title}
						style={{
							position: 'absolute',
							left: ROWS_X,
							top: y,
							display: 'flex',
							gap: 28,
							opacity: p,
							transform: `translateX(${(1 - p) * -16}px)`,
						}}
					>
						<div style={{width: 12, height: ROW_H - 34, background: b.top ? COLORS.red : COLORS.black, transform: `scaleY(${b.top ? 0.4 + 0.6 * top : 1})`, transformOrigin: 'bottom'}} />
						<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 28, width: 34, lineHeight: 1, color: b.top ? COLORS.red : COLORS.black}}>{i + 1}</span>
						<div>
							<div style={{fontFamily: FONTS.en, fontWeight: 500, fontSize: 18, color: '#6E6E6A', letterSpacing: '0.04em', height: 22}}>{b.author}</div>
							<div style={{display: 'flex', alignItems: 'baseline', gap: 14, marginTop: 4}}>
								<Txt size={30} weight={800}>
									{b.title}
								</Txt>
								{b.detail ? (
									<Txt size={22} weight={500} color="#3A3A38">
										{b.detail}
									</Txt>
								) : null}
								{b.note && b.top ? (
									<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 18, color: COLORS.offWhite, background: COLORS.red, padding: '2px 10px', opacity: top}}>{b.note}</span>
								) : null}
							</div>
							{b.note && !b.top ? (
								<div style={{marginTop: 2}}>
									<Txt size={20} color="#6E6E6A">
										{`— ${b.note}`}
									</Txt>
								</div>
							) : null}
						</div>
					</div>
				);
			})}
		</SceneFrame>
	);
};
