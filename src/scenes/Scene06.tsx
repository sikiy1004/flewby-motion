import React from 'react';
import {Canvas, DrawRect} from '../components/AnimatedLine';
import {Counter} from '../components/Counter';
import {Block, SceneFrame} from '../components/Grid';
import {FadeUp, Heading, Label, MaskReveal, Txt} from '../components/Typography';
import {COPY} from '../data/scenes';
import {COLORS, FONTS, colX, span} from '../theme';
import type {SceneProps} from '../Video';

const C = COPY.scene06;

const CARD = {y: 318, h: 468, w: span(4), pad: 36};

// Each card enters as the narration names it (frames).
const CARD_AT = [100, 278, 423];
const T = {count: 30};

export const Scene06: React.FC<SceneProps> = ({meta, showGrid}) => (
	<SceneFrame meta={meta} showGrid={showGrid}>
		<Block col={0} top={160}>
			<Heading size={64} delay={10}>
				{C.heading}
			</Heading>
		</Block>
		<Block col={8} top={150}>
			<div style={{display: 'flex', alignItems: 'flex-end', gap: 24}}>
				<Counter value={C.count} delay={T.count} size={124} color={COLORS.red} />
				<div style={{paddingBottom: 12}}>
					<Label delay={T.count + 14} size={14} color="#6E6E6A">
						{C.countLabel}
					</Label>
				</div>
			</div>
		</Block>

		<Canvas>
			{C.resources.map((_, i) => (
				<DrawRect key={i} x={colX(i * 4)} y={CARD.y} w={CARD.w} h={CARD.h} delay={CARD_AT[i] - 10} duration={30} width={3} />
			))}
		</Canvas>

		{C.resources.map((r, i) => {
			const at = CARD_AT[i];
			const inner = CARD.w - CARD.pad * 2;
			return (
				<div key={r.title} style={{position: 'absolute', left: colX(i * 4) + CARD.pad, top: CARD.y + CARD.pad, width: inner, height: CARD.h - CARD.pad * 2}}>
					<FadeUp delay={at + 4}>
						<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 28, color: COLORS.black}}>{String(i + 1).padStart(2, '0')}</span>
					</FadeUp>
					<div style={{marginTop: 22}}>
						<MaskReveal delay={at + 10}>
							<Txt size={28} weight={800} width={inner} lineHeight={1.4}>
								{r.title}
							</Txt>
						</MaskReveal>
					</div>
					{r.date ? (
						<div style={{marginTop: 14, display: 'flex', alignItems: 'baseline', gap: 12}}>
							<MaskReveal delay={at + 22}>
								<span style={{fontFamily: FONTS.en, fontWeight: 800, fontSize: 52, color: COLORS.red, letterSpacing: '-0.01em', lineHeight: 1}}>{r.date}</span>
							</MaskReveal>
							<FadeUp delay={at + 32}>
								<span style={{fontFamily: FONTS.jp, fontWeight: 700, fontSize: 24, color: COLORS.red}}>{r.dateNote}</span>
							</FadeUp>
						</div>
					) : null}
					<div style={{marginTop: 22}}>
						<FadeUp delay={at + 26}>
							<Txt size={22} color="#3A3A38" width={inner} lineHeight={1.75}>
								{r.body}
							</Txt>
						</FadeUp>
					</div>
					{r.url ? (
						<div style={{position: 'absolute', left: 0, bottom: 0}}>
							<FadeUp delay={at + 36}>
								<span style={{fontFamily: FONTS.en, fontWeight: 500, fontSize: 16, color: '#6E6E6A', letterSpacing: '0.02em'}}>{r.url}</span>
							</FadeUp>
						</div>
					) : null}
				</div>
			);
		})}
	</SceneFrame>
);
