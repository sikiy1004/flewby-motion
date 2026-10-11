import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {narrationFor, timedCues} from '../data/narration';
import {SCENES, sceneStartFrame} from '../data/scenes';
import {COLORS, FONTS, GRID, VIDEO, toneColors} from '../theme';

const FADE = 5;

/** Global subtitle layer, synchronised with the narration cue data. */
export const SubtitleTrack: React.FC = () => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	for (const scene of SCENES) {
		const n = narrationFor(scene.id);
		if (!n) {
			continue;
		}
		const start = sceneStartFrame(scene.id);
		for (const cue of timedCues(n)) {
			const from = start + Math.round(cue.from * fps);
			const to = start + Math.round(cue.to * fps);
			if (frame >= from && frame < to) {
				const opacity = interpolate(frame, [from, from + FADE, to - FADE, to], [0, 1, 1, 0], {
					extrapolateLeft: 'clamp',
					extrapolateRight: 'clamp',
				});
				const shifted = scene.toneShift && frame >= start + Math.round(scene.toneShift.at * fps);
				const tone = shifted && scene.toneShift ? scene.toneShift.tone : scene.tone;
				return <SubtitleLine text={cue.text} tone={tone} opacity={opacity} />;
			}
		}
	}
	return null;
};

const SubtitleLine: React.FC<{text: string; tone: 'light' | 'dark'; opacity: number}> = ({text, tone, opacity}) => {
	const c = toneColors(tone);
	return (
		<AbsoluteFill style={{pointerEvents: 'none'}}>
			<div
				style={{
					position: 'absolute',
					left: GRID.marginX,
					top: GRID.subtitleY,
					maxWidth: VIDEO.width - GRID.marginX * 2,
					display: 'flex',
					alignItems: 'center',
					gap: 24,
					opacity,
				}}
			>
				<div style={{width: 6, height: 40, background: COLORS.red, flexShrink: 0}} />
				<div
					style={{
						fontFamily: FONTS.jp,
						fontWeight: 500,
						fontSize: 38,
						lineHeight: 1.4,
						letterSpacing: '0.04em',
						color: c.fg,
					}}
				>
					{text}
				</div>
			</div>
		</AbsoluteFill>
	);
};
