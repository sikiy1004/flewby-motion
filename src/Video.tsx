import {TransitionSeries} from '@remotion/transitions';
import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {SoundTrack, type AudioAvailability} from './components/Sound';
import {SubtitleTrack} from './components/Subtitle';
import {barWipe, sceneTiming} from './components/Transition';
import {FPS, SCENES, TOTAL_FRAMES, TRANSITION_FRAMES, type SceneId, type SceneMeta} from './data/scenes';
import {Scene00} from './scenes/Scene00';
import {Scene01} from './scenes/Scene01';
import {Scene02} from './scenes/Scene02';
import {Scene03} from './scenes/Scene03';
import {Scene04} from './scenes/Scene04';
import {Scene05} from './scenes/Scene05';
import {Scene06} from './scenes/Scene06';
import {Scene07} from './scenes/Scene07';
import {Scene08} from './scenes/Scene08';
import {COLORS, GRID, VIDEO} from './theme';

export type SceneProps = {meta: SceneMeta; showGrid: boolean};

export const SCENE_COMPONENTS: Record<SceneId, React.FC<SceneProps>> = {
	scene00: Scene00,
	scene01: Scene01,
	scene02: Scene02,
	scene03: Scene03,
	scene04: Scene04,
	scene05: Scene05,
	scene06: Scene06,
	scene07: Scene07,
	scene08: Scene08,
};

export type VideoProps = {
	showGrid: boolean;
	showSubtitles: boolean;
	audio: AudioAvailability;
};

/** Thin running progress rule along the bottom edge. */
const Progress: React.FC = () => {
	const frame = useCurrentFrame();
	const p = interpolate(frame, [0, TOTAL_FRAMES - 1], [0, 1], {extrapolateRight: 'clamp'});
	return (
		<div style={{position: 'absolute', left: GRID.marginX, right: GRID.marginX, top: 1036, height: 2, background: 'rgba(184,184,179,0.35)'}}>
			<div style={{width: `${p * 100}%`, height: '100%', background: COLORS.red}} />
		</div>
	);
};

export const Video: React.FC<VideoProps> = ({showGrid, showSubtitles, audio}) => (
	<AbsoluteFill style={{background: COLORS.offWhite, width: VIDEO.width, height: VIDEO.height}}>
		<TransitionSeries>
			{SCENES.map((meta, i) => {
				const Scene = SCENE_COMPONENTS[meta.id];
				const isLast = i === SCENES.length - 1;
				// Every scene but the last is padded by the transition length so that
				// each scene still begins exactly on its nominal second.
				const frames = Math.round(meta.durationSec * FPS) + (isLast ? 0 : TRANSITION_FRAMES);
				const next = SCENES[i + 1];
				return (
					<React.Fragment key={meta.id}>
						<TransitionSeries.Sequence durationInFrames={frames} name={`${meta.id} ${meta.title}`}>
							<Scene meta={meta} showGrid={showGrid} />
						</TransitionSeries.Sequence>
						{isLast ? null : (
							<TransitionSeries.Transition
								timing={sceneTiming}
								presentation={barWipe(next.tone === 'dark' || meta.tone === 'dark' ? COLORS.red : COLORS.black)}
							/>
						)}
					</React.Fragment>
				);
			})}
		</TransitionSeries>
		{showSubtitles ? <SubtitleTrack /> : null}
		<Progress />
		<SoundTrack audio={audio} />
	</AbsoluteFill>
);
