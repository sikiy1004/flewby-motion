// Build post images:  node pipeline/build.mjs data/posts/<post>.json [--only cover,compare] [--fonts]
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import nunjucks from "nunjucks";
import { withBrowser, shoot } from "./shot.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const T = JSON.parse(fs.readFileSync(path.join(ROOT, "tokens/tokens.json"), "utf8"));

const env = nunjucks.configure(path.join(ROOT, "templates"), { autoescape: true, throwOnUndefined: false });
env.addFilter("pad2", (n) => (typeof n === "number" ? String(n).padStart(2, "0") : n));
env.addFilter("yen", (n) => "¥" + Number(n).toLocaleString("ja-JP"));
env.addFilter("kebab", (s) => s.replace(/([a-z0-9])([A-Z])/g, "$1-$2").toLowerCase());
env.addFilter("nl2br", (s) => new nunjucks.runtime.SafeString(nunjucks.lib.escape(String(s ?? "")).replace(/\n/g, "<br>")));

// captions are plain text: separate environment without HTML escaping
const capEnv = new nunjucks.Environment(new nunjucks.FileSystemLoader(path.join(ROOT, "captions")), { autoescape: false, trimBlocks: true, lstripBlocks: true });
for (const f of ["pad2", "yen"]) capEnv.addFilter(f, env.getFilter(f));

function loadProducts() {
  const list = JSON.parse(fs.readFileSync(path.join(ROOT, "data/products.json"), "utf8"));
  return Object.fromEntries(
    list.map((p) => {
      const cutout = `assets/products/cutout/${p.id}.png`;
      if (!fs.existsSync(path.join(ROOT, cutout))) throw new Error(`cut-out missing for ${p.id}: run npm run cutout`);
      return [p.id, { ...p, cutout, displayHeight: p.displayHeight ?? T.layout.productMaxHeight }];
    })
  );
}

/** Which slides a post gets. Multi-product: cover → details → compare → summary. */
function slidesFor(post, items) {
  const s = [{ key: "cover", tpl: "a-cover.njk", canvas: "carousel" }];
  items.forEach((item, i) =>
    s.push({ key: `detail-${item.id}`, group: "detail", tpl: "a-detail.njk", canvas: "carousel", ctx: { item, itemNo: i + 1, mirror: i % 2 === 0 } })
  );
  if (items.length >= 2) {
    if (items.length > 4) throw new Error("compare page supports 2–4 products");
    s.push({ key: "compare", tpl: "a-compare.njk", canvas: "carousel" });
  }
  s.push({ key: "summary", tpl: "a-summary.njk", canvas: "carousel" });
  return s;
}

const get = (obj, dotted) => dotted.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);
const yen = (n) => "¥" + Number(n).toLocaleString("ja-JP");

/** Compare table rows. Default: price + spec keys shared by every item + first point. */
function compareRows(post, items) {
  let rows = post.compare?.rows;
  if (!rows) {
    const shared = Object.keys(items[0].specs).filter((k) => items.every((it) => k in it.specs));
    rows = [{ label: "価格", field: "price" }, ...shared.slice(0, 4).map((k) => ({ label: k, spec: k })), { label: "推しポイント", field: "points.0" }];
  }
  return rows.map((r) => ({
    label: r.label,
    kind: r.field === "price" ? "price" : "text",
    cells: items.map((it) => {
      const v = r.spec ? it.specs[r.spec] : get(it, r.field);
      if (v == null || v === "") return "—";
      return r.field === "price" ? yen(v) : String(v);
    }),
  }));
}

export async function buildPost(postFile, { only, fonts } = {}) {
  const post = JSON.parse(fs.readFileSync(postFile, "utf8"));
  const products = loadProducts();
  const items = post.products.map((id) => products[id] ?? (() => { throw new Error(`unknown product ${id}`); })());
  const hero = products[post.cover.hero] ?? items[0];
  const outDir = path.join(ROOT, "out", post.id);
  const htmlDir = path.join(ROOT, ".cache/html", post.id);
  fs.mkdirSync(outDir, { recursive: true });
  fs.mkdirSync(htmlDir, { recursive: true });

  const all = slidesFor(post, items);
  const slides = all.map((s, i) => ({ ...s, index: i })).filter((s) => !only || only.includes(s.key) || only.includes(s.group));
  const priceNote = T.brand.priceNote.replace("{date}", post.priceDate ?? "投稿");
  const dots = T.palette.aurora[post.cover.aurora]?.dots ?? T.palette.accentDots;
  const results = [];
  await withBrowser(async (browser) => {
    for (const s of slides) {
      const c = T.canvas[s.canvas];
      const ctx = {
        root: pathToFileURL(ROOT).href, T, brand: T.brand, post, cover: post.cover, compare: post.compare ?? {}, summary: post.summary ?? {},
        hero, items, dots, priceNote, compareRows: items.length >= 2 ? compareRows(post, items) : [],
        pageNo: s.index === 0 ? null : `${String(s.index + 1).padStart(2, "0")} / ${String(all.length).padStart(2, "0")}`,
        canvas: { name: s.canvas, ...c }, ...s.ctx,
      };
      const html = env.render(s.tpl, ctx);
      const name = `${String(s.index + 1).padStart(2, "0")}-${s.key}`;
      const htmlFile = path.join(htmlDir, `${name}.html`);
      fs.writeFileSync(htmlFile, html);
      const png = path.join(outDir, `${name}.png`);
      const report = await shoot(browser, htmlFile, png, { width: c.width, height: c.height, fontsReport: fonts });
      results.push(path.relative(ROOT, png));
      console.log("wrote", path.relative(ROOT, png), report ? JSON.stringify(report) : "");
    }
  });
  // caption
  const hashtags = [...new Set([...(post.hashtags ?? []), ...T.brand.hashtags])];
  const caption = capEnv.render("caption.njk", { brand: T.brand, post, cover: post.cover, items, priceNote, hashtags }).replace(/\n{3,}/g, "\n\n").trim() + "\n";
  fs.writeFileSync(path.join(outDir, "caption.txt"), caption);
  results.push(path.relative(ROOT, path.join(outDir, "caption.txt")));
  return results;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  const files = args.filter((a) => a.endsWith(".json"));
  const oi = args.indexOf("--only");
  const only = oi >= 0 ? args[oi + 1].split(",") : null;
  for (const f of files.length ? files : fs.readdirSync(path.join(ROOT, "data/posts")).map((f) => path.join(ROOT, "data/posts", f)))
    await buildPost(f, { only, fonts: args.includes("--fonts") });
}
