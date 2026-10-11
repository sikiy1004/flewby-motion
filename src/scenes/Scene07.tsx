import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, Txt} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene07;

const ROW_TOP = 300;
const ROW_H = 150;
const SPINE_W = 18;

const T = {rows: 60, note: 187};

export const Scene07: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={168}>
				<Heading size={80} delay={12}>
					{C.heading}
				</Heading>
			</Block>
			<Block col={0} top={290}>
				<Label delay={24} size={16} color="#6E6E6A">
					{C.headingEn}
				</Label>
			</Block>
			<Block col={0} top={ROW_TOP + ROW_H * 2 + 40} width={span(4)}>
				<FadeUp delay={T.note}>
					<div style={{borderLeft: `3px solid ${COLORS.red}`, paddingLeft: 18}}>
						<Txt size={24} color="#55554F">
							{C.note}
						</Txt>
					</div>
				</FadeUp>
			</Block>

			<Canvas>
				{C.books.map((_, i) => (
					<DrawLine
						key={i}
						x1={colX(5)}
						y1={ROW_TOP + ROW_H * (i + 1) - 18}
						x2={colX(11) + span(1)}
						y2={ROW_TOP + ROW_H * (i + 1) - 18}
						delay={T.rows + 10 + i * 18}
						duration={30}
						width={1}
						color={COLORS.gray}
					/>
				))}
			</Canvas>

			{C.books.map((b, i) => {
				const p = interpolate(frame, [T.rows + i * 18, T.rows + 22 + i * 18], [0, 1], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
					easing: EASE.out,
				});
				const top = ROW_TOP + ROW_H * i;
				return (
					<React.Fragment key={i}>
						{/* Spine */}
						<div
							style={{
								position: 'absolute',
								left: colX(5),
								top,
								width: SPINE_W,
								height: ROW_H - 46,
								background: COLORS.black,
								transform: `scaleY(${p})`,
								transformOrigin: 'bottom',
							}}
						/>
						<div
							style={{
								position: 'absolute',
								left: colX(5) + SPINE_W + 36,
								top: top - 4,
								opacity: p,
								transform: `translateX(${(1 - p) * -16}px)`,
							}}
						>
							<div style={{display: 'flex', gap: 16, alignItems: 'baseline'}}>
								<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 16, color: COLORS.red, letterSpacing: '0.08em'}}>{String(i + 1).padStart(2, '0')}</span>
								<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 14, color: '#6E6E6A', letterSpacing: '0.18em'}}>TITLE</span>
							</div>
							<div style={{marginTop: 6}}>
								<Txt size={36} weight={700}>
									{b.title}
								</Txt>
							</div>
							<div style={{display: 'flex', gap: 16, alignItems: 'baseline', marginTop: 4}}>
								<span style={{fontFamily: FONTS.en, fontWeight: 700, fontSize: 14, color: '#6E6E6A', letterSpacing: '0.18em'}}>AUTHOR</span>
								<Txt size={26}>{b.author}</Txt>
							</div>
						</div>
					</React.Fragment>
				);
			})}
		</SceneFrame>
	);
};
