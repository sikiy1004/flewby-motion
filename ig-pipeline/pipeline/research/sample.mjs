// Try the whole research flow on TEST DATA (fake products) — for learning the steps, not for posting.
//   npm run research:sample            copy research/examples/sample-run into a new run, with every time
//                                      shifted so that "now" matches the sample (prices fresh, sales not over),
//                                      put layout-only images in place, and render ideas.md
//   npm run research:sample -- --clean remove sample runs, test products/posts/images from data/ and assets/
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { ROOT, readJson, writeJson, newRunId, runDir, jstIso, parseArgs } from "./lib.mjs";

const SRC = path.join(ROOT, "research/examples/sample-run");
const IMAGES = { "test-ems-device": "facial-ems", "test-light-dryer": "hair-dryer", "test-scalp-dryer": "hair-dryer", "test-sonic-brush": "face-brush" };
const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?\+09:00$/;
const DAY = /^\d{4}-\d{2}-\d{2}$/;

function shift(v, ms) {
  if (Array.isArray(v)) return v.map((x) => shift(x, ms));
  if (v && typeof v === "object") return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, shift(x, ms)]));
  if (typeof v === "string" && ISO.test(v)) return jstIso(new Date(new Date(v).getTime() + ms)).replace(/:\d{2}\+09:00$/, (m) => (v.length === 25 ? m : "+09:00"));
  if (typeof v === "string" && DAY.test(v)) return jstIso(new Date(new Date(`${v}T12:00:00+09:00`).getTime() + ms)).slice(0, 10);
  return v;
}

function create() {
  const ideas = readJson(path.join(SRC, "ideas.json"));
  // align the newest recorded time (createdAt / fetchedAt) with "now", rounded down to the minute
  const times = [];
  const collect = (v, k) => { if (Array.isArray(v)) v.forEach((x) => collect(x)); else if (v && typeof v === "object") Object.entries(v).forEach(([kk, x]) => collect(x, kk)); else if ((k === "fetchedAt" || k === "createdAt") && ISO.test(v)) times.push(new Date(v).getTime()); };
  collect(ideas);
  for (const dir of ["evidence", "market"]) for (const f of fs.readdirSync(path.join(SRC, dir))) collect(readJson(path.join(SRC, dir, f)));
  const ms = Math.floor((Date.now() - Math.max(...times)) / 60e3) * 60e3;
  const runId = `${newRunId()}-sample`;
  const dst = runDir(runId);
  fs.mkdirSync(path.join(dst, "evidence"), { recursive: true });
  fs.mkdirSync(path.join(dst, "market"), { recursive: true });
  for (const f of fs.readdirSync(path.join(SRC, "market"))) writeJson(path.join(dst, "market", f), shift(readJson(path.join(SRC, "market", f)), ms));
  for (const f of fs.readdirSync(path.join(SRC, "evidence"))) writeJson(path.join(dst, "evidence", f), { ...shift(readJson(path.join(SRC, "evidence", f)), ms), runId });
  writeJson(path.join(dst, "ideas.json"), { ...shift(ideas, ms), runId });
  fs.copyFileSync(path.join(SRC, "market.md"), path.join(dst, "market.md"));
  for (const [id, from] of Object.entries(IMAGES)) {
    const to = path.join(ROOT, `assets/products/raw/${id}.jpg`);
    if (!fs.existsSync(to)) fs.copyFileSync(path.join(ROOT, `assets/products/raw/${from}.jpg`), to);
  }
  return runId;
}

function clean() {
  const removed = [];
  const runs = path.join(ROOT, "research/runs");
  for (const d of fs.readdirSync(runs)) if (d.endsWith("-sample")) { fs.rmSync(path.join(runs, d), { recursive: true }); removed.push(`research/runs/${d}`); }
  for (const dir of ["assets/products/raw", "assets/products/cutout"])
    for (const f of fs.readdirSync(path.join(ROOT, dir))) if (f.startsWith("test-")) { fs.rmSync(path.join(ROOT, dir, f)); removed.push(`${dir}/${f}`); }
  const prods = readJson("data/products.json");
  const keep = prods.filter((p) => !p.id.startsWith("test-"));
  if (keep.length !== prods.length) { writeJson("data/products.json", keep); removed.push(`data/products.json（test- の商品 ${prods.length - keep.length} 件）`); }
  for (const f of fs.readdirSync(path.join(ROOT, "data/posts"))) {
    const p = readJson(path.join(ROOT, "data/posts", f));
    if (p.products.some((id) => id.startsWith("test-"))) { fs.rmSync(path.join(ROOT, "data/posts", f)); removed.push(`data/posts/${f}`); fs.rmSync(path.join(ROOT, "out", p.id), { recursive: true, force: true }); }
  }
  console.log(removed.length ? "削除しました：\n  " + removed.join("\n  ") : "片付けるものはありません");
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const a = parseArgs(process.argv.slice(2));
  if (a.clean) clean();
  else {
    const runId = create();
    const { checkIdeas, renderIdeas, loadIdeas } = await import("./ideas.mjs");
    const doc = loadIdeas(runId);
    const c = checkIdeas(doc, runId);
    if (c.errors.length) { c.errors.forEach((e) => console.log("✗ " + e)); process.exit(1); }
    fs.writeFileSync(path.join(runDir(runId), "ideas.md"), renderIdeas(doc, runId, c));
    console.log(`✓ 見本の実行を作りました：research/runs/${runId}/（テスト用データ・公開不可）`);
    console.log(`  投稿案リスト：research/runs/${runId}/ideas.md`);
    console.log(`  次に承認（あなたが実行）：npm run research:approve -- latest I01 I02`);
  }
}
