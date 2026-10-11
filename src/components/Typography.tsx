import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {isPdfPlaceholder} from '../data/scenes';
import {COLORS, EASE, FONTS} from '../theme';

/** 0→1 progress for an entrance starting at `delay` frames. */
export const useProgress = (delay: number, duration = 20, easing = EASE.out) => {
	const frame = useCurrentFrame();
	return interpolate(frame, [delay, delay + duration], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing,
	});
};

type RevealProps = {
	delay?: number;
	duration?: number;
	style?: React.CSSProperties;
	children: React.ReactNode;
};

/** Text revealed by a horizontal mask, with a short lateral settle. */
export const MaskReveal: React.FC<RevealProps> = ({delay = 0, duration = 22, style, children}) => {
	const p = useProgress(delay, duration);
	return (
		<div
			style={{
				clipPath: `inset(-10% ${(1 - p) * 100}% -10% 0)`,
				transform: `translateX(${(1 - p) * -24}px)`,
				...style,
			}}
		>
			{children}
		</div>
	);
};

/** Short vertical move + fade, used for secondary copy. */
export const FadeUp: React.FC<RevealProps & {distance?: number}> = ({
	delay = 0,
	duration = 18,
	distance = 16,
	style,
	children,
}) => {
	const p = useProgress(delay, duration);
	return (
		<div style={{opacity: p, transform: `translateY(${(1 - p) * distance}px)`, ...style}}>{children}</div>
	);
};

type LabelProps = {
	children: string;
	delay?: number;
	color?: string;
	size?: number;
	style?: React.CSSProperties;
};

/** Latin uppercase label whose tracking tightens as it fades in. */
export const Label: React.FC<LabelProps> = ({children, delay = 0, color = COLORS.black, size = 18, style}) => {
	const p = useProgress(delay, 30);
	return (
		<div
			style={{
				fontFamily: FONTS.en,
				fontWeight: 700,
				fontSize: size,
				letterSpacing: `${interpolate(p, [0, 1], [0.5, 0.16])}em`,
				textTransform: 'uppercase',
				color,
				opacity: p,
				whiteSpace: 'nowrap',
				lineHeight: 1,
				...style,
			}}
		>
			{children}
		</div>
	);
};

type HeadingProps = {
	children: string;
	size?: number;
	color?: string;
	delay?: number;
	weight?: 700 | 800;
	style?: React.CSSProperties;
};

export const Heading: React.FC<HeadingProps> = ({children, size = 76, color = COLORS.black, delay = 0, weight = 800, style}) => (
	<MaskReveal delay={delay} duration={24}>
		<div
			style={{
				fontFamily: FONTS.jp,
				fontWeight: weight,
				fontSize: size,
				lineHeight: 1.18,
				letterSpacing: '0.02em',
				color,
				whiteSpace: 'nowrap',
				...style,
			}}
		>
			{children}
		</div>
	</MaskReveal>
);

type TextProps = {
	children: string;
	size?: number;
	weight?: 400 | 500 | 700 | 800;
	color?: string;
	style?: React.CSSProperties;
};

/**
 * Japanese body text. Strings marked with PDF() are rendered as a visibly flagged
 * placeholder so that untranscribed source wording can never pass as final copy.
 */
export const Txt: React.FC<TextProps> = ({children, size = 32, weight = 500, color = COLORS.black, style}) => {
	if (isPdfPlaceholder(children)) {
		return (
			<span
				style={{
					fontFamily: FONTS.jp,
					fontWeight: 500,
					fontSize: size * 0.8,
					color: '#8C8C87',
					borderBottom: `2px dashed ${COLORS.gray}`,
					paddingBottom: 2,
					whiteSpace: 'nowrap',
					...style,
				}}
			>
				{children}
			</span>
		);
	}
	return (
		<span
			style={{
				fontFamily: FONTS.jp,
				fontWeight: weight,
				fontSize: size,
				lineHeight: 1.5,
				letterSpacing: '0.03em',
				color,
				whiteSpace: 'nowrap',
				...style,
			}}
		>
			{children}
		</span>
	);
};
