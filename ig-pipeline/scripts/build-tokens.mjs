// tokens/tokens.json → tokens/build/{tokens.css, tokens.ts, tokens.ase, ffmpeg.json}
// tokens.json is the single source of truth. Never edit files in tokens/build by hand.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const T = JSON.parse(fs.readFileSync(path.join(root, "tokens/tokens.json"), "utf8"));
const outDir = path.join(root, "tokens/build");
fs.mkdirSync(outDir, { recursive: true });

const kebab = (s) => s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase();
const fontDir = "../../assets/fonts/fallback"; // relative to tokens/build/tokens.css

/* ---------- CSS ---------- */
let css = "/* AUTO-GENERATED from tokens/tokens.json — do not edit. Run `npm run tokens`. */\n\n";

// @font-face for bundled OFL fallbacks
for (const fam of Object.values(T.font.family)) {
  for (const [key, file] of Object.entries(fam.fallbackFiles)) {
    const italic = key.endsWith("i");
    const weight = parseInt(key, 10);
    css += `@font-face{font-family:"${fam.fallback}";src:url("${fontDir}/${file}") format("truetype");font-weight:${weight};font-style:${italic ? "italic" : "normal"};font-display:block}\n`;
  }
}

const generic = { serifDisplay: "serif", mincho: "serif", gothicHeavy: "sans-serif", label: "sans-serif" };
const stack = (list) => list.map((f) => `"${f}"`).join(", ");

css += "\n:root{\n";
for (const [group, colors] of Object.entries(T.color))
  for (const [name, hex] of Object.entries(colors)) css += `  --c-${group}-${kebab(name)}: ${hex};\n`;
for (const [k, v] of Object.entries(T.space)) css += `  --sp-${k}: ${v}px;\n`;
css += `  --margin-x: ${T.layout.margin.x}px;\n  --margin-top: ${T.layout.margin.top}px;\n  --margin-bottom: ${T.layout.margin.bottom}px;\n`;
css += `  --rule-weight: ${T.layout.rule.weight}px;\n  --rule-length: ${T.layout.rule.length}px;\n`;
css += `  --dot-size: ${T.layout.dots.size}px;\n  --dot-gap: ${T.layout.dots.gap}px;\n  --product-max-h: ${T.layout.productMaxHeight}px;\n`;
for (const [name, fam] of Object.entries(T.font.family))
  css += `  --font-${kebab(name)}: ${stack([...fam.adobe, fam.fallback])}, ${generic[name]};\n`;
for (const [name, t] of Object.entries(T.type)) {
  const n = kebab(name);
  css += `  --fs-${n}: ${t.size}px;\n  --lh-${n}: ${t.lineHeight};\n  --tr-${n}: ${t.tracking};\n  --fw-${n}: ${t.weight};\n`;
}
css += "}\n\n";

// Fallback mode: ignore Adobe Fonts entirely (used in CI / cloud, or to compare)
css += 'html[data-font-mode="fallback"]{\n';
for (const [name, fam] of Object.entries(T.font.family))
  css += `  --font-${kebab(name)}: "${fam.fallback}", ${generic[name]};\n`;
css += "}\n\n";

// Type role classes: .t-display-word etc.
for (const [name, t] of Object.entries(T.type)) {
  const n = kebab(name);
  css += `.t-${n}{font-family:var(--font-${kebab(t.family)});font-size:var(--fs-${n});line-height:var(--lh-${n});letter-spacing:var(--tr-${n});font-weight:var(--fw-${n});${t.case === "upper" ? "text-transform:uppercase;" : ""}}\n`;
}
// Pigment helpers for dots etc.
for (const name of Object.keys(T.color.pigment)) css += `.bg-${kebab(name)}{background:var(--c-pigment-${kebab(name)})}\n`;
fs.writeFileSync(path.join(outDir, "tokens.css"), css);

/* ---------- TS (for Remotion / Node / phase-2 video) ---------- */
fs.writeFileSync(
  path.join(outDir, "tokens.ts"),
  `// AUTO-GENERATED from tokens/tokens.json — do not edit.\nexport const tokens = ${JSON.stringify(T, null, 2)} as const;\nexport type Tokens = typeof tokens;\n`
);

/* ---------- JS global (for preview boards opened from file://) ---------- */
fs.writeFileSync(path.join(outDir, "tokens.js"), `// AUTO-GENERATED\nwindow.TOKENS = ${JSON.stringify(T)};\n`);

/* ---------- ASE (Adobe Swatch Exchange: Photoshop / Illustrator / Premiere) ---------- */
function aseBuild(groups) {
  const chunks = [];
  const u16 = (n) => { const b = Buffer.alloc(2); b.writeUInt16BE(n); return b; };
  const u32 = (n) => { const b = Buffer.alloc(4); b.writeUInt32BE(n); return b; };
  const f32 = (n) => { const b = Buffer.alloc(4); b.writeFloatBE(n); return b; };
  const name = (s) => { const str = Buffer.from(s + "\0", "utf16le").swap16(); return Buffer.concat([u16(s.length + 1), str]); };
  let count = 0;
  for (const [g, colors] of Object.entries(groups)) {
    const gn = name(g);
    chunks.push(u16(0xc001), u32(gn.length), gn); count++;
    for (const [cn, hex] of Object.entries(colors)) {
      const [r, gg, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255);
      const body = Buffer.concat([name(`${g}/${cn}`), Buffer.from("RGB "), f32(r), f32(gg), f32(b), u16(2)]);
      chunks.push(u16(0x0001), u32(body.length), body); count++;
    }
    chunks.push(u16(0xc002), u32(0)); count++;
  }
  return Buffer.concat([Buffer.from("ASEF"), u16(1), u16(0), u32(count), ...chunks]);
}
fs.writeFileSync(path.join(outDir, "tokens.ase"), aseBuild(T.color));

/* ---------- ffmpeg (phase 2: drawtext / color sources) ---------- */
const ff = { colors: {}, fonts: {} };
for (const [g, colors] of Object.entries(T.color))
  for (const [n, hex] of Object.entries(colors)) ff.colors[`${g}.${n}`] = "0x" + hex.slice(1).toUpperCase();
for (const [n, fam] of Object.entries(T.font.family))
  ff.fonts[n] = Object.fromEntries(Object.entries(fam.fallbackFiles).map(([w, f]) => [w, `assets/fonts/fallback/${f}`]));
ff.canvas = T.canvas; ff.motion = T.motion;
fs.writeFileSync(path.join(outDir, "ffmpeg.json"), JSON.stringify(ff, null, 2));

console.log("tokens built →", path.relative(root, outDir));
