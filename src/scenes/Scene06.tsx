import React from 'react';
import {Canvas, DrawLine, DrawRect} from '../components/AnimatedLine';
import {Counter} from '../components/Counter';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, FONTS, VIDEO, GRID, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene06;

const CARD = {y: 352, h: 236, w: span(4)};
const NOTE_RULE_Y = 664;

const T = {count: 40, cards: 86, rule: 212, date: 275, text: 352};

export const Scene06: React.FC<SceneProps> = ({meta, showGrid}) => (
	<SceneFrame meta={meta} showGrid={showGrid}>
		<Block col={0} top={168}>
			<Heading size={72} delay={12}>
				{C.heading}
			</Heading>
		</Block>
		<Block col={8} top={168}>
			<div style={{display: 'flex', alignItems: 'flex-end', gap: 24}}>
				<Counter value={C.count} delay={T.count} size={124} color={COLORS.red} />
				<div style={{paddingBottom: 12}}>
					<Label delay={T.count + 14} size={15} color="#6E6E6A">
						{C.countLabel}
					</Label>
				</div>
			</div>
		</Block>

		<Canvas>
			{C.resources.map((_, i) => (
				<DrawRect key={i} x={colX(i * 4)} y={CARD.y} w={CARD.w} h={CARD.h} delay={T.cards + i * 12} duration={34} width={3} />
			))}
			<DrawLine x1={GRID.marginX} y1={NOTE_RULE_Y} x2={VIDEO.width - GRID.marginX} y2={NOTE_RULE_Y} delay={T.rule} duration={36} width={2} />
		</Canvas>
		{C.resources.map((r, i) => (
			<div key={i} style={{position: 'absolute', left: colX(i * 4) + 36, top: CARD.y + 34}}>
				<FadeUp delay={T.cards + 16 + i * 12}>
					<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 30, color: COLORS.black}}>{String(i + 1).padStart(2, '0')}</span>
				</FadeUp>
				<div style={{marginTop: 92}}>
					<MaskReveal delay={T.cards + 24 + i * 12}>
						<Txt size={34} weight={700}>
							{r}
						</Txt>
					</MaskReveal>
				</div>
			</div>
		))}

		{/* Source note: a date stated in the original memo, shown as such. */}
		<Block col={0} top={NOTE_RULE_Y + 30}>
			<Label delay={T.rule + 10} size={15} color="#6E6E6A">
				{C.dateLabel}
			</Label>
		</Block>
		<Block col={0} top={NOTE_RULE_Y + 68}>
			<MaskReveal delay={T.date}>
				<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 72, color: COLORS.red, letterSpacing: '-0.01em', lineHeight: 1}}>{C.date}</span>
			</MaskReveal>
		</Block>
		<Block col={5} top={NOTE_RULE_Y + 76}>
			<MaskReveal delay={T.text}>
				<Txt size={44} weight={800}>
					{C.dateText}
				</Txt>
			</MaskReveal>
		</Block>
		<Block col={9} top={NOTE_RULE_Y + 92}>
			<FadeUp delay={T.text + 16}>
				<span style={{fontFamily: FONTS.jp, fontWeight: 500, fontSize: 24, color: '#6E6E6A', letterSpacing: '0.04em', borderLeft: `3px solid ${COLORS.gray}`, paddingLeft: 16}}>
					{C.dateNote}
				</span>
			</FadeUp>
		</Block>
	</SceneFrame>
);
