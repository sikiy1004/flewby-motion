import {linearTiming, type TransitionPresentation, type TransitionPresentationComponentProps} from '@remotion/transitions';
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {TRANSITION_FRAMES} from '../data/scenes';
import {COLORS, EASE} from '../theme';

type BarWipeProps = {edgeColor: string};

/**
 * Straight left-to-right wipe. The incoming page is revealed behind a thin edge bar
 * while the outgoing page slides a short distance to the left.
 */
const BarWipe: React.FC<TransitionPresentationComponentProps<BarWipeProps>> = ({
	children,
	presentationDirection,
	presentationProgress,
	passedProps,
}) => {
	const p = presentationProgress;
	if (presentationDirection === 'exiting') {
		return <AbsoluteFill style={{transform: `translateX(${-120 * p}px)`}}>{children}</AbsoluteFill>;
	}
	return (
		<AbsoluteFill>
			<AbsoluteFill style={{clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`}}>{children}</AbsoluteFill>
			{p > 0 && p < 1 ? (
				<div
					style={{
						position: 'absolute',
						top: 0,
						bottom: 0,
						left: `${p * 100}%`,
						width: 10,
						transform: 'translateX(-100%)',
						background: passedProps.edgeColor,
					}}
				/>
			) : null}
		</AbsoluteFill>
	);
};

export const barWipe = (edgeColor: string = COLORS.black): TransitionPresentation<BarWipeProps> => ({
	component: BarWipe,
	props: {edgeColor},
});

export const sceneTiming = linearTiming({durationInFrames: TRANSITION_FRAMES, easing: EASE.inOut});
