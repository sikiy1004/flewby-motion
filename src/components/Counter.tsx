import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {COLORS, EASE, FONTS} from '../theme';

type Props = {
	value: number;
	delay?: number;
	/** Frames spent counting up from 0. 0 = the final number simply slides in. */
	countFrames?: number;
	size?: number;
	color?: string;
	pad?: number;
	style?: React.CSSProperties;
};

/** Bold Inter numeral that arrives slightly after its text, rising from a mask. */
export const Counter: React.FC<Props> = ({value, delay = 0, countFrames = 0, size = 200, color = COLORS.red, pad = 0, style}) => {
	const frame = useCurrentFrame();
	const enter = interpolate(frame, [delay, delay + 22], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: EASE.out,
	});
	const current =
		countFrames > 0
			? Math.round(
					interpolate(frame, [delay, delay + countFrames], [0, value], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
						easing: EASE.out,
					}),
				)
			: value;
	return (
		<div style={{overflow: 'hidden', lineHeight: 0.86, ...style}}>
			<div
				style={{
					fontFamily: FONTS.en,
					fontWeight: 800,
					fontSize: size,
					color,
					letterSpacing: '-0.04em',
					marginLeft: '-0.05em',
					fontVariantNumeric: 'tabular-nums',
					transform: `translateY(${(1 - enter) * 100}%)`,
				}}
			>
				{String(current).padStart(pad, '0')}
			</div>
		</div>
	);
};
