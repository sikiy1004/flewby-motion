// Copy checks (research/compliance.json): efficacy claims (薬機法), misleading claims (景表法), and
// first-person usage/review wording (this account does not review products it has not used).
//   npm run research:lint                         every data/posts/*.json (texts + products + caption)
//   npm run research:lint -- data/posts/x.json
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { ROOT, readJson } from "./lib.mjs";
import { renderCaption } from "./caption.mjs";

export const rules = () => readJson("research/compliance.json").rules.map((r) => ({ ...r, re: new RegExp(r.pattern) }));

/** texts: [[where, text], …] → findings [{level, id, where, match, reason, suggest}] */
export function lintTexts(texts) {
  const R = rules(), out = [];
  for (const [where, text] of texts) {
    if (!text) continue;
    for (const r of R) {
      const m = String(text).match(r.re);
      if (m) out.push({ level: r.level, id: r.id, where, match: m[0], reason: r.reason, suggest: r.suggest });
    }
  }
  return out;
}

/** Every human-readable text of a post, its products, and its rendered caption. */
export function postTexts(post, items, caption) {
  const t = [
    ["cover.kicker", post.cover?.kicker], ["cover.lead", post.cover?.lead], ["compare.kicker", post.compare?.kicker], ["compare.lead", post.compare?.lead],
    ["reel.headline", post.reel?.headline], ["reel.sub", post.reel?.sub], ["reel.accent", post.reel?.accent],
  ];
  for (const p of items) {
    t.push([`${p.id}.name`, p.name], [`${p.id}.nameJa`, p.nameJa]);
    (p.points ?? []).forEach((x, i) => t.push([`${p.id}.points[${i}]`, x]));
    Object.entries(p.specs ?? {}).forEach(([k, v]) => t.push([`${p.id}.specs.${k}`, `${k}：${v}`]));
  }
  if (caption) t.push(["caption", caption]);
  return t;
}

export const formatFindings = (fs_) => fs_.map((f) => `${f.level === "error" ? "✗" : "△"} ${f.where}：「${f.match}」${f.reason}\n    → ${f.suggest}`).join("\n");

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const files = process.argv.slice(2).filter((a) => a.endsWith(".json"));
  const list = files.length ? files : fs.readdirSync(path.join(ROOT, "data/posts")).filter((f) => f.endsWith(".json")).map((f) => `data/posts/${f}`);
  const products = Object.fromEntries(readJson("data/products.json").map((p) => [p.id, p]));
  let errors = 0;
  for (const f of list) {
    const post = readJson(f);
    const items = post.products.map((id) => products[id]).filter(Boolean);
    const res = lintTexts(postTexts(post, items, renderCaption(post, items)));
    console.log(`${path.basename(f)}: ${res.length ? "" : "OK"}`);
    if (res.length) console.log(formatFindings(res));
    errors += res.filter((r) => r.level === "error").length;
  }
  process.exit(errors ? 1 : 0);
}
