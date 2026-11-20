// Put a checked draft into the engine's input (data/), then render it yourself with npm run build.
//   npm run research:install -- <run|latest> <idea-id> [--allow-placeholder] [--update]
// Re-runs every draft check; refuses on any error. Existing products with the same id are only replaced
// with --update.
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { ROOT, readJson, writeJson, parseArgs } from "./lib.mjs";
import { resolveRun } from "./ideas.mjs";
import { buildDraft, writeDraft } from "./draft.mjs";

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const a = parseArgs(process.argv.slice(2));
  const [r, ideaId] = a._;
  const runId = resolveRun(r);
  if (!runId || !ideaId) { console.log("usage: npm run research:install -- <run|latest> <idea-id> [--allow-placeholder] [--update]"); process.exit(1); }
  const d = buildDraft(runId, ideaId, { allowPlaceholder: !!a["allow-placeholder"] });
  if (!d.stoppedBeforeGeneration) writeDraft(runId, d);
  if (d.errors.length) { d.errors.forEach((e) => console.log("✗ " + e)); console.log("取り込みを中止しました"); process.exit(1); }
  const list = readJson("data/products.json");
  for (const p of d.products) {
    const i = list.findIndex((x) => x.id === p.id);
    if (i < 0) list.push(p);
    else if (JSON.stringify(list[i]) === JSON.stringify(p)) continue;
    else if (a.update) list[i] = p;
    else { console.log(`✗ data/products.json に同じ id「${p.id}」の別内容があります（置き換えるなら --update）`); process.exit(1); }
  }
  writeJson("data/products.json", list);
  writeJson(`data/posts/${d.postId}.json`, d.post);
  d.warnings.forEach((w) => console.log("△ " + w));
  console.log(`✓ data/products.json と data/posts/${d.postId}.json に取り込みました`);
  for (const p of d.products) if (!fs.existsSync(path.join(ROOT, p.image))) console.log(`△ 画像がまだありません：${p.image}`);
  console.log(`次に描画：npm run cutout && npm run build -- data/posts/${d.postId}.json`);
}
