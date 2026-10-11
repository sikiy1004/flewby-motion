import {getLength} from '@remotion/paths';
import React, {useMemo} from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {COLORS, EASE, VIDEO} from '../theme';

type PathProps = {
	d: string;
	delay?: number;
	duration?: number;
	color?: string;
	width?: number;
	dashed?: boolean;
	opacity?: number;
};

/** SVG path drawn with strokeDasharray / strokeDashoffset. Use inside <Canvas>. */
export const DrawPath: React.FC<PathProps> = ({
	d,
	delay = 0,
	duration = 24,
	color = COLORS.black,
	width = 2,
	dashed = false,
	opacity = 1,
}) => {
	const frame = useCurrentFrame();
	const length = useMemo(() => getLength(d), [d]);
	const p = interpolate(frame, [delay, delay + duration], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
		easing: EASE.line,
	});
	if (dashed) {
		// Dashed strokes cannot also use dasharray for drawing, so mask them instead.
		const id = `m${Math.abs(hash(d))}`;
		return (
			<g opacity={opacity}>
				<defs>
					<mask id={id} maskUnits="userSpaceOnUse">
						<path d={d} stroke="#fff" strokeWidth={width + 6} fill="none" strokeDasharray={length} strokeDashoffset={length * (1 - p)} />
					</mask>
				</defs>
				<path d={d} stroke={color} strokeWidth={width} fill="none" strokeDasharray="10 10" mask={`url(#${id})`} />
			</g>
		);
	}
	return (
		<path
			d={d}
			stroke={color}
			strokeWidth={width}
			fill="none"
			strokeLinecap="butt"
			strokeDasharray={length}
			strokeDashoffset={length * (1 - p)}
			opacity={p === 0 ? 0 : opacity}
		/>
	);
};

type LineProps = Omit<PathProps, 'd'> & {x1: number; y1: number; x2: number; y2: number};

export const DrawLine: React.FC<LineProps> = ({x1, y1, x2, y2, ...rest}) => (
	<DrawPath d={`M ${x1} ${y1} L ${x2} ${y2}`} {...rest} />
);

/** Rectangle outline drawn clockwise from its top-left corner. */
export const DrawRect: React.FC<Omit<PathProps, 'd'> & {x: number; y: number; w: number; h: number}> = ({x, y, w, h, ...rest}) => (
	<DrawPath d={`M ${x} ${y} H ${x + w} V ${y + h} H ${x} Z`} {...rest} />
);

/** Full-frame SVG layer in video coordinates (1920×1080). */
export const Canvas: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
	<svg
		width={VIDEO.width}
		height={VIDEO.height}
		viewBox={`0 0 ${VIDEO.width} ${VIDEO.height}`}
		style={{position: 'absolute', inset: 0, overflow: 'visible', ...style}}
	>
		{children}
	</svg>
);

const hash = (s: string) => {
	let h = 0;
	for (let i = 0; i < s.length; i++) {
		h = (h * 31 + s.charCodeAt(i)) | 0;
	}
	return h;
};
