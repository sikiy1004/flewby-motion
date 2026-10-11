import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine, DrawPath} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {Heading, Label, MaskReveal, Txt} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, GRID, VIDEO, colX} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene04;

const LABEL_Y = 300;
const RULE_Y = 336;
const ROW_H = 140;
const rowMid = (i: number) => RULE_Y + ROW_H * (i + 0.5);
const ARROW_X0 = colX(3) + 20;
const ARROW_X1 = colX(4) - 24;

const T = {labels: 40, rows: [138, 307, 500]};

const Cross: React.FC<{cx: number; cy: number; p: number}> = ({cx, cy, p}) => (
	<g opacity={p} transform={`translate(${cx} ${cy})`}>
		<line x1={-12 * p} y1={-12 * p} x2={12 * p} y2={12 * p} stroke={COLORS.red} strokeWidth={4} />
		<line x1={12 * p} y1={-12 * p} x2={-12 * p} y2={12 * p} stroke={COLORS.red} strokeWidth={4} />
	</g>
);

export const Scene04: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const at = (start: number, dur = 14) =>
		interpolate(frame, [start, start + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.out});

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={160}>
				<Heading size={64} delay={10}>
					{C.heading}
				</Heading>
			</Block>

			<Block col={0} top={LABEL_Y}>
				<Label delay={T.labels} size={14} color={COLORS.red}>
					{`× ${C.badLabel}`}
				</Label>
			</Block>
			<Block col={4} top={LABEL_Y}>
				<Label delay={T.labels + 6} size={14} color={COLORS.black}>
					{`○ ${C.goodLabel}`}
				</Label>
			</Block>

			<Canvas>
				<DrawLine x1={GRID.marginX} y1={RULE_Y} x2={VIDEO.width - GRID.marginX} y2={RULE_Y} delay={T.labels - 8} duration={30} width={2} />
				{C.pairs.map((_, i) => {
					const y = rowMid(i);
					const start = T.rows[i];
					return (
						<React.Fragment key={i}>
							<Cross cx={colX(0) + 12} cy={y} p={at(start)} />
							<DrawLine x1={ARROW_X0} y1={y} x2={ARROW_X1} y2={y} delay={start + 26} duration={14} width={3} />
							<DrawPath d={`M ${ARROW_X1 - 14} ${y - 12} L ${ARROW_X1} ${y} L ${ARROW_X1 - 14} ${y + 12}`} delay={start + 36} duration={6} width={3} />
							<circle cx={colX(4) + 12} cy={y} r={12 * at(start + 40)} fill="none" stroke={COLORS.black} strokeWidth={4} />
							<DrawLine
								x1={GRID.marginX}
								y1={RULE_Y + ROW_H * (i + 1)}
								x2={VIDEO.width - GRID.marginX}
								y2={RULE_Y + ROW_H * (i + 1)}
								delay={start + 6}
								duration={34}
								width={1}
								color={COLORS.gray}
							/>
						</React.Fragment>
					);
				})}
			</Canvas>

			{C.pairs.map((p, i) => {
				const y = rowMid(i);
				const start = T.rows[i];
				return (
					<React.Fragment key={p.bad}>
						<div style={{position: 'absolute', left: colX(0) + 44, top: y - 24, opacity: interpolate(at(start + 40, 20), [0, 1], [1, 0.5])}}>
							<MaskReveal delay={start + 2}>
								<Txt size={30} weight={700} color="#55554F">
									{p.bad}
								</Txt>
							</MaskReveal>
						</div>
						<div style={{position: 'absolute', left: colX(4) + 44, top: y - 27}}>
							<MaskReveal delay={start + 40} duration={26}>
								<Txt size={33} weight={800}>
									{p.good}
								</Txt>
							</MaskReveal>
						</div>
					</React.Fragment>
				);
			})}
		</SceneFrame>
	);
};
