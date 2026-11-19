// Live preview while editing templates / tokens / data: rebuilds on save.
//   npm run preview -- data/posts/post-01-morning.json [--only cover]
// Output PNGs land in out/<post>/ (keep them open in Finder's Quick Look / Preview, they refresh).
// The rendered HTML is in .cache/html/<post>/ — open it in Chrome to inspect with DevTools.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const args = process.argv.slice(2);
const postFile = args.find((a) => a.endsWith(".json"));
if (!postFile) { console.log("usage: npm run preview -- data/posts/<post>.json [--only cover]"); process.exit(1); }
const passthru = args.filter((a) => a !== postFile);

let timer = null, tokensDirty = false;
function rebuild() {
  try {
    if (tokensDirty) { execFileSync("node", ["scripts/build-tokens.mjs"], { cwd: ROOT, stdio: "inherit" }); tokensDirty = false; }
    execFileSync("node", ["pipeline/build.mjs", postFile, ...passthru], { cwd: ROOT, stdio: "inherit" });
    console.log(`✓ ${new Date().toLocaleTimeString()} — watching for changes (Ctrl+C to stop)`);
  } catch { console.log("✗ build failed — fix and save again"); }
}
const schedule = () => { clearTimeout(timer); timer = setTimeout(rebuild, 250); };
for (const dir of ["templates", "data", "tokens", "captions", "assets/aurora", "assets/paint", "assets/products"]) {
  fs.watch(path.join(ROOT, dir), { recursive: true }, (_e, f) => {
    if (!f || f.includes("build/")) return;
    if (dir === "tokens") tokensDirty = true;
    schedule();
  });
}
rebuild();
