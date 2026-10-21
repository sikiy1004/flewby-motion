import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {ASSET_PATHS, HOOK, TIMING, TOTAL_FRAMES, type AssetAvailability} from './config';
import {Plate} from './Plate';

export type HookProps = {
	assets: AssetAvailability;
	/** Draw the tracked screen corners over the footage (for aligning SCREEN_TRACK). */
	showTrackingGuide: boolean;
	/** Light tap sound at the moment of the tap. */
	tapSound: boolean;
};

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** Subtle animated film grain + vignette. Fades out during the hand-off so the last frame is the ad's first frame. */
const Grade: React.FC = () => {
	const frame = useCurrentFrame();
	const amount = interpolate(frame, [TIMING.handoffFrom, TIMING.handoffTo], [1, 0], clamp);
	if (amount <= 0) return null;
	return (
		<AbsoluteFill style={{pointerEvents: 'none', opacity: amount}}>
			<AbsoluteFill style={{background: 'radial-gradient(ellipse 85% 70% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.42) 100%)'}} />
			<svg width={HOOK.width} height={HOOK.height} style={{position: 'absolute', inset: 0, mixBlendMode: 'overlay', opacity: 0.22}}>
				<filter id="grain">
					<feTurbulence type="fractalNoise" baseFrequency={0.9} numOctaves={2} seed={frame % 24} stitchTiles="stitch" />
					<feColorMatrix type="saturate" values="0" />
				</filter>
				<rect width="100%" height="100%" filter="url(#grain)" />
			</svg>
		</AbsoluteFill>
	);
};

/** Final frames: the main ad's first frame, full-frame, exactly as the main ad opens. */
const Handoff: React.FC<{assets: AssetAvailability}> = ({assets}) => {
	const frame = useCurrentFrame();
	const opacity = interpolate(frame, [TIMING.handoffFrom, TIMING.handoffTo], [0, 1], clamp);
	if (opacity <= 0 || !assets.mainAdFirstFrame) return null;
	return (
		<AbsoluteFill style={{opacity}}>
			<Img src={staticFile(ASSET_PATHS.mainAdFirstFrame)} style={{width: HOOK.width, height: HOOK.height, objectFit: 'cover'}} />
		</AbsoluteFill>
	);
};

export const FlewbyHook: React.FC<HookProps> = ({assets, showTrackingGuide, tapSound}) => (
	<AbsoluteFill style={{background: '#000'}}>
		<Sequence durationInFrames={TIMING.matchCut} name="CUT01–02 wide">
			<Plate kind="wide" offset={0} assets={assets} showTrackingGuide={showTrackingGuide} />
		</Sequence>
		<Sequence from={TIMING.matchCut} durationInFrames={TOTAL_FRAMES - TIMING.matchCut} name="CUT02–04 close-up">
			<Plate kind="closeup" offset={TIMING.matchCut} assets={assets} showTrackingGuide={showTrackingGuide} />
		</Sequence>
		<Grade />
		<Handoff assets={assets} />
		{tapSound ? (
			<Sequence from={TIMING.tap} durationInFrames={10} name="tap sfx">
				<Audio src={staticFile('audio/sfx/click.wav')} volume={0.35} />
			</Sequence>
		) : null}
	</AbsoluteFill>
);
