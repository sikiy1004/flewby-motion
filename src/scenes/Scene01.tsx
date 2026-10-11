import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Canvas, DrawLine, DrawPath} from '../components/AnimatedLine';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt, useProgress} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, EASE, FONTS, GRID, VIDEO, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene01;

// Table geometry: header row, then one row per track.
const HEADER_Y = 326;
const HEADER_RULE = 366;
const ROW_H = 130;
const ROW_Y = [HEADER_RULE + ROW_H / 2, HEADER_RULE + ROW_H * 1.5];
const TABLE_X0 = colX(2);
const TABLE_X1 = VIDEO.width - GRID.marginX;
const ORIGIN = {x: colX(0), w: span(2), h: 120};
const ORIGIN_MID = HEADER_RULE + ROW_H;
const NODE_X = colX(2) + 34;
const FIELD_COLS = [4, 6, 9];
const REASON_Y = 690;

// Timing (frames) — follows the narration cues.
const T = {origin: 30, header: 56, rows: [100, 211], reasons: [300, 446]};

export const Scene01: React.FC<SceneProps> = ({meta, showGrid}) => {
	const frame = useCurrentFrame();
	const originP = useProgress(T.origin, 24);

	return (
		<SceneFrame meta={meta} showGrid={showGrid}>
			<Block col={0} top={168}>
				<Heading size={80} delay={12}>
					{C.heading}
				</Heading>
			</Block>

			{/* Column headers. */}
			{C.fields.map((f, i) => (
				<Block key={f} col={FIELD_COLS[i]} top={HEADER_Y}>
					<FadeUp delay={T.header + i * 5} distance={8}>
						<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 20, letterSpacing: '0.12em', color: i === 2 ? COLORS.red : '#6E6E6A'}}>{f}</span>
					</FadeUp>
				</Block>
			))}

			{/* Origin: the single request. */}
			<div
				style={{
					position: 'absolute',
					left: ORIGIN.x,
					top: ORIGIN_MID - ORIGIN.h / 2,
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
				<DrawLine x1={TABLE_X0} y1={HEADER_RULE} x2={TABLE_X1} y2={HEADER_RULE} delay={T.header - 6} duration={30} width={2} />
				{ROW_Y.map((y, i) => (
					<React.Fragment key={y}>
						<DrawPath
							d={`M ${ORIGIN.x + ORIGIN.w} ${ORIGIN_MID} H ${TABLE_X0 - 8} V ${y} H ${NODE_X - 24}`}
							delay={T.rows[i] - 14}
							duration={20}
							width={3}
						/>
						<DrawLine x1={TABLE_X0} y1={y + ROW_H / 2} x2={TABLE_X1} y2={y + ROW_H / 2} delay={T.rows[i] + 4} duration={34} width={1} color={COLORS.gray} />
					</React.Fragment>
				))}
			</Canvas>

			{C.tracks.map((t, i) => {
				const start = T.rows[i];
				const node = interpolate(frame, [start - 4, start + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: EASE.out});
				const y = ROW_Y[i];
				return (
					<React.Fragment key={t.key}>
						<div
							style={{
								position: 'absolute',
								left: NODE_X - 24,
								top: y - 24,
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
								fontSize: 20,
								color: COLORS.offWhite,
							}}
						>
							{i === 0 ? 'A' : 'B'}
						</div>
						<div style={{position: 'absolute', left: NODE_X + 40, top: y - 34}}>
							<MaskReveal delay={start + 2}>
								<Txt size={40} weight={800}>
									{t.key}
								</Txt>
							</MaskReveal>
							<Label delay={start + 8} size={13} color="#6E6E6A" style={{marginTop: 2}}>
								{t.en}
							</Label>
						</div>
						{t.cells.map((cell, j) => (
							<div key={cell} style={{position: 'absolute', left: colX(FIELD_COLS[j]), top: y - 26}}>
								<MaskReveal delay={start + 10 + j * 8}>
									<Txt size={j === 0 ? 32 : 27} weight={j === 0 ? 800 : 700}>
										{cell}
									</Txt>
								</MaskReveal>
							</div>
						))}
					</React.Fragment>
				);
			})}

			{/* Why: the memo's reasons for the split. */}
			{C.reasons.map((r, i) => (
				<Block key={r} col={0} top={REASON_Y + i * 62}>
					<FadeUp delay={T.reasons[i]}>
						<div style={{display: 'flex', alignItems: 'center', gap: 20}}>
							<div style={{width: 6, height: 30, background: i === 0 ? COLORS.black : COLORS.red}} />
							<Txt size={28} weight={i === 1 ? 700 : 500}>
								{r}
							</Txt>
						</div>
					</FadeUp>
				</Block>
			))}
		</SceneFrame>
	);
};
