// CSV ⇄ JSON for products and posts (spreadsheet-friendly input).
//   node pipeline/csv.mjs import data/csv/products.csv   → data/products.json  (replaces; old file kept as .bak)
//   node pipeline/csv.mjs import data/csv/posts.csv      → data/posts/<id>.json (one file per row)
//   node pipeline/csv.mjs export                         → data/csv/products.csv + posts.csv from current JSON
// The file type is detected from its header. UTF-8 (with or without BOM). Line breaks inside a cell:
// a real newline (Alt+Enter in Excel) or the two characters \n.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateProducts, validatePost } from "./validate.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const MAX_SPECS = 6;

/* ---------- RFC 4180 parse / write ---------- */
export function parseCsv(text) {
  text = text.replace(/^﻿/, "");
  const rows = [];
  let row = [], cell = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (c === '"') q = false;
      else cell += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(cell); cell = ""; }
    else if (c === "\n" || c === "\r") {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell); rows.push(row); row = []; cell = "";
    } else cell += c;
  }
  if (cell !== "" || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows.filter((r) => r.some((c) => c.trim() !== ""));
  return body.map((r) => Object.fromEntries(head.map((h, i) => [h.trim(), (r[i] ?? "").trim()])));
}
const esc = (v) => (/[",\n\r]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
const writeCsv = (file, header, rows) =>
  fs.writeFileSync(file, "﻿" + [header, ...rows.map((r) => header.map((h) => r[h] ?? ""))].map((r) => r.map((v) => esc(String(v))).join(",")).join("\r\n") + "\r\n");

const nl = (s) => s.replace(/\\n/g, "\n");
const int = (s) => (s === "" ? undefined : parseInt(String(s).replace(/[¥,円\s]/g, ""), 10));
const clean = (o) => {
  for (const k of Object.keys(o)) {
    if (o[k] === undefined || o[k] === "" || (typeof o[k] === "object" && !Array.isArray(o[k]) && Object.keys(clean(o[k])).length === 0) || (Array.isArray(o[k]) && !o[k].length)) delete o[k];
  }
  return o;
};

/* ---------- columns ---------- */
const PRODUCT_COLS = ["id", "category", "categoryEn", "brand", "name", "nameJa", "price", "image", "displayHeight",
  ...Array.from({ length: MAX_SPECS }, (_, i) => [`spec${i + 1}_label`, `spec${i + 1}_value`]).flat(),
  "point1", "point2", "point3", "rakuten", "amazon"];
const POST_COLS = ["id", "collection", "issue", "priceDate", "word", "kicker", "lead", "aurora", "hero", "products",
  "compare_word", "compare_kicker", "compare_lead", "compare_rows", "summary_word",
  "reel_headline", "reel_sub", "reel_accent", "reel_kicker", "reel_seed", "reel_layout", "hashtags"];

function rowToProduct(r) {
  const specs = {};
  for (let i = 1; i <= MAX_SPECS; i++) if (r[`spec${i}_label`]) specs[r[`spec${i}_label`]] = r[`spec${i}_value`] ?? "";
  return clean({
    id: r.id, category: r.category, categoryEn: r.categoryEn, brand: r.brand, name: r.name, nameJa: r.nameJa,
    price: int(r.price), image: r.image || `assets/products/raw/${r.id}.jpg`, displayHeight: int(r.displayHeight ?? ""),
    specs, points: [r.point1, r.point2, r.point3].filter(Boolean), links: { rakuten: r.rakuten, amazon: r.amazon },
  });
}
function productToRow(p) {
  const r = { ...p, links: undefined, specs: undefined, points: undefined, rakuten: p.links?.rakuten, amazon: p.links?.amazon };
  Object.entries(p.specs ?? {}).forEach(([k, v], i) => { r[`spec${i + 1}_label`] = k; r[`spec${i + 1}_value`] = v; });
  (p.points ?? []).forEach((v, i) => (r[`point${i + 1}`] = v));
  return r;
}
// compare_rows: "価格=price|重さ=spec:重さ|推し=points.0"
const parseRows = (s) => s ? s.split("|").map((x) => { const [label, src] = x.split("="); return src?.startsWith("spec:") ? { label, spec: src.slice(5) } : { label, field: src }; }) : undefined;
const rowsToStr = (rows) => (rows ?? []).map((r) => `${r.label}=${r.spec ? "spec:" + r.spec : r.field}`).join("|");

function rowToPost(r) {
  return clean({
    id: r.id,
    collection: { number: int(r.collection) ?? 1, issue: int(r.issue) ?? 1 },
    priceDate: r.priceDate,
    cover: clean({ word: r.word, kicker: r.kicker, lead: nl(r.lead ?? ""), aurora: r.aurora || "dawn", hero: r.hero }),
    products: r.products.split(/[|\s]+/).filter(Boolean),
    compare: clean({ word: r.compare_word, kicker: r.compare_kicker, lead: nl(r.compare_lead ?? ""), rows: parseRows(r.compare_rows) }),
    summary: clean({ word: r.summary_word }),
    reel: r.reel_headline ? clean({ headline: nl(r.reel_headline), sub: r.reel_sub, accent: r.reel_accent, kicker: r.reel_kicker, seed: int(r.reel_seed ?? ""), layout: r.reel_layout }) : undefined,
    hashtags: r.hashtags ? r.hashtags.split(/\s+/).filter(Boolean) : undefined,
  });
}
function postToRow(p) {
  const n = (s) => (s ?? "").replace(/\n/g, "\\n");
  return {
    id: p.id, collection: p.collection.number, issue: p.collection.issue, priceDate: p.priceDate,
    word: p.cover.word, kicker: p.cover.kicker, lead: n(p.cover.lead), aurora: p.cover.aurora, hero: p.cover.hero, products: p.products.join("|"),
    compare_word: p.compare?.word, compare_kicker: p.compare?.kicker, compare_lead: n(p.compare?.lead), compare_rows: rowsToStr(p.compare?.rows),
    summary_word: p.summary?.word, reel_headline: n(p.reel?.headline), reel_sub: p.reel?.sub, reel_accent: p.reel?.accent,
    reel_kicker: p.reel?.kicker, reel_seed: p.reel?.seed, reel_layout: p.reel?.layout, hashtags: (p.hashtags ?? []).join(" "),
  };
}

/* ---------- commands ---------- */
const [cmd, file] = process.argv.slice(2);
if (cmd === "import") {
  const rows = parseCsv(fs.readFileSync(file, "utf8"));
  const head = Object.keys(rows[0] ?? {});
  if (head.includes("price")) {
    const list = rows.map(rowToProduct);
    validateProducts(list);
    const dst = path.join(ROOT, "data/products.json");
    if (fs.existsSync(dst)) fs.copyFileSync(dst, dst + ".bak");
    fs.writeFileSync(dst, JSON.stringify(list, null, 2) + "\n");
    console.log(`imported ${list.length} products → data/products.json (previous saved as .bak)`);
  } else if (head.includes("word")) {
    const products = Object.fromEntries(JSON.parse(fs.readFileSync(path.join(ROOT, "data/products.json"), "utf8")).map((p) => [p.id, p]));
    for (const r of rows) {
      const post = rowToPost(r);
      validatePost(post, products, `${file} row "${r.id}"`);
      fs.writeFileSync(path.join(ROOT, "data/posts", `${post.id}.json`), JSON.stringify(post, null, 2) + "\n");
      console.log(`imported post → data/posts/${post.id}.json`);
    }
  } else throw new Error("unknown CSV: header must contain 'price' (products) or 'word' (posts)");
} else if (cmd === "export") {
  const dir = path.join(ROOT, "data/csv");
  fs.mkdirSync(dir, { recursive: true });
  const products = JSON.parse(fs.readFileSync(path.join(ROOT, "data/products.json"), "utf8"));
  writeCsv(path.join(dir, "products.csv"), PRODUCT_COLS, products.map(productToRow));
  const posts = fs.readdirSync(path.join(ROOT, "data/posts")).filter((f) => f.endsWith(".json")).sort()
    .map((f) => JSON.parse(fs.readFileSync(path.join(ROOT, "data/posts", f), "utf8")));
  writeCsv(path.join(dir, "posts.csv"), POST_COLS, posts.map(postToRow));
  console.log(`exported → data/csv/products.csv (${products.length}), data/csv/posts.csv (${posts.length})`);
} else {
  console.log("usage: node pipeline/csv.mjs import <file.csv> | export");
  process.exit(1);
}
