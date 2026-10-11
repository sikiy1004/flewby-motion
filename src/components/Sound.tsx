import React from 'react';
import {Audio, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import {NARRATION} from '../data/narration';
import {SCENES, TOTAL_FRAMES, sceneStartFrame} from '../data/scenes';
import {AUDIO_FILES, MIX, SFX_CUES, type SfxType} from '../data/sound';

export type AudioAvailability = {
	narration: boolean;
	bgm: boolean;
	sfx: Record<SfxType, boolean>;
};

export const NO_AUDIO: AudioAvailability = {
	narration: false,
	bgm: false,
	sfx: {click: false, line: false, impact: false, slide: false},
};

/** Probe public/ for each audio slot so missing files never break preview or render. */
export const detectAudio = async (): Promise<AudioAvailability> => {
	const exists = async (path: string) => {
		try {
			const res = await fetch(staticFile(path), {method: 'HEAD'});
			const type = res.headers.get('content-type') ?? '';
			return res.ok && !type.includes('text/html');
		} catch {
			return false;
		}
	};
	const sfxKeys = Object.keys(AUDIO_FILES.sfx) as SfxType[];
	const [narration, bgm, ...sfx] = await Promise.all([
		exists(AUDIO_FILES.narration),
		exists(AUDIO_FILES.bgm),
		...sfxKeys.map((k) => exists(AUDIO_FILES.sfx[k])),
	]);
	return {
		narration,
		bgm,
		sfx: Object.fromEntries(sfxKeys.map((k, i) => [k, sfx[i]])) as Record<SfxType, boolean>,
	};
};

/** Narration windows in global frames, used for subtitle sync and BGM ducking. */
const narrationWindows = (fps: number) =>
	NARRATION.map((n) => {
		const sceneStart = sceneStartFrame(n.sceneId);
		const from = sceneStart + Math.round(n.start * fps);
		const to = sceneStart + Math.round(n.end * fps);
		const fileFrom = Math.round((n.fileOffsetSec ?? sceneStart / fps + n.start) * fps);
		return {sceneId: n.sceneId, from, to, fileFrom};
	});

export const SoundTrack: React.FC<{audio: AudioAvailability}> = ({audio}) => {
	const {fps} = useVideoConfig();
	const windows = narrationWindows(fps);

	return (
		<>
			{audio.narration
				? windows.map((w) => (
						<Sequence key={w.sceneId} from={w.from} durationInFrames={w.to - w.from + fps} name={`narration ${w.sceneId}`} layout="none">
							<Audio
								src={staticFile(AUDIO_FILES.narration)}
								trimBefore={w.fileFrom}
								trimAfter={w.fileFrom + (w.to - w.from) + fps}
								volume={MIX.narration}
							/>
						</Sequence>
					))
				: null}

			{audio.bgm ? (
				<Audio
					src={staticFile(AUDIO_FILES.bgm)}
					loop
					volume={(f) => {
						const ducked = windows.some((w) => f >= w.from - 6 && f <= w.to + 6);
						const base = audio.narration && ducked ? MIX.bgmDucked : MIX.bgm;
						const fade = MIX.fadeSec * fps;
						return base * interpolate(f, [0, fade, TOTAL_FRAMES - fade, TOTAL_FRAMES], [0, 1, 1, 0], {extrapolateRight: 'clamp'});
					}}
				/>
			) : null}

			{SCENES.flatMap((s) =>
				SFX_CUES[s.id]
					.filter((cue) => audio.sfx[cue.type])
					.map((cue, i) => (
						<Sequence
							key={`${s.id}-${i}`}
							from={sceneStartFrame(s.id) + Math.round(cue.at * fps)}
							durationInFrames={fps * 3}
							name={`sfx ${cue.type}`}
							layout="none"
						>
							<Audio src={staticFile(AUDIO_FILES.sfx[cue.type])} volume={MIX.sfx[cue.type]} />
						</Sequence>
					)),
			)}
		</>
	);
};
