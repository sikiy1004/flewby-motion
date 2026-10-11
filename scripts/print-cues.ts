// Prints resolved subtitle cue timings (scene-relative and global) — handy when
// re-timing animations or recording narration.  Usage: node scripts/print-cues.ts
import {NARRATION, timedCues} from '../src/data/narration.ts';
import {SCENES} from '../src/data/scenes.ts';

const fmt = (s: number) => s.toFixed(2).padStart(6);
let offset = 0;
for (const scene of SCENES) {
	const n = NARRATION.find((x) => x.sceneId === scene.id);
	console.log(`\n${scene.id}  ${scene.title}  (${offset}s – ${offset + scene.durationSec}s)`);
	if (n) {
		for (const c of timedCues(n)) {
			console.log(`  ${fmt(c.from)} → ${fmt(c.to)}   [global ${fmt(offset + c.from)}]  ${c.text}`);
		}
	}
	offset += scene.durationSec;
}
