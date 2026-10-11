import {continueRender, delayRender, staticFile} from 'remotion';

// Fonts are bundled locally in public/fonts (SIL Open Font License 1.1, see OFL-*.txt).
const FACES = [
	{family: 'Noto Sans JP', weight: '400', file: 'NotoSansJP_400Regular.ttf'},
	{family: 'Noto Sans JP', weight: '500', file: 'NotoSansJP_500Medium.ttf'},
	{family: 'Noto Sans JP', weight: '700', file: 'NotoSansJP_700Bold.ttf'},
	{family: 'Noto Sans JP', weight: '800', file: 'NotoSansJP_800ExtraBold.ttf'},
	{family: 'Inter', weight: '400', file: 'Inter_400Regular.ttf'},
	{family: 'Inter', weight: '500', file: 'Inter_500Medium.ttf'},
	{family: 'Inter', weight: '700', file: 'Inter_700Bold.ttf'},
	{family: 'Inter', weight: '800', file: 'Inter_800ExtraBold.ttf'},
];

let started = false;

export const loadFonts = () => {
	if (started || typeof window === 'undefined') {
		return;
	}
	started = true;
	const handle = delayRender('Loading local fonts');
	Promise.all(
		FACES.map(async ({family, weight, file}) => {
			const face = new FontFace(family, `url(${staticFile(`fonts/${file}`)}) format('truetype')`, {
				weight,
				style: 'normal',
			});
			await face.load();
			document.fonts.add(face);
		}),
	)
		.then(() => continueRender(handle))
		.catch((err) => {
			console.error('Font loading failed', err);
			continueRender(handle);
		});
};
