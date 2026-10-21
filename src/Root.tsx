import React from 'react';
import {Composition, Folder} from 'remotion';
import {NO_AUDIO, detectAudio} from './components/Sound';
import {FPS, SCENES, TOTAL_FRAMES, TRANSITION_FRAMES} from './data/scenes';
import {loadFonts} from './fonts';
import {VIDEO} from './theme';
import {SCENE_COMPONENTS, Video, type VideoProps} from './Video';
import {HOOK, NO_ASSETS, TOTAL_FRAMES as HOOK_FRAMES} from './hook/config';
import {FlewbyHook, type HookProps} from './hook/FlewbyHook';
import {detectHookAssets} from './hook/geometry';

loadFonts();

const defaultProps: VideoProps = {showGrid: false, showSubtitles: true, audio: NO_AUDIO};
const hookProps: HookProps = {assets: NO_ASSETS, showTrackingGuide: false, tapSound: true};

export const RemotionRoot: React.FC = () => (
	<>
		<Composition
			id="FlewbyHook"
			component={FlewbyHook}
			durationInFrames={HOOK_FRAMES}
			fps={HOOK.fps}
			width={HOOK.width}
			height={HOOK.height}
			defaultProps={hookProps}
			calculateMetadata={async ({props}) => ({props: {...props, assets: await detectHookAssets()}})}
		/>
		<Composition
			id="InterviewMemo"
			component={Video}
			durationInFrames={TOTAL_FRAMES}
			fps={FPS}
			width={VIDEO.width}
			height={VIDEO.height}
			defaultProps={defaultProps}
			calculateMetadata={async ({props}) => ({props: {...props, audio: await detectAudio()}})}
		/>
		<Folder name="Scenes">
			{SCENES.map((meta) => (
				<Composition
					key={meta.id}
					id={meta.id}
					component={SCENE_COMPONENTS[meta.id]}
					durationInFrames={Math.round(meta.durationSec * FPS) + TRANSITION_FRAMES}
					fps={FPS}
					width={VIDEO.width}
					height={VIDEO.height}
					defaultProps={{meta, showGrid: false}}
				/>
			))}
		</Folder>
	</>
);
